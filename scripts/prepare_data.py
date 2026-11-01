"""恢复随项目附带的公开数据，按固定上游提交和预期 SHA-256 校验。"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '6cb26819af7b646275aff8a4693676f2849e67f6'
BASE = f'https://raw.githubusercontent.com/649453932/Chinese-Text-Classification-Pytorch/{COMMIT}/'
EXPECTED = {'class.txt': '005e8813ad639c219e5902dc84889202b4a717b4238497d26c3fbd5e43927a86',
            'train.txt': 'ba6fcbbb8fb809a9eb2be443b6b4db533c147861d94ebe0931b8c6092d8abe94',
            'dev.txt': '6ed73aa2c57ee1560c8f76570d48735c4b1c29ae4983fe3523d56e115813e175',
            'test.txt': 'ebecc8c896635ad69730083ca7b81d37c42c9a5779bc05c9d2479d894e34f026',
            'README.md': '5dd0c7071b71e7fce3582762cf34f63b8347180cb81e47973161f6708d1ca9b7',
            'LICENSE': 'c59122f7624279cb08820f671fc5a30fb72d97fbe84fc2f1603ba4df70967ad4'}


def main():
    folder = ROOT / 'data' / 'raw'
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {'commit': COMMIT, 'repository': BASE, 'files': {}}
    for name, digest in EXPECTED.items():
        path = folder / name
        url = BASE + ('THUCNews/data/' if name.endswith('.txt') else '') + name
        content = path.read_bytes() if path.exists() else b''
        if hashlib.sha256(content).hexdigest() != digest:
            print('[data] 下载', name, flush=True)
            with urllib.request.urlopen(url, timeout=60) as response:
                content = response.read(12 * 1024 * 1024)
            if hashlib.sha256(content).hexdigest() != digest:
                raise ValueError(f'{name} 远程数据校验失败')
            path.write_bytes(content)
        manifest['files'][name] = {'sha256': digest, 'bytes': len(content), 'url': url}
    (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('[data] 全部校验通过')


if __name__ == '__main__':
    main()
