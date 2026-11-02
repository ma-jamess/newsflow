from datetime import datetime, timezone

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
