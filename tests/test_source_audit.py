from datetime import datetime, timezone

import pytest

NOW = datetime(2026, 11, 2, 8, tzinfo=timezone.utc)
RSS = b'''<rss><channel><item><title>Chinese headline</title><link>https://example.org/article</link><pubDate>Mon, 02 Nov 2026 07:00:00 GMT</pubDate></item></channel></rss>'''


def feed(title, date='Mon, 02 Nov 2026 07:00:00 GMT'):
    return RSS.replace(b'Chinese headline', title.encode()).replace(b'Mon, 02 Nov 2026 07:00:00 GMT', date.encode())


def test_audit_selects_recent_chinese_feeds_and_isolates_old_english_and_network_failures():
    from scripts.check_news_sources import audit_sources
    payloads = {'fresh': feed('足球队夺得冠军'), 'old': feed('旧闻', 'Mon, 02 Nov 2020 07:00:00 GMT'),
                'english': feed('English headline'), 'future': feed('未来标题', 'Mon, 02 Nov 2030 07:00:00 GMT')}
    sources = [{'id': key, 'name': key, 'url': 'https://example.org/' + key} for key in [*payloads, 'error']]
    def fetch(url):
        key = url.rsplit('/', 1)[1]
        if key == 'error':
            raise OSError('upstream-secret-response')
        return payloads[key]
    data = audit_sources(sources, fetcher=fetch, now=NOW)
    results = {item['id']: item for item in data['sources']}
    assert data['available_count'] == 1
    assert results['fresh']['available'] and results['fresh']['latest_published_at'] == '2026-11-02T07:00:00+00:00'
    assert results['old']['status'] == 'old' and not results['future']['available']
    assert results['english']['status'] == 'non_chinese' and results['error']['status'] == 'error'
    assert 'upstream-secret-response' not in str(data)


def test_audit_marks_undated_feed_without_inventing_publication_time():
    from scripts.check_news_sources import audit_sources
    data = audit_sources([{'id': 'undated', 'name': 'undated', 'url': 'https://example.org/feed'}],
                         fetcher=lambda url: feed('高校公布招生计划', ''), now=NOW)
    row = data['sources'][0]
    assert row['available'] and row['status'] == 'unknown_time'
    assert row['latest_published_at'] is None


def test_audit_rejects_private_and_keyed_inputs_before_fetch_and_does_not_echo_credentials():
    from scripts.check_news_sources import audit_sources
    sources = [{'id': str(i), 'name': 'unsafe', 'url': url} for i, url in enumerate([
        'https://alice:secret@example.org/feed', 'https://127.0.0.1/feed',
        'https://example.org/feed?api_key=private-value'])]
    def fail_if_called(url):
        raise AssertionError('unsafe input was fetched')
    data = audit_sources(sources, fetcher=fail_if_called, now=NOW)
    assert data['available_count'] == 0
    assert all(row['status'] == 'invalid' and row['url'] == '' for row in data['sources'])
    assert 'secret' not in str(data) and 'private-value' not in str(data)


def test_audit_rejects_undated_archive_with_old_dates_in_article_urls():
    from scripts.check_news_sources import audit_sources
    archive = feed('湘财祈年：白糖收盘评论20080612', '').replace(
        b'https://example.org/article', b'http://finance.sina.com.cn/money/future/20080612/16344975099.shtml')
    row = audit_sources([{'id':'sina','name':'新浪财经','url':'https://rss.sina.com.cn/finance/rollnews.xml'}],
                        fetcher=lambda url: archive, now=NOW)['sources'][0]
    assert row['status'] == 'old' and not row['available']
    assert row['latest_published_at'] is None


@pytest.mark.parametrize('date,status,available,recent', [
    ('Mon, 02 Nov 2020 07:00:00 GMT', 'old', False, 0),
    ('Mon, 02 Nov 2026 07:00:00 GMT', 'current', True, 1),
])
def test_audit_only_uses_recent_dated_items_to_mark_mixed_feed_current(date, status, available, recent):
    from scripts.check_news_sources import audit_sources
    payload = ('<rss><channel><item><title>标注日期的中文新闻</title><link>https://example.org/dated</link>'
               '<pubDate>'+date+'</pubDate></item><item><title>未标日期的中文新闻</title>'
               '<link>https://example.org/undated</link></item></channel></rss>').encode()
    row = audit_sources([{'id':'mixed','name':'混合日期','url':'https://example.org/feed'}],
                        fetcher=lambda url: payload, now=NOW)['sources'][0]
    assert row['status'] == status and row['available'] is available
    assert row['recent_items'] == recent and row['undated_items'] == 1
