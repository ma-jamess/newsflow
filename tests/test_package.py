import hashlib
import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile


def test_package_inventory_matches_payload_and_does_not_hash_itself(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'scripts' / 'package.py'
    spec = importlib.util.spec_from_file_location('package_script', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'run.py').write_text('print("demo")', encoding='utf-8')
    (tmp_path / 'docs' / 'source-inventory.json').write_text('[]', encoding='utf-8')
    module.main()
    inventory = json.loads((tmp_path / 'docs' / 'source-inventory.json').read_text(encoding='utf-8'))
    assert 'docs/source-inventory.json' not in {row['path'] for row in inventory}
    with ZipFile(next((tmp_path / 'dist').glob('*.zip'))) as archive:
        for row in inventory:
            content = archive.read('NewsFlow/' + row['path'])
            assert len(content) == row['bytes']
            assert hashlib.sha256(content).hexdigest() == row['sha256']


def test_newsflow_package_is_shareable_complete_source_without_personal_or_qa_files(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'scripts' / 'package.py'
    spec = importlib.util.spec_from_file_location('newsflow_package_script', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    public = ['run.py', 'README.md', 'README_EN.md', 'LICENSE', 'docs/newsflow-guide.md',
              'newsroom/live_news.py', 'web/live-news.js', 'tests/test_live_news.py',
              'artifacts/model.joblib', 'data/raw/LICENSE', 'third_party/lucide/LICENSE']
    private = ['runtime/deepseek.env', 'runtime/news.sqlite3', '.env', '.env.secret', 'deepseek.env',
               'qa/newsflow/debug.json', 'output/playwright/newsflow.png',
               '.playwright-cli/page.yml', 'node_modules/demo/index.js', 'cache.sqlite3', 'debug.log']
    for name in public + private:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(('public' if name in public else 'TEST-ONLY-PRIVATE-SENTINEL').encode())
    (tmp_path / 'docs/source-inventory.json').write_text('[]', encoding='utf-8')
    module.main()
    archive_path = tmp_path / 'dist/NewsFlow_1.4_完整源码.zip'
    assert archive_path.exists()
    with ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert all('NewsFlow/' + name in names for name in public)
        assert not any('NewsFlow/' + name in names for name in private)
        assert all(b'TEST-ONLY-PRIVATE-SENTINEL' not in archive.read(name) for name in names)
