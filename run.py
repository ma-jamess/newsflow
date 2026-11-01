"""入口：python run.py。独立环境、自检、本地服务、默认打开 Edge。"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8510


def log(message):
    print('[Codex 毕设] ' + message, flush=True)


def choose_environment(no_install):
    venv_python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        return subprocess.call([str(venv_python), str(ROOT / 'run.py'), *sys.argv[1:]], cwd=ROOT)
    if not venv_python.exists() and not no_install:
        log('正在创建项目独立 Python 环境')
        subprocess.run([sys.executable, '-m', 'venv', str(ROOT / '.venv')], check=True)
        subprocess.run([str(venv_python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], check=True)
        return subprocess.call([str(venv_python), str(ROOT / 'run.py'), *sys.argv[1:]], cwd=ROOT)
    modules = ['sklearn', 'jieba', 'numpy', 'scipy', 'joblib', 'threadpoolctl']
    missing = [name for name in modules if importlib.util.find_spec(name) is None]
    compatible = False
    if not missing:
        import sklearn
        compatible = sklearn.__version__ == '1.6.1'
    if missing or not compatible:
        if no_install:
            raise ValueError('依赖缺失或版本不同；请执行 python -m pip install -r requirements.txt')
        log('正在安装项目依赖')
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], check=True)
    return None


def open_edge(url):
    if os.name == 'nt':
        for root in [os.environ.get('PROGRAMFILES(X86)', ''), os.environ.get('PROGRAMFILES', ''), os.environ.get('LOCALAPPDATA', '')]:
            executable = Path(root) / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe'
            if executable.exists():
                subprocess.Popen([str(executable), url], creationflags=subprocess.CREATE_NO_WINDOW)
                return
    webbrowser.open(url)


def existing_app(port):
    from newsroom.server import APP_ID
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=1) as response:
            return json.load(response).get('app') == APP_ID
    except (OSError, ValueError, urllib.error.URLError):
        return False


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='中文新闻标题分类系统 · Codex 版')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--no-install', action='store_true')
    parser.add_argument('--setup-only', action='store_true')
    parser.add_argument('--retrain', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('端口必须为1到65535')
    if not (3, 11) <= sys.version_info[:2] <= (3, 13):
        raise ValueError('请使用 Python 3.11到3.13，推荐3.13')
    delegated = choose_environment(args.no_install)
    if delegated is not None:
        return delegated
    from newsroom.data import verify_raw
    from newsroom.ml import ModelService, code_signature, environment
    from newsroom.server import create_server
    from newsroom.store import Store
    from newsroom.news_store import NewsStore
    from newsroom.live_news import LiveNewsService
    log(f'独立项目：{ROOT}')
    ok, detail = verify_raw(ROOT / 'data' / 'raw')
    if not ok:
        log(detail + '，正在恢复公开数据')
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'prepare_data.py')], check=True)
    try:
        service = ModelService(ROOT / 'artifacts')
        stale = service.report.get('code_signature') != code_signature() or service.report.get('environment') != environment()
    except (OSError, ValueError, KeyError, TypeError, ImportError):
        stale = True
    if args.retrain or stale:
        log('首次准备或模型已过期，正在训练三种算法；通常约1至3分钟')
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'train.py')], check=True)
        service = ModelService(ROOT / 'artifacts')
    log('数据与模型已校验；推荐算法：' + service.report['recommended_model'])
    if args.setup_only:
        return 0
    url = f'http://127.0.0.1:{args.port}'
    if existing_app(args.port):
        log('已有本项目服务运行：' + url)
        if not args.no_browser:
            open_edge(url)
        return 0
    try:
        live = LiveNewsService(NewsStore(ROOT / 'runtime' / 'news.sqlite3'), service)
        server = create_server(args.port, service, Store(ROOT / 'runtime' / 'history.sqlite3'), live=live)
    except OSError as error:
        raise ValueError(f'端口{args.port}被占用，请用 --port 8511 更换') from error
    log('打开 ' + url + '；按 Ctrl+C 退出')
    live.start()
    log('新闻订阅每两分钟检查更新；自动分类使用本地模型')
    if not args.no_browser:
        threading.Timer(.5, open_edge, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log('服务已停止')
    finally:
        live.stop()
        server.server_close()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, subprocess.CalledProcessError) as error:
        print('[启动失败]', error, file=sys.stderr)
        sys.exit(1)
