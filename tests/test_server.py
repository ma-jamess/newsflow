import json
import threading
import urllib.error
import urllib.request

import pytest


def test_history_and_feedback_persist_with_real_sqlite(tmp_path):
    from newsroom.store import Store
    db = tmp_path / 'history.db'
    store = Store(db)
    index = store.add({'title': "<script>alert('x')</script>", 'prediction': '体育', 'score': .7, 'status': 'ok', 'model': 'lr'})
    store.feedback(index, '财经', '老师核对')
    record = Store(db).history()[0]
    assert record['id'] == index and record['correction'] == '财经'
    assert record['note'] == '老师核对'
    with pytest.raises(ValueError):
        store.feedback(index, '无效类别', '')
    with pytest.raises(ValueError):
        store.feedback(9999, '科技', '')


def test_store_connection_is_closed_after_context(tmp_path):
    from newsroom.store import Store
    import sqlite3
    store = Store(tmp_path / 'db.sqlite3')
    with store.connect() as db:
        assert db.execute('SELECT 1').fetchone()[0] == 1
    with pytest.raises(sqlite3.ProgrammingError):
        db.execute('SELECT 1')


def test_api_origin_validation_and_prediction(tmp_path):
    from newsroom.server import create_server
    from newsroom.store import Store
    from newsroom.ml import ModelService
    from tests.test_ml import sample_parts
    from newsroom.ml import train_experiment
    folder = tmp_path / 'artifacts'
    train_experiment(sample_parts(), folder, quick=True)
    server = create_server(0, ModelService(folder), Store(tmp_path / 'store.db'))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        with urllib.request.urlopen(url + '/api/bootstrap') as response:
            bootstrap = json.load(response)
        body = json.dumps({'title': '足球联赛夺冠', 'model': 'lr', 'threshold': .65}).encode()
        request = urllib.request.Request(url + '/api/predict', body, headers={'Content-Type': 'application/json', 'X-Request-Token': bootstrap['token'], 'Origin': url})
        with urllib.request.urlopen(request) as response:
            result = json.load(response)
        assert result['result']['prediction'] == '体育' and result['result']['id'] > 0
        request = urllib.request.Request(url + '/api/predict', body, headers={'Content-Type': 'application/json', 'X-Request-Token': bootstrap['token'], 'Origin': 'https://evil.example'})
        with pytest.raises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        assert caught.value.code == 403
        with pytest.raises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(url + '/../run.py')
        assert caught.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
