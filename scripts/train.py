"""直接运行可复现的完整训练：python scripts/train.py。"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from newsroom.data import prepare_splits, verify_raw
from newsroom.ml import train_experiment


def main():
    ok, message = verify_raw(ROOT / 'data' / 'raw')
    if not ok:
        raise ValueError(message + '，请执行 python scripts/prepare_data.py')
    splits, audit = prepare_splits(ROOT / 'data' / 'raw')
    report = train_experiment(splits, ROOT / 'artifacts')
    report['data_audit'] = audit
    report['test_data_sha256'] = hashlib.sha256(json.dumps(splits['test'], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    report['source_manifest'] = json.loads((ROOT / 'data' / 'raw' / 'manifest.json').read_text(encoding='utf-8-sig'))
    (ROOT / 'artifacts' / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[train] 推荐算法（只按选参集决定）:', report['recommended_model'])
    for key, model in report['models'].items():
        print(key, 'accuracy=', round(model['test']['accuracy'], 6), 'macro_f1=', round(model['test']['macro_f1'], 6))
    return 0


if __name__ == '__main__':
    sys.exit(main())
