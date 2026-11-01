"""打包完整源码、公开数据和模型，排除环境、个人运行记录、QA中间文件。"""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {'.venv', '.git', '__pycache__', '.pytest_cache', 'runtime', 'dist', 'qa', '.clean-verify',
                'output', '.playwright-cli', 'node_modules', 'site'}


def included(path):
    relative = path.relative_to(ROOT)
    return (not any(part in EXCLUDE_DIRS for part in relative.parts)
            and not any(part == '.env' or part.startswith('.env.') for part in relative.parts)
            and path.suffix.lower() not in {'.log', '.env', '.sqlite3', '.pyc'}
            and not path.name.endswith(('.sqlite3-shm', '.sqlite3-wal')))


def main():
    folder = ROOT / 'dist'
    folder.mkdir(exist_ok=True)
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and included(p))
    # 清单覆盖交付内容，但不能包含其自身的旧哈希。
    inventory_path = ROOT / 'docs' / 'source-inventory.json'
    inventory = [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
                  'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    inventory = [row for row in inventory if row['path'] != 'docs/source-inventory.json']
    inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and included(p))
    destination = folder / 'NewsFlow_1.4_完整源码.zip'
    top = 'NewsFlow'
    with ZipFile(destination, 'w', compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, top + '/' + path.relative_to(ROOT).as_posix())
    with ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP 校验失败')
        print('文件数:', len(archive.namelist()))
    print('完整源码包:', destination)
    print('大小 MB:', round(destination.stat().st_size / 1024 / 1024, 2))


if __name__ == '__main__':
    main()
