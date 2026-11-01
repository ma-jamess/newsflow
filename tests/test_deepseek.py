import io
import json
import socket
import sqlite3
import threading
import urllib.error
import urllib.request

import pytest


def completion(category='科技', reason='标题讨论芯片研发，主题属于科技。', needs_review=False):
    content = json.dumps({'category': category, 'reason': reason,
                          'needs_review': needs_review}, ensure_ascii=False)
    return io.BytesIO(json.dumps({'choices': [{'finish_reason': 'stop',
                                             'message': {'content': content}}]}).encode())


def service(opener=None, key='test-secret'):
    from newsroom.deepseek import DeepSeekService
    return DeepSeekService(api_key=key, opener=opener or (lambda *a, **k: completion()))


def test_request_uses_exact_official_model_and_returns_reason_without_probability():
    requests = []

    def open_request(request, **kwargs):
        requests.append(request)
        assert kwargs['timeout'] <= 90
        return completion()

    result = service(open_request).predict('国产人工智能芯片发布')
    request = requests[0]
    body = json.loads(request.data)
    assert request.full_url == 'https://api.deepseek.com/chat/completions'
    assert request.headers['Authorization'] == 'Bearer test-secret'
    assert body['model'] == 'deepseek-flash'
    assert body['response_format'] == {'type': 'json_object'}
    assert body['thinking']['type'] == 'enabled'
    assert json.loads(body['messages'][1]['content'])['title'] == '国产人工智能芯片发布'
    assert result['prediction'] == '科技' and result['model'] == 'deepseek'
    assert result['provider_model'] == 'deepseek-flash'
    assert result['score'] is None and result['probabilities'] == {}
    assert '芯片' in result['reason'] and result['status'] == 'ok'


@pytest.mark.parametrize('category', ['其他', '信息不足'])
def test_outside_or_ambiguous_titles_are_not_forced_into_five_categories(category):
    result = service(lambda *a, **k: completion(category, '标题不提供五类内的明确线索。', True)).predict('今天发生了一件事')
    assert result['prediction'] == '' and result['status'] == 'unknown'
    assert result['category'] == category and result['score'] is None


@pytest.mark.parametrize('title', ['', '!', '字' * 201, None])
def test_invalid_title_never_calls_paid_api(title):
    def forbidden(*args, **kwargs):
        pytest.fail('invalid title called paid API')
    with pytest.raises(ValueError):
        service(forbidden).predict(title)


@pytest.mark.parametrize('response', [
    b'not json',
    json.dumps({'choices': []}).encode(),
    json.dumps({'choices': [{'finish_reason': 'length', 'message': {'content': '{}'}}]}).encode(),
    json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'content': '{"category":"军事","reason":"军事","needs_review":false}'}}]}).encode(),
    json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'content': '{"category":"科技","reason":"","needs_review":"false"}'}}]}).encode(),
])
def test_invalid_provider_output_is_an_error_not_a_success(response):
    from newsroom.deepseek import DeepSeekError
    with pytest.raises(DeepSeekError):
        service(lambda *a, **k: io.BytesIO(response)).predict('国产芯片发布')


@pytest.mark.parametrize('status, text', [(401, '密钥'), (402, '余额'), (429, '频繁'), (503, '不可用')])
def test_provider_errors_are_actionable_and_do_not_echo_secrets(status, text):
    from newsroom.deepseek import DeepSeekError
    def unavailable(*a, **k):
        raise urllib.error.HTTPError('https://api.deepseek.com/chat/completions', status, 'test-secret', {}, io.BytesIO(b'test-secret'))
    with pytest.raises(DeepSeekError) as error:
        service(unavailable).predict('芯片发布')
    assert text in str(error.value) and 'test-secret' not in str(error.value)


def test_timeout_is_reported_without_automatic_paid_retry():
    from newsroom.deepseek import DeepSeekError
    calls = []
    def slow(*a, **k):
        calls.append(1)
        raise socket.timeout('test-secret')
    with pytest.raises(DeepSeekError, match='超时'):
        service(slow).predict('芯片发布')
    assert len(calls) == 1


