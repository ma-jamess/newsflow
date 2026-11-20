"""Recheck the fixed 4,989-title test set using saved models, without training."""
import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from threadpoolctl import threadpool_limits
from newsroom.data import prepare_splits, verify_raw
from newsroom.ml import ModelService, code_signature, metrics
from newsroom.model_reports import MODELS, model_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/model-verification.json')
    args = parser.parse_args()
    valid, reason = verify_raw(ROOT / 'data/raw')
    if not valid:
        raise ValueError(reason)
    service = ModelService(ROOT / 'artifacts')
    report = service.report
    if code_signature() != report['code_signature']:
        raise ValueError('训练核心源码与实验记录不同，不能沿用原实验结论')
    splits, audit = prepare_splits(ROOT / 'data/raw')
    rows = splits['test']
    test_hash = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if test_hash != report['test_data_sha256']:
        raise ValueError('测试数据与原实验记录不同')
    labels = [row['label'] for row in rows]
    titles = [row['title'] for row in rows]
    result = {'verified_at': datetime.now(timezone.utc).isoformat(), 'training_performed': False,
              'original_training_at': report['created_at'], 'test_count': len(rows),
              'test_data_sha256': test_hash, 'model_sha256': report['model_sha256'],
              'core_source_signature_matches': True, 'data_audit': audit,
              'recommended_model': report['recommended_model'], 'selection_basis': report['selection_source'],
              'models': {}}
    for kind in MODELS:
        started = time.perf_counter()
        bundle = service.models[kind]
        with threadpool_limits(limits=2):
            x = bundle['features'].transform(titles)
            probabilities = bundle['calibrated'].predict_proba(x)
        classes = bundle['calibrated'].classes_
        predictions = classes[probabilities.argmax(axis=1)]
        measured = metrics(labels, predictions, probabilities, classes)
        expected = report['models'][kind]['test']
        if measured['confusion_matrix'] != expected['confusion_matrix']:
            raise ValueError(f'{kind}: 混淆矩阵与原报告不同')
        for name in ['accuracy', 'macro_f1', 'ece', 'brier']:
            if not np.isclose(measured[name], expected[name], rtol=0, atol=1e-8):
                raise ValueError(f'{kind}: {name} 与原报告不同')
        path = ROOT / f'artifacts/{kind}_test_predictions.csv'
        saved = list(csv.DictReader(path.open(encoding='utf-8-sig', newline='')))
        if len(saved) != len(rows):
            raise ValueError(f'{kind}: 测试 CSV 数量不同')
        for old, row, prediction, score in zip(saved, rows, predictions, probabilities.max(axis=1)):
            if (old['title'], old['label'], old['prediction']) != (row['title'], row['label'], str(prediction)):
                raise ValueError(f'{kind}: 测试 CSV 与当前复核预测不同')
            if abs(float(old['score']) - round(float(score), 6)) > 1e-8:
                raise ValueError(f'{kind}: 测试 CSV 概率不同')
        correct = int(np.sum(np.asarray(labels) == predictions))
        result['models'][kind] = {'test': measured, 'correct': correct, 'errors': len(rows) - correct,
                                 'recorded_metrics_match': True, 'saved_predictions_match': True,
                                 'verification_seconds': round(time.perf_counter() - started, 3),
                                 'prediction_file_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        destination = ROOT / f'docs/model-reports/{kind}-验证报告.md'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(model_report(report, kind), encoding='utf-8')
        print(f'{kind}: {correct}/{len(rows)}，accuracy={measured["accuracy"]:.6f}，与原报告一致', flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('已有模型复核完成；未训练，未更改模型和原报告。', flush=True)


if __name__ == '__main__':
    main()
