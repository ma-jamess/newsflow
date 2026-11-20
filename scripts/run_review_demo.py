"""Run the real local app with an archived news case in separate demo storage."""
import argparse
import html
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from newsroom.deepseek import DeepSeekService
from newsroom.live_news import LiveNewsService
from newsroom.ml import ModelService
from newsroom.news_store import NewsStore
from newsroom.store import Store
import newsroom.server as server_module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8523)
    args = parser.parse_args()
    case = json.loads((ROOT / 'examples/review-case.json').read_text(encoding='utf-8'))
    row = case['article']
    service = ModelService(ROOT / 'artifacts')
    folder = ROOT / 'runtime/review-demo'
    folder.mkdir(parents=True, exist_ok=True)
    assert folder.resolve().is_relative_to((ROOT / 'runtime').resolve())
    news = NewsStore(folder / 'news.sqlite3')
    result = service.predict([row['title'][:200]], model='svm', explain=True)[0]
    news.ingest(row['source_id'], [row], [result], datetime.fromisoformat(case['snapshot_generated_at']))
    news.bookmark(row['id'], True)
    live = LiveNewsService(news, service)
    live.stop()  # This review mode must not pretend that it is fetching fresh news.
    assets = folder / 'assets/web'
    shutil.copytree(ROOT / 'web', assets, dirs_exist_ok=True)
    page = (assets / 'index.html').read_text(encoding='utf-8')
    banner = '<div class="alert">归档案例演示：数据来自 ' + html.escape(case['snapshot_generated_at'])
    banner += ' 的公开快照，不自动采集新新闻。点击“我的收藏”，搜索“福州”。本模式使用真实模型与独立 SQLite，记录不影响日常数据。</div>'
    page = page.replace('<div class="content">', '<div class="content">' + banner, 1)
    page = page.replace('<h1>最新新闻</h1>', '<h1>归档案例</h1>')
    page = page.replace('按主题浏览近 72 小时的订阅新闻。', '使用公开快照演示分类与保存，原始发布时间保留。')
    page = page.replace('id="news-refresh" class="primary news-refresh"', 'id="news-refresh" class="primary news-refresh hidden"')
    page = page.replace('定时检查订阅', '归档案例演示').replace('本地运行 <i></i>', '演示模式 <i></i>')
    (assets / 'index.html').write_text(page, encoding='utf-8')
    server_module.ROOT = folder / 'assets'
    server = server_module.create_server(args.port, service, Store(folder / 'history.sqlite3'),
                                          artifacts=ROOT / 'artifacts', live=live,
                                          deepseek=DeepSeekService(api_key=''))
    print(f'归档案例演示：http://127.0.0.1:{args.port}。先点“我的收藏”，再搜索福州。', flush=True)
    print('未训练，不自动抓取，不调用第三方模型。Ctrl+C退出。', flush=True)
    try:
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
