"""可审计的标题归一化、去重与公开数据校验。"""
import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path

CATEGORIES = ['体育', '科技', '教育', '财经', '娱乐']
LABELS = dict(zip(['sports', 'science', 'education', 'finance', 'entertainment'], CATEGORIES))
RAW_FILES = ('class.txt', 'train.txt', 'dev.txt', 'test.txt', 'README.md', 'LICENSE')
MAX_TITLE = 200


def normalize(value):
    if value is None:
        return ''
    text = unicodedata.normalize('NFKC', html.unescape(str(value)))
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', ' ', text)).strip().lower()


def title_error(value):
    if not isinstance(value, str):
        return '标题必须是文本'
    text = normalize(value)
    if not text:
        return '标题为空'
    if len(value) > MAX_TITLE or len(text) > MAX_TITLE:
        return '标题超过200字'
    if not re.search(r'[a-z0-9\u4e00-\u9fff]', text):
        return '请输入包含文字的标题'
    return ''


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_raw(folder):
    folder = Path(folder)
    try:
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        for name in RAW_FILES:
            if digest_file(folder / name) != manifest['files'][name]['sha256']:
                return False, f'{name} 校验失败'
    except (OSError, KeyError, ValueError, TypeError):
        return False, '数据文件或校验清单缺失/损坏'
    return True, '六个源文件 SHA-256 校验通过'


def prepare_splits(folder):
    folder = Path(folder)
    names = (folder / 'class.txt').read_text(encoding='utf-8').splitlines()
    records = []
    labels_by_key = {}
    audit = {'raw_rows': {}, 'selected_rows': 0, 'invalid_titles_removed': 0}
    for split in ['train', 'dev', 'test']:
        lines = (folder / f'{split}.txt').read_text(encoding='utf-8').splitlines()
        audit['raw_rows'][split] = len(lines)
        for number, line in enumerate(lines, 1):
            try:
                title, index = line.rsplit('\t', 1)
                index = int(index)
                if not 0 <= index < len(names):
                    raise ValueError('标签范围错误')
            except ValueError as error:
                raise ValueError(f'{split} 第 {number} 行格式或标签错误') from error
            label = LABELS.get(names[index])
            if label is None:
                continue
            audit['selected_rows'] += 1
            title = normalize(title)
            key = re.sub(r'[^\w\u4e00-\u9fff]', '', title)
            if not key or len(title) > MAX_TITLE:
                audit['invalid_titles_removed'] += 1
                continue
            records.append((split, title, label, key))
            labels_by_key.setdefault(key, set()).add(label)
    conflicts = {key for key, labels in labels_by_key.items() if len(labels) > 1}
    audit.update(conflicting_titles=len(conflicts), conflicting_rows_removed=0, duplicate_rows_removed=0)
    seen, splits = set(), {name: [] for name in ['train', 'dev', 'test']}
    for split, title, label, key in records:
        if key in conflicts:
            audit['conflicting_rows_removed'] += 1
        elif key in seen:
            audit['duplicate_rows_removed'] += 1
        else:
            seen.add(key)
            splits[split].append({'title': title, 'label': label})
    audit['split_counts'] = {name: len(rows) for name, rows in splits.items()}
    audit['class_counts'] = {name: {label: sum(r['label'] == label for r in rows) for label in CATEGORIES} for name, rows in splits.items()}
    audit['cross_split_overlap'] = 0
    return splits, audit
