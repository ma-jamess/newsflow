import csv
import io
import json
from pathlib import Path

import pytest


def test_normalization_handles_html_and_full_width():
    from newsroom.data import normalize
    assert normalize('  <b>ＡＩ</b> &amp; 科技\n新闻 ') == 'ai & 科技 新闻'
    assert normalize(None) == ''


def test_cross_split_duplicates_and_conflicts_removed(tmp_path):
    from newsroom.data import prepare_splits
    (tmp_path / 'class.txt').write_text('sports\nscience\neducation\nfinance\nentertainment', encoding='utf-8')
    (tmp_path / 'train.txt').write_text('足球夺冠\t0\n标签冲突\t0\n\t0\n', encoding='utf-8')
    (tmp_path / 'dev.txt').write_text('足球！夺冠\t0\n标签冲突\t1\n科技新发现\t1\n', encoding='utf-8')
    (tmp_path / 'test.txt').write_text('科技新发现\t1\n电影上映\t4\n', encoding='utf-8')
    parts, audit = prepare_splits(tmp_path)
    assert parts['train'] == [{'title': '足球夺冠', 'label': '体育'}]
    assert parts['dev'] == [{'title': '科技新发现', 'label': '科技'}]
    assert parts['test'] == [{'title': '电影上映', 'label': '娱乐'}]
    assert audit['duplicate_rows_removed'] == 2
    assert audit['conflicting_rows_removed'] == 2
    assert audit['invalid_titles_removed'] == 1


def test_upload_encoding_and_empty_title_preserved():
    from newsroom.csvio import parse_csv
    rows = parse_csv('标题,真实类别\r\n足球夺冠,体育\r\n,科技\r\n'.encode('gb18030'))
    assert rows == [{'title': '足球夺冠', 'label': '体育'}, {'title': '', 'label': '科技'}]


@pytest.mark.parametrize('content', [b'', b'title,title\na,b', b'title,\xe6\xa0\x87\xe9\xa2\x98\na,b', b'title\na,b', b'title\n"broken', b'title\n\x00'])
def test_invalid_csv_rejected(content):
    from newsroom.csvio import parse_csv
    with pytest.raises(ValueError):
        parse_csv(content)


def test_csv_row_limit_and_formula_protection():
    from newsroom.csvio import parse_csv, export_csv
    with pytest.raises(ValueError):
        parse_csv(('title\n' + '足球\n' * 5001).encode())
    decoded = export_csv([{'title': ' \t=1+1', 'prediction': '体育', 'score': .8}]).decode('utf-8-sig')
    assert list(csv.DictReader(io.StringIO(decoded)))[0]['title'] == "' \t=1+1"


def test_raw_manifest_detects_changes(tmp_path):
    from newsroom.data import digest_file, verify_raw
    for name in ['class.txt', 'train.txt', 'dev.txt', 'test.txt', 'README.md', 'LICENSE']:
        (tmp_path / name).write_text('ok', encoding='utf-8')
    info = {'files': {n.name: {'sha256': digest_file(n)} for n in tmp_path.iterdir()}}
    (tmp_path / 'manifest.json').write_text(json.dumps(info), encoding='utf-8')
    assert verify_raw(tmp_path)[0]
    (tmp_path / 'train.txt').write_text('changed', encoding='utf-8')
    assert not verify_raw(tmp_path)[0]


def test_physical_empty_csv_row_keeps_alignment():
    from newsroom.csvio import parse_csv
    assert parse_csv('title,label\n足球,体育\n\n芯片,科技\n'.encode()) == [
        {'title': '足球', 'label': '体育'}, {'title': '', 'label': ''}, {'title': '芯片', 'label': '科技'}]
