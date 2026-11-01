import json
from pathlib import Path

import pytest


def sample_parts():
    groups = {'体育': '足球 球队 联赛 冠军', '科技': '人工智能 芯片 计算机 科技', '教育': '高考 招生 学校 教育', '财经': '股票 银行 投资 财经', '娱乐': '电影 明星 导演 娱乐'}
    return {split: [{'title': f'{words} {split} {i}', 'label': label} for label, words in groups.items() for i in range(count)] for split, count in [('train', 15), ('dev', 12), ('test', 5)]}


@pytest.fixture(scope='module')
def trained(tmp_path_factory):
    from newsroom.ml import train_experiment
    folder = tmp_path_factory.mktemp('models')
    report = train_experiment(sample_parts(), folder, quick=True)
    return folder, report


def test_feature_vocabulary_does_not_learn_validation_text():
    from newsroom.ml import build_features
    features = build_features('joint', tiny=True)
    features.fit(['足球联赛冠军', '人工智能芯片', '高考招生学校'])
    features.transform(['验证独有火星量子'])
    assert all('火星' not in n and '量子' not in n for n in features.get_feature_names_out())


def test_parameter_selection_and_calibration_are_disjoint(trained):
    _, report = trained
    assert set(report['development_split']['selection_indices']).isdisjoint(report['development_split']['calibration_indices'])
    assert report['recommended_model'] in ['nb', 'lr', 'svm']
    assert report['selection_source'] == 'dev_selection_only'
    assert all(0 <= m['test']['accuracy'] <= 1 for m in report['models'].values())


def test_prediction_explanation_and_batch_agree(trained):
    from newsroom.ml import ModelService
    service = ModelService(trained[0])
    title = '足球联赛球队夺冠'
    single = service.predict([title], explain=True)[0]
    batch = service.predict([title, '', '!', '字' * 201, 'zzqvwxzzqvwx'])
    assert single['prediction'] == '体育'
    assert batch[0]['prediction'] == single['prediction']
    assert batch[0]['score'] == single['score']
    assert single['evidence'] and all(e['feature'] for e in single['evidence'])
    assert abs(sum(single['probabilities'].values()) - 1) < 1e-5
    assert all(r['status'] == 'invalid' for r in batch[1:4])
    assert batch[4]['status'] == 'unknown' and not batch[4]['prediction']


def test_model_hash_is_checked_before_loading(trained, tmp_path):
    from newsroom.ml import ModelService
    import shutil
    for path in trained[0].iterdir():
        shutil.copy2(path, tmp_path / path.name)
    with (tmp_path / 'models.joblib').open('ab') as stream:
        stream.write(b'tamper')
    with pytest.raises(ValueError, match='校验'):
        ModelService(tmp_path)
