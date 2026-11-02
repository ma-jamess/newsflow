import copy
import json
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from newsroom.ml import ModelService
from newsroom.public_site import build_snapshot, write_site

NOW = datetime(2026, 11, 2, 10, tzinfo=timezone.utc)
RSS = b'''<rss><channel><item><title>\xe8\xb6\xb3\xe7\x90\x83\xe9\x98\x9f\xe5\xa4\xba\xe5\xbe\x97\xe8\x81\x94\xe8\xb5\x9b\xe5\x86\xa0\xe5\x86\x9b</title>
<link>https://example.org/sport</link><pubDate>Mon, 02 Nov 2026 09:00:00 GMT</pubDate>
<description>sports</description></item></channel></rss>'''


@pytest.fixture(scope='module')
def classifier():
    return ModelService(Path(__file__).resolve().parents[1] / 'artifacts')


@pytest.fixture(scope='module')
def snapshot(classifier):
    return build_snapshot(classifier, fetcher=lambda url: RSS, now=NOW)


def seeded_site(tmp_path, classifier, snapshot):
    from newsroom.ecs_site import bootstrap_site
    seed = tmp_path / 'seed.json'
    seed.write_text(json.dumps(snapshot), encoding='utf-8')
    site = tmp_path / 'site'
    bootstrap_site(site, classifier, seed_path=seed, repository='ma-jamess/newsflow')
    return site, seed


def test_ecs_page_advertises_its_real_update_interval(tmp_path, classifier, snapshot):
    site = write_site(tmp_path / 'site', snapshot, classifier.report, 'ma-jamess/newsflow',
                      deployment='ecs', interval_seconds=120)
    data = json.loads((site / 'data/news.json').read_text(encoding='utf-8'))
    html = (site / 'index.html').read_text(encoding='utf-8')
    assert data['deployment'] == 'ecs' and data['interval_seconds'] == 120
    assert '2 分钟' in html and '5 分钟' not in html
    assert '{{' not in html


def test_scheduled_refresh_preserves_assets_and_publishes_current_data(tmp_path, classifier, snapshot):
    from newsroom.ecs_site import refresh_site
    site, seed = seeded_site(tmp_path, classifier, snapshot)
    assets = {p.relative_to(site): p.read_bytes() for p in site.rglob('*')
              if p.is_file() and p.relative_to(site).as_posix() != 'data/news.json'}
    fresh = RSS.replace(b'/sport', b'/new-sport')
    result = refresh_site(site, classifier, seed_path=seed, repository='ma-jamess/newsflow',
                          fetcher=lambda url: fresh, now=NOW + timedelta(minutes=2))
    published = json.loads((site / 'data/news.json').read_text(encoding='utf-8'))
    assert published['generated_at'] == '2026-11-02T10:02:00+00:00'
    assert published['interval_seconds'] == 120 and published['deployment'] == 'ecs'
    assert len(published['rows']) == 2 and result['update']['status'] == 'success'
    assert all((site / relative).read_bytes() == content for relative, content in assets.items())


def test_classifier_failure_leaves_previous_page_and_json_intact(tmp_path, classifier, snapshot, monkeypatch):
    from newsroom.ecs_site import refresh_site
    site, seed = seeded_site(tmp_path, classifier, snapshot)
    before = {p.relative_to(site): p.read_bytes() for p in site.rglob('*') if p.is_file()}
    def fail(*args, **kwargs):
        raise RuntimeError('model unavailable')
    monkeypatch.setattr(classifier, 'predict', fail)
    with pytest.raises(RuntimeError, match='model unavailable'):
        refresh_site(site, classifier, seed_path=seed, repository='ma-jamess/newsflow',
                     fetcher=lambda url: RSS, now=NOW)
    assert all((site / relative).read_bytes() == content for relative, content in before.items())


def test_disk_replace_failure_preserves_complete_json(tmp_path, classifier, snapshot, monkeypatch):
    from newsroom import ecs_site
    site, seed = seeded_site(tmp_path, classifier, snapshot)
    before = (site / 'data/news.json').read_bytes()
    def fail(*args, **kwargs):
        raise OSError('simulated filesystem failure')
    monkeypatch.setattr(ecs_site.os, 'replace', fail)
    with pytest.raises(OSError, match='filesystem failure'):
        ecs_site.refresh_site(site, classifier, seed_path=seed, repository='ma-jamess/newsflow',
                              fetcher=lambda url: RSS, now=NOW)
    assert (site / 'data/news.json').read_bytes() == before
    assert not list(site.glob('**/*.tmp'))


@pytest.mark.parametrize('corrupt', [b'{broken', b' ' * (8 * 1024 * 1024 + 1)],
                         ids=['invalid-json', 'oversized-json'])
def test_bad_previous_json_falls_back_to_public_seed(tmp_path, classifier, snapshot, corrupt):
    from newsroom.ecs_site import refresh_site
    site, seed = seeded_site(tmp_path, classifier, snapshot)
    (site / 'data/news.json').write_bytes(corrupt)
    def offline(url):
        raise OSError('offline')
    result = refresh_site(site, classifier, seed_path=seed, repository='ma-jamess/newsflow',
                          fetcher=offline, now=NOW)
    assert len(result['rows']) == 1
    assert result['rows'][0]['url'] == 'https://example.org/sport'
    assert result['update']['status'] == 'error'
    assert json.loads((site / 'data/news.json').read_text(encoding='utf-8'))['schema_version'] == 1


def test_bootstrap_scrubs_personal_flags_without_changing_news_time(tmp_path, classifier, snapshot):
    from newsroom.ecs_site import bootstrap_site
    altered = copy.deepcopy(snapshot)
    altered['rows'][0].update(saved=True, correction='教育', human_labeled=True)
    seed = tmp_path / 'seed.json'
    seed.write_text(json.dumps(altered), encoding='utf-8')
    site = tmp_path / 'site'
    bootstrap_site(site, classifier, seed_path=seed, repository='ma-jamess/newsflow')
    public = json.loads((site / 'data/news.json').read_text(encoding='utf-8'))
    assert public['generated_at'] == '2026-11-02T10:00:00+00:00'
    assert all(r['saved'] is False and r['correction'] == '' and r['human_labeled'] is False for r in public['rows'])


@pytest.mark.skipif(os.name != 'posix', reason='Nginx file permissions are verified on the Linux ECS')
def test_refreshed_json_is_readable_by_the_separate_nginx_user(tmp_path, classifier, snapshot):
    from newsroom.ecs_site import refresh_site
    site, seed = seeded_site(tmp_path, classifier, snapshot)
    refresh_site(site, classifier, seed_path=seed, repository='ma-jamess/newsflow',
                 fetcher=lambda url: RSS, now=NOW)
    assert stat.S_IMODE((site / 'data/news.json').stat().st_mode) & stat.S_IROTH
