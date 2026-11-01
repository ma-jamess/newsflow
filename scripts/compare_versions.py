"""按标题和标签严格对齐两份已有测试预测，生成样本级对比。只读输入。"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def compare(old_path, new_path):
    old, new = read_rows(old_path), read_rows(new_path)
    if [(r['title'], r['label']) for r in old] != [(r['title'], r['label']) for r in new]:
        raise ValueError('两份预测的标题、标签或顺序不一致，不能直接比较')
    counts = {'both_correct': 0, 'new_correct_old_wrong': 0, 'old_correct_new_wrong': 0, 'both_wrong': 0}
    changes = []
    for left, right in zip(old, new):
        a, b = left['prediction'] == left['label'], right['prediction'] == right['label']
        key = 'both_correct' if a and b else 'old_correct_new_wrong' if a else 'new_correct_old_wrong' if b else 'both_wrong'
        counts[key] += 1
        if a != b:
            changes.append({'title': right['title'], 'label': right['label'], 'old_prediction': left['prediction'],
                            'new_prediction': right['prediction'], 'change': '新版改正' if b else '新版退步'})
    per_class = {}
    for label in sorted({r['label'] for r in new}):
        selected = [(a, b) for a, b in zip(old, new) if b['label'] == label]
        per_class[label] = {'count': len(selected), 'old_recall': sum(a['prediction'] == label for a, b in selected) / len(selected),
                            'new_recall': sum(b['prediction'] == label for a, b in selected) / len(selected)}
    return {'count': len(new), 'aligned': True, 'counts': counts, 'per_class': per_class,
            'accuracy_delta_percentage_points': (counts['new_correct_old_wrong'] - counts['old_correct_new_wrong']) / len(new) * 100,
            'input_sha256': {name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for name, path in [('old', old_path), ('new', new_path)]}}, changes


def main():
    parser = argparse.ArgumentParser(description='只读对比两份同测试集预测')
    parser.add_argument('--old', required=True, type=Path)
    parser.add_argument('--new', type=Path, default=ROOT / 'artifacts' / 'svm_test_predictions.csv')
    args = parser.parse_args()
    summary, changes = compare(args.old, args.new)
    from sys import path
    path.insert(0, str(ROOT))
    from newsroom.csvio import export_csv
    (ROOT / 'docs' / 'paired-comparison.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'docs' / '逐条差异.csv').write_bytes(export_csv(changes))
    print(summary['counts'])


if __name__ == '__main__':
    main()
