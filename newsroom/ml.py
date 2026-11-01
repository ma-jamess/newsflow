"""训练、概率校准、评估与线性特征解释；不依赖外部推理 API。"""
import json
import logging
import platform
import re
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import jieba
import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

from newsroom.data import CATEGORIES, digest_file, normalize, title_error
from newsroom.csvio import export_csv

jieba.setLogLevel(logging.ERROR)
MODEL_NAMES = {'nb': '朴素贝叶斯 · 词特征', 'lr': '逻辑回归 · 字词联合', 'svm': '线性 SVM · 字词联合'}
PARAMETERS = {'nb': [.1, .5, 1.0], 'lr': [1., 4.], 'svm': [.5, 1., 2.]}
SCHEMA = 1


def tokenize(text):
    return [word for word in jieba.lcut(normalize(text), HMM=False) if re.search(r'[a-z0-9\u4e00-\u9fff]', word)]


def build_features(kind, tiny=False):
    word = TfidfVectorizer(tokenizer=tokenize, token_pattern=None, lowercase=False,
                           ngram_range=(1, 2), min_df=1 if tiny else 2,
                           max_features=1500 if tiny else 40000, sublinear_tf=True, dtype=np.float64)
    if kind == 'word':
        return word
    char = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), min_df=1 if tiny else 3,
                           max_features=2500 if tiny else 70000, sublinear_tf=True, lowercase=False)
    return FeatureUnion([('word', word), ('char', char)], transformer_weights={'word': 1., 'char': .7})


def classifier_for(kind, parameter):
    if kind == 'nb':
        return MultinomialNB(alpha=parameter)
    if kind == 'lr':
        return LogisticRegression(C=parameter, max_iter=700, solver='lbfgs', random_state=42)
    return LinearSVC(C=parameter, max_iter=3000, random_state=42, dual='auto')


def metrics(labels, predicted, probabilities=None, classes=None):
    result = {'accuracy': float(accuracy_score(labels, predicted)),
              'macro_f1': float(f1_score(labels, predicted, labels=CATEGORIES, average='macro', zero_division=0)),
              'confusion_matrix': confusion_matrix(labels, predicted, labels=CATEGORIES).tolist(),
              'per_class': classification_report(labels, predicted, labels=CATEGORIES, output_dict=True, zero_division=0)}
    if probabilities is not None:
        probabilities = np.asarray(probabilities)
        confidence = probabilities.max(axis=1)
        correct = np.asarray(labels) == np.asarray(predicted)
        one_hot = (np.asarray(labels)[:, None] == np.asarray(classes)[None, :]).astype(float)
        result['brier'] = float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1)))
        bins, ece = [], 0.
        for low in np.arange(0., 1., .1):
            mask = (confidence >= low) & (confidence < low + .1 if low < .89 else confidence <= 1.)
            count = int(mask.sum())
            if count:
                average, accuracy = float(confidence[mask].mean()), float(correct[mask].mean())
                ece += count / len(labels) * abs(average - accuracy)
                bins.append({'lower': round(float(low), 1), 'count': count, 'confidence': average, 'accuracy': accuracy})
        result.update(ece=ece, calibration_bins=bins)
        accepted = confidence >= .65
        result['coverage_at_065'] = float(accepted.mean())
        result['accuracy_at_065'] = float(correct[accepted].mean()) if accepted.any() else None
    return result


def environment():
    return {'python': platform.python_version(), **{name: version(name) for name in ['scikit-learn', 'numpy', 'scipy', 'jieba', 'joblib']}}


def code_signature():
    return {name: digest_file(Path(__file__).parent / name) for name in ['ml.py', 'data.py']}


