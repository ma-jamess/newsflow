from datetime import datetime, timezone
from pathlib import Path

import pytest

from newsroom.ml import ModelService

NOW = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
RSS = '''<rss><channel><item><title>足球队夺得联赛冠军</title>
<link>https://example.org/sport</link><pubDate>Sun, 01 Nov 2026 07:00:00 GMT</pubDate>
<description>体育订阅摘要</description></item></channel></rss>'''.encode()


@pytest.fixture(scope='module')
def classifier():
    return ModelService(Path(__file__).resolve().parents[1] / 'artifacts')


def test_public_snapshot_uses_real_local_model_and_no_personal_state(classifier):
    from newsroom.public_site import build_snapshot
    data = build_snapshot(classifier, fetcher=lambda url: RSS, now=NOW)
    assert data['schema_version'] == 1 and data['interval_seconds'] == 300
    assert len(data['rows']) == 1
    row = data['rows'][0]
    assert row['category'] == '体育' and row['result']['probabilities']['体育'] > .5
    assert row['explanation']['evidence']
    assert not row['saved'] and not row['correction']
    assert len(data['sources']) == 5


def test_failed_public_refresh_preserves_previous_news_and_success_time(classifier):
    from newsroom.public_site import build_snapshot
    old = build_snapshot(classifier, fetcher=lambda url: RSS, now=NOW)
    def fail(url):
        raise OSError('network unavailable')
    data = build_snapshot(classifier, fetcher=fail, previous=old, now=NOW)
    assert data['rows'][0]['id'] == old['rows'][0]['id']
    assert data['update']['status'] == 'error'
    assert data['update']['last_success_at'] == old['update']['last_success_at']


def test_empty_total_failure_does_not_replace_a_working_deployment(classifier):
    from newsroom.public_site import build_snapshot
    def fail(url):
        raise OSError('unavailable')
    with pytest.raises(ValueError, match='没有可发布'):
        build_snapshot(classifier, fetcher=fail, now=NOW)


@pytest.mark.parametrize('field,value', [('rows', None), ('sources', {}), ('update', None)])
def test_corrupt_previous_structure_does_not_prevent_fresh_news(classifier, field, value):
    from newsroom.public_site import build_snapshot
    previous = {'schema_version': 1, field: value}
    data = build_snapshot(classifier, fetcher=lambda url: RSS, previous=previous, now=NOW)
    assert data['rows'][0]['category'] == '体育'


def test_corrupt_prior_source_count_does_not_prevent_refresh(classifier):
    from newsroom.public_site import build_snapshot
    previous = build_snapshot(classifier, fetcher=lambda url: RSS, now=NOW)
    previous['sources'][0]['item_count'] = 'invalid'
    data = build_snapshot(classifier, fetcher=lambda url: RSS, previous=previous, now=NOW)
    assert len(data['rows']) == 1


def test_partial_source_failure_retains_failed_source_articles(classifier):
    from newsroom.public_site import build_snapshot
    previous = build_snapshot(classifier, fetcher=lambda url: RSS, now=NOW)
    failed_source = previous['rows'][0]['source_id']
    failed_url = next(source['url'] for source in previous['sources'] if source['id'] == failed_source)
    fresh = RSS.replace('足球队夺得联赛冠军'.encode(), '人工智能芯片发布'.encode()).replace(b'/sport', b'/chip')
    def fetch(url):
        if url == failed_url:
            raise OSError('temporarily unavailable')
        return fresh
    data = build_snapshot(classifier, fetcher=fetch, previous=previous, now=NOW)
    assert data['update']['status'] == 'partial'
    assert {row['title'] for row in data['rows']} == {'足球队夺得联赛冠军', '人工智能芯片发布'}
    assert previous['rows'][0]['id'] in {row['id'] for row in data['rows']}


def test_long_feed_title_is_retained_when_the_next_fetch_fails(classifier):
    from newsroom.public_site import build_snapshot
    title = '人工智能芯片' * 40
    rss = RSS.replace('足球队夺得联赛冠军'.encode(), title.encode())
    previous = build_snapshot(classifier, fetcher=lambda url: rss, now=NOW)
    def fail(url):
        raise OSError('offline')
    data = build_snapshot(classifier, fetcher=fail, previous=previous, now=NOW)
    assert data['rows'][0]['title'] == title


def test_public_snapshot_fetch_has_separate_bounded_budget(monkeypatch):
    import io
    import json
    import socket
    from newsroom import feeds
    from scripts import build_public_site
    payload = {'schema_version': 1, 'rows': [{'summary': 'x' * 2600}] * 456}
    raw = json.dumps(payload).encode()
    assert len(raw) > feeds.MAX_FEED_BYTES
    class Response(io.BytesIO):
        def geturl(self):
            return 'https://example.org/data/news.json'
    class Opener:
        def open(self, *args, **kwargs):
            return Response(raw)
    monkeypatch.setattr(feeds.socket, 'getaddrinfo', lambda *a, **k:
                        [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))])
    monkeypatch.setattr(feeds, 'build_opener', lambda *args: Opener())
    with pytest.raises(ValueError, match='1 MiB'):
        feeds.fetch_feed('https://example.org/feed')
    assert len(build_public_site.load_previous_snapshot('https://example.org/data/news.json')['rows']) == 456


def test_prior_snapshot_cannot_import_personal_flags_or_unknown_sources(classifier):
    from newsroom.public_site import build_snapshot
    old = build_snapshot(classifier, fetcher=lambda url: RSS, now=NOW)
    old['rows'][0].update(saved=True, correction='财经', human_labeled=True)
    invalid = {**old['rows'][0], 'url': 'javascript:alert(1)', 'source_id': 'unknown'}
    old['rows'].append(invalid)
    empty = b'<rss><channel></channel></rss>'
    data = build_snapshot(classifier, fetcher=lambda url: empty, previous=old, now=NOW)
    assert len(data['rows']) == 1
    assert data['rows'][0]['category'] == '体育'
    assert not data['rows'][0]['saved'] and not data['rows'][0]['correction']


def test_static_artifact_is_relative_and_contains_only_public_files(classifier, tmp_path):
    from newsroom.public_site import build_snapshot, write_site
    data = build_snapshot(classifier, fetcher=lambda url: RSS, now=NOW)
    write_site(tmp_path, data, classifier.report, 'ma-jamess/newsflow')
    html = (tmp_path / 'index.html').read_text(encoding='utf-8')
    assert 'src="/api' not in html and 'src="/style' not in html
    assert 'public-backend.js' in html and 'page-news' in html
    assert (tmp_path / 'data/news.json').exists()
    names = {path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob('*') if path.is_file()}
    assert not any('runtime' in name or name.endswith(('.env', '.sqlite3', '.joblib')) for name in names)
    assert (tmp_path / 'LICENSE').exists()