def test_local_configuration_environment_override_and_public_metadata(tmp_path, monkeypatch):
    from newsroom.deepseek import DeepSeekService
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    path = tmp_path / 'deepseek.env'
    path.write_text('DEEPSEEK_API_KEY=file-secret\n', encoding='utf-8')
    instance = DeepSeekService(config_path=path)
    assert instance.metadata()['configured'] is True
    assert 'file-secret' not in json.dumps(instance.metadata())
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'env-secret')
    calls = []
    instance = DeepSeekService(config_path=path, opener=lambda request, **k: (calls.append(request), completion())[1])
    instance.predict('芯片发布')
    assert calls[0].headers['Authorization'] == 'Bearer env-secret'
    with pytest.raises(Exception, match='密钥'):
        service(key='').predict('芯片发布')


def test_existing_history_migrates_and_keeps_deepseek_explanations(tmp_path):
    from newsroom.store import Store
    path = tmp_path / 'old.db'
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE history (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, title TEXT NOT NULL, prediction TEXT NOT NULL, score REAL, status TEXT NOT NULL, model TEXT NOT NULL, correction TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '')")
        db.execute("INSERT INTO history(created_at,title,prediction,score,status,model) VALUES('2026-10-01','足球冠军','体育',0.9,'ok','svm')")
    store = Store(path)
    index = store.add(service().predict('芯片发布'))
    store.feedback(index, '科技', '已核对')
    rows = Store(path).history()
    assert len(rows) == 2 and rows[1]['prediction'] == '体育'
    assert rows[0]['provider_model'] == 'deepseek-flash' and '芯片' in rows[0]['reason']
    assert rows[0]['category'] == '科技' and rows[1]['category'] == ''
    assert rows[0]['correction'] == '科技'


def test_server_routes_deepseek_and_exports_reason_without_adding_to_local_report(tmp_path):
    from newsroom.server import create_server
    from newsroom.store import Store
    class LocalModel:
        report = {'recommended_model': 'svm', 'models': {'svm': {'test': {}}}}
        def predict(self, *args, **kwargs):
            raise ValueError('不支持的模型')
    server = create_server(0, LocalModel(), Store(tmp_path / 'db'), deepseek=service())
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        with urllib.request.urlopen(url + '/api/bootstrap') as response:
            bootstrap = json.load(response)
        assert bootstrap['deepseek']['configured'] is True
        assert 'deepseek' in bootstrap['model_names'] and 'deepseek' not in bootstrap['report']['models']
        assert 'test-secret' not in json.dumps(bootstrap)
        def post(path, payload, origin=url):
            request = urllib.request.Request(url + '/api/' + path, json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json', 'Origin': origin, 'X-Request-Token': bootstrap['token']})
            return urllib.request.urlopen(request)
        with post('predict', {'title': '芯片发布', 'model': 'deepseek'}) as response:
            result = json.load(response)['result']
        assert result['id'] > 0 and result['prediction'] == '科技'
        with post('export', {'history': True}) as response:
            exported = response.read().decode('utf-8-sig')
        assert 'deepseek-flash' in exported and '芯片研发' in exported
        assert 'category' in exported
        with pytest.raises(urllib.error.HTTPError) as caught:
            post('predict', {'title': '芯片发布', 'model': 'deepseek'}, 'https://evil.example')
        assert caught.value.code == 403
        with pytest.raises(urllib.error.HTTPError) as caught:
            post('batch', {'titles': ['芯片发布'], 'model': 'deepseek'})
        assert caught.value.code == 400
    finally:
        server.shutdown()
        server.server_close()


def test_packaging_excludes_api_secrets_even_if_placed_at_root(tmp_path, monkeypatch):
    from scripts import package
    monkeypatch.setattr(package, 'ROOT', tmp_path)
    assert not package.included(tmp_path / '.env')
    assert not package.included(tmp_path / '.env.local')
    assert not package.included(tmp_path / 'runtime' / 'deepseek.env')
    assert package.included(tmp_path / 'newsroom' / 'deepseek.py')


@pytest.mark.parametrize('category', ['其他', '信息不足'])
def test_abstention_category_survives_history_reload(tmp_path, category):
    from newsroom.store import Store
    path = tmp_path / 'db'
    result = service(lambda *a, **k: completion(category, '不属于五类或信息不足。', True)).predict('某件事发生了')
    Store(path).add(result)
    row = Store(path).history()[0]
    assert row['category'] == category and row['prediction'] == ''