def train_experiment(splits, output, quick=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in splits.items():
        if set(row['label'] for row in rows) != set(CATEGORIES):
            raise ValueError(f'{name} 必须包含五类')
    indices = np.arange(len(splits['dev']))
    selection, calibration = train_test_split(indices, test_size=.5, random_state=42,
                                               stratify=[row['label'] for row in splits['dev']])
    selection, calibration = sorted(selection.tolist()), sorted(calibration.tolist())
    texts = {name: [r['title'] for r in rows] for name, rows in splits.items()}
    labels = {name: [r['label'] for r in rows] for name, rows in splits.items()}
    report = {'schema': SCHEMA, 'created_at': datetime.now(timezone.utc).isoformat(), 'seed': 42,
              'categories': CATEGORIES, 'selection_source': 'dev_selection_only',
              'development_split': {'selection_indices': selection, 'calibration_indices': calibration,
                                    'selection_count': len(selection), 'calibration_count': len(calibration)},
              'split_counts': {name: len(rows) for name, rows in splits.items()}, 'environment': environment(),
              'code_signature': code_signature(), 'models': {}, 'candidates': []}
    started = time.perf_counter()
    matrices, features = {}, {}
    for feature_kind in ['word', 'joint']:
        print(f'[train] 提取 {feature_kind} 特征（仅训练集拟合）', flush=True)
        features[feature_kind] = build_features(feature_kind, tiny=quick)
        x_train = features[feature_kind].fit_transform(texts['train'])
        x_dev = features[feature_kind].transform(texts['dev'])
        matrices[feature_kind] = (x_train, x_dev)
    chosen = {}
    for kind in MODEL_NAMES:
        feature_kind = 'word' if kind == 'nb' else 'joint'
        x_train, x_dev = matrices[feature_kind]
        best = -1.
        for parameter in PARAMETERS[kind][:1] if quick else PARAMETERS[kind]:
            print(f'[train] {kind}, parameter={parameter}', flush=True)
            raw = classifier_for(kind, parameter)
            fit_start = time.perf_counter()
            with threadpool_limits(limits=2):
                raw.fit(x_train, labels['train'])
            seconds = time.perf_counter() - fit_start
            selection_metrics = metrics(np.asarray(labels['dev'])[selection], raw.predict(x_dev[selection]))
            report['candidates'].append({'model': kind, 'parameter': parameter,
                                         'selection_macro_f1': selection_metrics['macro_f1'], 'fit_seconds': seconds})
            if selection_metrics['macro_f1'] > best:
                best = selection_metrics['macro_f1']
                chosen[kind] = raw
                report['models'][kind] = {'name': MODEL_NAMES[kind], 'parameter': parameter,
                                          'selection': selection_metrics, 'fit_seconds': seconds,
                                          'feature_count': x_train.shape[1], 'feature_kind': feature_kind}
    # 算法和参数在碰触测试集特征、测试集指标前锁定。
    report['recommended_model'] = max(chosen, key=lambda k: report['models'][k]['selection']['macro_f1'])
    bundles = {}
    for kind, raw in chosen.items():
        feature_kind = report['models'][kind]['feature_kind']
        _, x_dev = matrices[feature_kind]
        print(f'[train] 校准 {kind}（独立 dev_calibration）', flush=True)
        calibrated = CalibratedClassifierCV(FrozenEstimator(raw), method='sigmoid', ensemble=False)
        calibrated.fit(x_dev[calibration], np.asarray(labels['dev'])[calibration])
        bundles[kind] = {'features': features[feature_kind], 'raw': raw, 'calibrated': calibrated}
    for kind, bundle in bundles.items():
        print(f'[train] 最终独立测试 {kind}', flush=True)
        test_start = time.perf_counter()
        x_test = bundle['features'].transform(texts['test'])
        prob = bundle['calibrated'].predict_proba(x_test)
        predicted = bundle['calibrated'].classes_[prob.argmax(axis=1)]
        item = report['models'][kind]
        item['test_seconds'] = time.perf_counter() - test_start
        item['test'] = metrics(labels['test'], predicted, prob, bundle['calibrated'].classes_)
        raw_pred = bundle['raw'].predict(x_test)
        raw_prob = bundle['raw'].predict_proba(x_test) if hasattr(bundle['raw'], 'predict_proba') else None
        item['before_calibration'] = metrics(labels['test'], raw_pred, raw_prob, bundle['raw'].classes_)
        result_rows = [{'title': title, 'label': label, 'prediction': str(p), 'score': round(float(s), 6)}
                       for title, label, p, s in zip(texts['test'], labels['test'], predicted, prob.max(axis=1))]
        (output / f'{kind}_test_predictions.csv').write_bytes(export_csv(result_rows))
        item['errors'] = [r for r in result_rows if r['label'] != r['prediction']][:100]
    majority = max(CATEGORIES, key=lambda c: labels['train'].count(c))
    report['majority_baseline'] = {'class': majority, **metrics(labels['test'], [majority] * len(labels['test']))}
    report['total_seconds'] = time.perf_counter() - started
    bundle_path = output / 'models.joblib'
    pending = output / 'models.joblib.tmp'
    joblib.dump(bundles, pending, compress=3)
    pending.replace(bundle_path)
    report['model_sha256'] = digest_file(bundle_path)
    report['model_bytes'] = bundle_path.stat().st_size
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


class ModelService:
    def __init__(self, folder):
        folder = Path(folder)
        self.report = json.loads((folder / 'report.json').read_text(encoding='utf-8'))
        if self.report.get('schema') != SCHEMA:
            raise ValueError('模型格式不兼容，请重新训练')
        if digest_file(folder / 'models.joblib') != self.report.get('model_sha256'):
            raise ValueError('模型 SHA-256 校验失败，请重新训练')
        self.models = joblib.load(folder / 'models.joblib')
        self.feature_names = {}

    def predict(self, titles, model=None, threshold=.65, explain=False):
        model = model or self.report['recommended_model']
        if model not in self.models:
            raise ValueError('不支持的模型')
        if not isinstance(threshold, (int, float)) or not .2 <= threshold <= .95:
            raise ValueError('阈值应在0.20到0.95之间')
        bundle = self.models[model]
        started = time.perf_counter()
        results, valid, cleaned = [], [], []
        for index, title in enumerate(titles):
            error = title_error(title)
            row = {'title': title, 'prediction': '', 'score': None, 'status': 'invalid' if error else 'pending',
                   'message': error, 'probabilities': {}, 'model': model}
            results.append(row)
            if not error:
                valid.append(index)
                cleaned.append(normalize(title))
        if cleaned:
            x = bundle['features'].transform(cleaned)
            prob = bundle['calibrated'].predict_proba(x)
            classes = bundle['calibrated'].classes_
            for local, index in enumerate(valid):
                row = results[index]
                if x[local].nnz == 0:
                    row.update(status='unknown', message='未识别到训练词语或字符片段，请补充具体信息')
                    continue
                order = np.argsort(prob[local])[::-1]
                chosen, second = order[:2]
                score = float(prob[local, chosen])
                margin = score - float(prob[local, second])
                review = score < threshold or margin < .15
                row.update(prediction=str(classes[chosen]), score=round(score, 6), margin=round(margin, 6),
                           status='review' if review else 'ok', message='建议人工核对' if review else '分类完成',
                           probabilities={str(c): round(float(p), 6) for c, p in zip(classes, prob[local])})
                if explain:
                    row['tokens'] = tokenize(cleaned[local])
                    row['evidence'] = self.explain(bundle, x[local], str(classes[chosen]), str(classes[second]), model)
        elapsed = (time.perf_counter() - started) * 1000
        for row in results:
            row['elapsed_ms'] = round(elapsed / max(1, len(results)), 2)
        return results

    def explain(self, bundle, row, chosen, runner_up, model):
        raw = bundle['raw']
        names = self.feature_names.setdefault(model, bundle['features'].get_feature_names_out())
        class_list = list(raw.classes_)
        weights = raw.feature_log_prob_ if model == 'nb' else raw.coef_
        difference = weights[class_list.index(chosen)] - weights[class_list.index(runner_up)]
        contribution = row.data * difference[row.indices]
        positive = sorted(zip(row.indices, contribution), key=lambda pair: pair[1], reverse=True)
        return [{'feature': str(names[index]).replace('word__', '').replace('char__', ''),
                 'kind': '字符片段' if str(names[index]).startswith('char__') else '词语',
                 'contribution': round(float(value), 5), 'against': runner_up}
                for index, value in positive[:10] if value > 0]
