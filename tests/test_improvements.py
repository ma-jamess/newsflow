import csv
import io
import json
import threading
import urllib.error
import urllib.request

import pytest


@pytest.fixture(scope='module')
def local_app(tmp_path_factory):
    from newsroom.ml import ModelService, train_experiment
    from newsroom.server import create_server
    from newsroom.store import Store
    from tests.test_ml import sample_parts
    folder = tmp_path_factory.mktemp('improved') / 'artifacts'
    train_experiment(sample_parts(), folder, quick=True)
    server = create_server(0, ModelService(folder), Store(folder / 'history.db'), artifacts=folder)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    token = json.load(urllib.request.urlopen(url + '/api/bootstrap'))['token']

    def post(path, payload, raw=False):
        request = urllib.request.Request(url + '/api/' + path, json.dumps(payload).encode(),
                                         headers={'Content-Type': 'application/json', 'Origin': url, 'X-Request-Token': token})
        with urllib.request.urlopen(request) as response:
            return response.read() if raw else json.load(response)
    yield folder, post
    server.shutdown()
    server.server_close()


def test_preview_validates_without_prediction_or_history(local_app):
    _, post = local_app
    result = post('preview', {'titles': ['足球联赛', '', '字' * 201]})
    assert result['total'] == 3 and result['invalid_count'] == 2
    assert len(result['rows']) == 3 and 'prediction' not in result['rows'][0]
    assert all('message' in row for row in result['rows'])


def test_same_title_comparison_is_three_models_without_saving_history(local_app):
    folder, post = local_app
    from newsroom.store import Store
    before = Store(folder / 'history.db').counts()['total']
    result = post('compare', {'title': '足球联赛球队夺冠', 'threshold': .65})
    assert result['title'] == '足球联赛球队夺冠'
    assert {row['model'] for row in result['rows']} == {'nb', 'lr', 'svm'}
    assert all(row['prediction'] == '体育' for row in result['rows'])
    assert Store(folder / 'history.db').counts()['total'] == before
    with pytest.raises(urllib.error.HTTPError) as error:
        post('compare', {'title': ''})
    assert error.value.code == 400


def test_errors_export_reads_full_prediction_file_not_report_sample(local_app):
    folder, post = local_app
    from newsroom.csvio import export_csv
    rows = [{'title': '=bad'+str(i), 'label': '体育', 'prediction': '科技', 'score': .6} for i in range(121)]
    rows.append({'title': '足球冠军', 'label': '体育', 'prediction': '体育', 'score': .9})
    (folder / 'svm_test_predictions.csv').write_bytes(export_csv(rows))
    data = post('errors', {'model': 'svm'}, raw=True)
    exported = list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
    assert len(exported) == 121
    assert exported[0]['title'] == "'=bad0"
    with pytest.raises(urllib.error.HTTPError) as error:
        post('errors', {'model': '../../run'})
    assert error.value.code == 400
