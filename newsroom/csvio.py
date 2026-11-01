"""严格 CSV 输入与安全导出；保留逐行状态。"""
import csv
import io

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000


def parse_csv(content):
    if len(content) > MAX_BYTES:
        raise ValueError('文件不能超过5 MB')
    if not content.strip():
        raise ValueError('CSV 文件为空')
    text = None
    for encoding in ['utf-8-sig', 'gb18030']:
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None or '\x00' in text:
        raise ValueError('无法识别文本编码，请使用 UTF-8 或 GB18030 CSV')
    try:
        reader = csv.reader(io.StringIO(text), strict=True)
        header = [value.strip() for value in next(reader)]
        if len(header) != len(set(header)):
            raise ValueError('表头重复')
        title_cols = [i for i, name in enumerate(header) if name in ['title', '标题']]
        label_cols = [i for i, name in enumerate(header) if name in ['label', '真实类别']]
        if len(title_cols) != 1 or len(label_cols) > 1:
            raise ValueError('必须有且仅有一列 title 或 标题，可选一列 label 或 真实类别')
        rows = []
        for row in reader:
            if not row:
                row = [''] * len(header)
            if len(row) != len(header):
                raise ValueError(f'第{reader.line_num}行列数不一致')
            item = {'title': row[title_cols[0]]}
            if label_cols:
                item['label'] = row[label_cols[0]].strip()
            rows.append(item)
            if len(rows) > MAX_ROWS:
                raise ValueError('每批最多5000条')
        if not rows:
            raise ValueError('CSV 没有数据行')
        return rows
    except (StopIteration, csv.Error) as error:
        raise ValueError('CSV 格式错误，请检查引号和分隔符') from error


def export_csv(rows):
    if not rows:
        return b'\xef\xbb\xbf'
    output = io.StringIO(newline='')
    columns = list(dict.fromkeys(key for row in rows for key in row))
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        safe = {}
        for key, value in row.items():
            if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
                value = "'" + value
            safe[key] = value
        writer.writerow(safe)
    return output.getvalue().encode('utf-8-sig')
