"""News updates exercise the parser, real SQLite state and local model boundary."""
import socket
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

NOW = datetime(2026, 10, 31, 8, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]
RSS = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Fixture</title><pubDate>Sat, 31 Oct 2026 16:00:00 +0800</pubDate>
<item><title><![CDATA[ 人工智能芯片正式发布 ]]></title><link>https://example.org/ai?id=42&amp;utm_source=rss</link>
<description><![CDATA[<p>新芯片发布。<script>not-visible()</script></p><img src="x" onerror="bad()">]]></description>
<pubDate>Sat, 31 Oct 2026 15:30:00 +0800</pubDate></item>
<item><title>足球队夺得联赛冠军</title><link>https://example.org/sports</link>
<description>比赛结束。</description><pubDate>Sat, 31 Oct 2026 15:00:00 +0800</pubDate></item>
<item><title>不安全链接</title><link>javascript:alert(1)</link></item>
</channel></rss>'''.encode('utf-8')


def components():
    from newsroom import feeds
    from newsroom.live_news import LiveNewsService
    from newsroom.news_store import NewsStore
    return feeds, NewsStore, LiveNewsService


def article(url='https://example.org/one', title='高校公布招生计划', published=None):
    return {'title': title, 'url': url, 'summary': '学校公布招生计划。',
            'published_at': (published or NOW).isoformat()}


def prediction(category='教育', score=.9, status='ok'):
    return {'title': '高校公布招生计划', 'prediction': category, 'score': score,
            'status': status, 'model': 'svm', 'probabilities': {category: score},
            'message': '分类完成', 'elapsed_ms': 1}


def test_rss_dates_are_item_dates_and_unsafe_html_links_are_removed():
    feeds, _, _ = components()
    rows = feeds.parse_feed(RSS, 'https://example.org/feed', NOW)
    assert len(rows) == 2
    assert rows[0]['title'] == '人工智能芯片正式发布'
    assert rows[0]['url'] == 'https://example.org/ai?id=42'
    assert rows[0]['published_at'] == '2026-10-31T07:30:00+00:00'
    assert rows[0]['summary'] == '新芯片发布。'


def test_atom_alternate_links_and_iso_dates_are_supported():
    feeds, _, _ = components()
    data = '''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
    <title>高校发布招生计划</title><link rel="self" href="https://example.org/api/1"/>
    <link rel="alternate" href="/education"/><published>2026-10-31T07:00:00Z</published>
    <summary type="html">&lt;p&gt;招生说明&lt;/p&gt;</summary></entry></feed>'''.encode()
    row = feeds.parse_feed(data, 'https://example.org/feed', NOW)[0]
    assert row['url'] == 'https://example.org/education'
    assert row['published_at'] == '2026-10-31T07:00:00+00:00'
    assert row['summary'] == '招生说明'


def test_missing_publication_time_does_not_copy_channel_or_fetch_time():
    feeds, _, _ = components()
    data = b'<rss><channel><pubDate>Sat, 31 Oct 2026 16:00:00 +0800</pubDate><item><title>News</title><link>https://example.org/x</link></item></channel></rss>'
    assert feeds.parse_feed(data, 'https://example.org/feed', NOW)[0]['published_at'] is None


@pytest.mark.parametrize('body', [b'<!DOCTYPE rss [<!ENTITY x "secret">]><rss><channel/></rss>',
                                 b'<html><body>Not a feed</body></html>', b'<rss>broken'])
def test_invalid_and_entity_declaring_feeds_are_rejected(body):
    feeds, _, _ = components()
    with pytest.raises(ValueError):
        feeds.parse_feed(body, 'https://example.org/feed', NOW)


def test_public_feed_validation_rejects_private_dns_and_credentials(monkeypatch):
    feeds, _, _ = components()
    monkeypatch.setattr(feeds.socket, 'getaddrinfo', lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))])
    with pytest.raises(ValueError):
        feeds.validate_feed_url('https://example.org/feed')
    for url in ['http://example.org/feed', 'https://user:pass@example.org/feed',
                'https://example.org:8443/feed', 'https://localhost/feed', 'https://[::1]/feed']:
        with pytest.raises(ValueError):
            feeds.validate_feed_url(url)


def test_public_feed_validation_accepts_https_and_rejects_mixed_dns(monkeypatch):
    feeds, _, _ = components()
    public = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))
    monkeypatch.setattr(feeds.socket, 'getaddrinfo', lambda *a, **k: [public])
    assert feeds.validate_feed_url('https://example.org/feed#section') == 'https://example.org/feed'
    monkeypatch.setattr(feeds.socket, 'getaddrinfo', lambda *a, **k: [public, (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 443))])
    with pytest.raises(ValueError):
        feeds.validate_feed_url('https://example.org/feed')


def test_feed_socket_connects_to_the_validated_numeric_ip_without_second_dns(monkeypatch):
    feeds, _, _ = components()
    resolutions, connected = [], []
    def resolve(host, port, **kwargs):
        resolutions.append(host)
        address = '93.184.216.34' if len(resolutions) == 1 else '127.0.0.1'
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (address, 443))]
    class Socket:
        def settimeout(self, timeout):
            pass
        def connect(self, address):
            connected.append(address)
        def close(self):
            pass
    monkeypatch.setattr(feeds.socket, 'getaddrinfo', resolve)
    monkeypatch.setattr(feeds.socket, 'socket', lambda *args: Socket())
    feeds._public_connection(('example.org', 443), timeout=10)
    assert resolutions == ['example.org']
    assert connected == [('93.184.216.34', 443)]
    assert feeds._PublicHTTPSConnection('example.org')._create_connection is feeds._public_connection


def test_feed_socket_rejects_a_host_that_rebinds_after_url_validation(monkeypatch):
    feeds, _, _ = components()
    addresses = iter(['93.184.216.34', '10.0.0.1'])
    monkeypatch.setattr(feeds.socket, 'getaddrinfo', lambda *args, **kwargs:
                        [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (next(addresses), 443))])
    assert feeds.validate_feed_url('https://example.org/feed')
    with pytest.raises(ValueError):
        feeds._public_connection(('example.org', 443), timeout=10)


def test_news_stats_include_all_current_rows_past_the_export_limit(tmp_path):
    _, Store, _ = components()
    store = Store(tmp_path / 'news.sqlite3')
    rows = [article(f'https://example.org/{index}') for index in range(5001)]
    store.ingest('ithome', rows, [prediction()] * len(rows), NOW)
    assert store.query(now=NOW)['total'] == 5001
    assert store.stats(NOW)['total'] == 5001
    assert store.stats(NOW)['categories']['教育'] == 5001


def test_stop_waits_for_a_manual_job_whose_thread_is_still_being_created(tmp_path, monkeypatch):
    _, Store, Live = components()
    from newsroom import live_news
    from newsroom.ml import ModelService
    store = Store(tmp_path / 'news.sqlite3')
    for source in store.sources(NOW):
        store.set_enabled(source['id'], False)
    live = Live(store, ModelService(ROOT / 'artifacts'), clock=lambda: NOW)
    original_thread = threading.Thread
    entered, release, stopped = threading.Event(), threading.Event(), threading.Event()
    def thread_factory(*args, **kwargs):
        if kwargs.get('name') == 'newsflow-update':
            entered.set()
            release.wait(3)
        return original_thread(*args, **kwargs)
    monkeypatch.setattr(live_news.threading, 'Thread', thread_factory)
    requester = original_thread(target=live.request_refresh)
    stopper = original_thread(target=lambda: (live.stop(), stopped.set()))
    requester.start()
    try:
        assert entered.wait(2)
        stopper.start()
        assert not stopped.wait(.05), 'stop returned before the active job was registered'
    finally:
        release.set()
        requester.join(3)
        if stopper.ident is not None:
            stopper.join(3)
        live.stop()
    assert not requester.is_alive() and not stopper.is_alive()


def test_refresh_deduplicates_urls_and_preserves_human_category_and_bookmark(tmp_path):
    _, Store, _ = components()
    store = Store(tmp_path / 'news.sqlite3')
    store.ingest('ithome', [article()], [prediction()], NOW)
    row = store.query(now=NOW)['rows'][0]
    store.bookmark(row['id'], True)
    store.feedback(row['id'], '财经')
    store.ingest('ithome', [article(title='高校更新招生计划')], [prediction('教育', .99)], NOW + timedelta(minutes=2))
    rows = store.query(saved=True, now=NOW + timedelta(minutes=2))['rows']
    assert len(rows) == 1
    assert rows[0]['title'] == '高校更新招生计划'
    assert rows[0]['category'] == '财经'
    assert rows[0]['saved'] is True
    assert rows[0]['needs_review'] is False


def test_category_source_text_and_saved_filters_are_an_intersection(tmp_path):
    _, Store, _ = components()
    store = Store(tmp_path / 'news.sqlite3')
    store.ingest('ithome', [article('https://example.org/a', '高校公布招生计划'),
                            article('https://example.org/b', '大学公布课程')], [prediction(), prediction()], NOW)
    store.ingest('sspai', [article('https://example.org/c', '高校公布招生计划')], [prediction()], NOW)
    for row in store.query(now=NOW)['rows']:
        if row['url'] != 'https://example.org/b':
            store.bookmark(row['id'], True)
    data = store.query(q='招生', category='教育', source='ithome', saved=True, now=NOW)
    assert data['total'] == 1
    assert data['rows'][0]['url'] == 'https://example.org/a'


def test_pending_news_keeps_the_model_prediction_until_human_correction(tmp_path):
    _, Store, _ = components()
    store = Store(tmp_path / 'news.sqlite3')
    store.ingest('ithome', [article()], [prediction('教育', .51, 'review')], NOW)
    row = store.query(review=True, now=NOW)['rows'][0]
    assert row['category'] == '教育'
    assert row['needs_review'] is True
    store.feedback(row['id'], '科技')
    assert store.query(review=True, now=NOW)['total'] == 0
    assert store.query(now=NOW)['rows'][0]['category'] == '科技'


def test_old_publication_is_not_new_and_retention_keeps_old_bookmarks(tmp_path):
    _, Store, _ = components()
    store = Store(tmp_path / 'news.sqlite3')
    old = NOW - timedelta(days=8)
    store.ingest('ithome', [article('https://example.org/a', published=old), article('https://example.org/b', published=old)],
                 [prediction(), prediction()], old)
    saved_id = store.query(now=old)['rows'][0]['id']
    store.bookmark(saved_id, True)
    assert store.query(now=NOW)['total'] == 0
    store.prune(NOW)
    assert store.query(saved=True, now=NOW)['total'] == 1
    assert store.query(saved=True, now=NOW)['rows'][0]['id'] == saved_id


def test_source_health_separates_successful_fetch_from_old_news(tmp_path):
    _, Store, _ = components()
    store = Store(tmp_path / 'news.sqlite3')
    store.finish_source('ithome', NOW, latest='2025-06-05T00:00:00+00:00', count=1)
    source = next(s for s in store.sources(NOW) if s['id'] == 'ithome')
    assert source['last_success_at'] == NOW.isoformat()
    assert source['fresh'] is False
    assert source['status'] == 'stale'


def test_live_refresh_uses_real_local_classifier_and_caches_source_failures(tmp_path):
    _, Store, Live = components()
    from newsroom.ml import ModelService
    store = Store(tmp_path / 'news.sqlite3')
    for source in store.sources(NOW):
        store.set_enabled(source['id'], source['id'] in {'ithome', 'sspai'})
    def fetch(url):
        if 'sspai.com' in url:
            raise OSError('provider unavailable')
        return RSS
    live = Live(store, ModelService(ROOT / 'artifacts'), fetcher=fetch, clock=lambda: NOW)
    live.refresh()
    data = live.snapshot()
    assert data['total'] == 2
    assert next(r for r in data['rows'] if '冠军' in r['title'])['category'] == '体育'
    assert next(r for r in data['rows'] if '芯片' in r['title'])['category'] == '科技'
    source = next(s for s in store.sources(NOW) if s['id'] == 'sspai')
    assert source['status'] == 'error'
    row = data['rows'][0]
    store.bookmark(row['id'], True)
    live.fetcher = lambda url: (_ for _ in ()).throw(OSError('offline'))
    live.refresh()
    assert live.snapshot(saved=True)['rows'][0]['id'] == row['id']
    assert live.snapshot()['update']['status'] == 'error'


def test_repeated_refresh_requests_share_one_job_and_obey_cooldown(tmp_path):
    _, Store, Live = components()
    from newsroom.ml import ModelService
    entered, release = threading.Event(), threading.Event()
    store = Store(tmp_path / 'news.sqlite3')
    for source in store.sources(NOW):
        store.set_enabled(source['id'], source['id'] == 'ithome')
    def fetch(url):
        entered.set()
        release.wait(3)
        return RSS
    clock = [NOW]
    live = Live(store, ModelService(ROOT / 'artifacts'), fetcher=fetch, clock=lambda: clock[0])
    try:
        assert live.request_refresh()['started'] is True
        assert entered.wait(2)
        assert live.request_refresh()['started'] is False
        release.set()
        live.stop()
        assert live.snapshot()['update']['refreshing'] is False
        assert live.request_refresh()['started'] is False
    finally:
        release.set()
        live.stop()


def test_finished_manual_refresh_cannot_restart_within_thirty_seconds(tmp_path):
    _, Store, Live = components()
    from newsroom.ml import ModelService
    store = Store(tmp_path / 'news.sqlite3')
    for source in store.sources(NOW):
        store.set_enabled(source['id'], False)
    live = Live(store, ModelService(ROOT / 'artifacts'), fetcher=lambda url: RSS, clock=lambda: NOW)
    live.refresh()
    result = live.request_refresh()
    assert result['started'] is False
    assert result['cooldown_seconds'] == 30


def test_unknown_news_or_invalid_manual_categories_do_not_create_records(tmp_path):
    _, Store, _ = components()
    store = Store(tmp_path / 'news.sqlite3')
    with pytest.raises(ValueError):
        store.bookmark('not-an-id', True)
    store.ingest('ithome', [article()], [prediction()], NOW)
    row = store.query(now=NOW)['rows'][0]
    with pytest.raises(ValueError):
        store.feedback(row['id'], '<script>bad()</script>')
    assert store.query(now=NOW)['rows'][0]['category'] == '教育'
