"""Exercise new news routes through the actual local HTTP server."""
import json
import threading
from contextlib import contextmanager
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from newsroom.ml import ModelService
from newsroom.store import Store
from tests.test_live_news import NOW, ROOT, RSS, article


class DisabledProvider:
    def metadata(self):
        return {'configured': False}

    def predict(self, title):
        raise AssertionError('Automatic news must never call a paid model')


@contextmanager
def running(tmp_path):
    from newsroom.live_news import LiveNewsService
    from newsroom.news_store import NewsStore
    from newsroom.server import create_server
    model = ModelService(ROOT / 'artifacts')
    cache = NewsStore(tmp_path / 'news.sqlite3')
    for source in cache.sources(NOW):
        cache.set_enabled(source['id'], source['id'] == 'ithome')
    titles = ['高校公布招生计划', '足球队夺得联赛冠军']
    rows = [article('https://example.org/education', titles[0]), article('https://example.org/sports', titles[1])]
    cache.ingest('ithome', rows, model.predict(titles), NOW)
    live = LiveNewsService(cache, model, fetcher=lambda url: RSS, clock=lambda: NOW)
    server = create_server(0, model, Store(tmp_path / 'history.sqlite3'), live=live, deepseek=DisabledProvider())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    def request(path, data=None, token=None, extra_headers=None):
        headers = {}
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers = {'Content-Type': 'application/json', 'Origin': base, 'X-Request-Token': token or ''}
        headers.update(extra_headers or {})
        with urlopen(Request(base + path, data=body, headers=headers), timeout=10) as response:
            raw = response.read()
            return json.loads(raw) if 'application/json' in response.headers['Content-Type'] else raw
    try:
        token = request('/api/bootstrap')['token']
        yield request, token, cache, live
    finally:
        server.shutdown()
        server.server_close()
        live.stop()
        thread.join(timeout=2)


def test_news_api_filters_and_detail_return_real_local_model_results(tmp_path):
    with running(tmp_path) as (request, token, cache, live):
        data = request('/api/news?' + urlencode({'category': '体育', 'q': '冠军', 'source': 'ithome'}))
        assert data['total'] == 1
        assert data['rows'][0]['title'] == '足球队夺得联赛冠军'
        assert data['interval_seconds'] == 120
        detail = request('/api/news/detail?id=' + data['rows'][0]['id'])
        assert detail['explanation']['prediction'] == '体育'
        assert detail['explanation']['evidence']


def test_news_mutations_require_the_existing_request_token(tmp_path):
    with running(tmp_path) as (request, token, cache, live):
        item = request('/api/news')['rows'][0]
        with pytest.raises(HTTPError) as caught:
            request('/api/news/save', {'id': item['id'], 'saved': True}, 'wrong-token')
        assert caught.value.code == 403
        assert cache.query(saved=True, now=NOW)['total'] == 0


@pytest.mark.parametrize('extra_headers, use_valid_token, status', [
    ({}, False, 403),
    ({'Origin': 'https://other.example'}, True, 403),
    ({'Content-Type': 'text/plain'}, True, 415),
])
def test_bounded_rejected_post_returns_json_error_without_connection_reset(
        tmp_path, extra_headers, use_valid_token, status):
    with running(tmp_path) as (request, token, cache, live):
        item = request('/api/news')['rows'][0]
        payload = {'id': item['id'], 'saved': True, 'padding': 'x' * (1024 * 1024)}
        for _ in range(25):
            with pytest.raises(HTTPError) as caught:
                request('/api/news/save', payload,
                        token if use_valid_token else 'wrong-token', extra_headers)
            with caught.value as response:
                assert response.code == status
                assert isinstance(json.load(response)['error'], str)
        assert cache.query(saved=True, now=NOW)['total'] == 0


def test_saved_news_and_human_category_are_reflected_in_filtered_results(tmp_path):
    with running(tmp_path) as (request, token, cache, live):
        item = request('/api/news')['rows'][0]
        request('/api/news/save', {'id': item['id'], 'saved': True}, token)
        request('/api/news/feedback', {'id': item['id'], 'category': '财经'}, token)
        rows = request('/api/news?category=' + '%E8%B4%A2%E7%BB%8F' + '&saved=1')['rows']
        assert len(rows) == 1
        assert rows[0]['id'] == item['id']
        assert rows[0]['human_labeled'] is True


def test_news_export_contains_source_publication_and_human_category(tmp_path):
    with running(tmp_path) as (request, token, cache, live):
        item = request('/api/news')['rows'][0]
        request('/api/news/save', {'id': item['id'], 'saved': True}, token)
        request('/api/news/feedback', {'id': item['id'], 'category': '科技'}, token)
        text = request('/api/news/export', {'saved': True}, token).decode('utf-8-sig')
        assert 'source_name' in text
        assert 'published_at' in text
        assert '科技' in text
        assert item['url'] in text
        assert len(text.splitlines()) == 2


def test_private_custom_feed_is_rejected_without_creating_a_source(tmp_path):
    with running(tmp_path) as (request, token, cache, live):
        original = len(request('/api/news/sources')['sources'])
        with pytest.raises(HTTPError) as caught:
            request('/api/news/sources', {'name': 'Private', 'url': 'https://127.0.0.1/feed'}, token)
        assert caught.value.code == 400
        assert len(request('/api/news/sources')['sources']) == original


def test_refresh_is_async_and_reuses_an_active_job(tmp_path):
    with running(tmp_path) as (request, token, cache, live):
        entered, release = threading.Event(), threading.Event()
        def fetch(url):
            entered.set()
            release.wait(3)
            return RSS
        live.fetcher = fetch
        try:
            assert request('/api/news/refresh', {}, token)['started'] is True
            assert entered.wait(2)
            assert request('/api/news/refresh', {}, token)['started'] is False
            assert request('/api/news')['update']['refreshing'] is True
        finally:
            release.set()


def test_invalid_news_query_is_a_client_error_and_keeps_service_usable(tmp_path):
    with running(tmp_path) as (request, token, cache, live):
        with pytest.raises(HTTPError) as caught:
            request('/api/news?category=invalid&limit=-1')
        assert caught.value.code == 400
        assert request('/api/news')['total'] == 2
