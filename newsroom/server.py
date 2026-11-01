"""仅本机访问的 HTTP 服务，前端和 JSON 接口共享同源。"""
import base64
import binascii
import csv
import json
import logging
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from newsroom import VERSION
from newsroom.csvio import MAX_ROWS, export_csv, parse_csv
from newsroom.data import CATEGORIES, title_error
from newsroom.deepseek import DeepSeekError, DeepSeekService, MODEL_NAME
from newsroom.ml import MODEL_NAMES, metrics

ROOT = Path(__file__).resolve().parents[1]
APP_ID = 'codex-news-title-classifier'
STATIC = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/deepseek-ui.js': ('deepseek-ui.js', 'text/javascript; charset=utf-8'),
          '/improvements.js': ('improvements.js', 'text/javascript; charset=utf-8'),
          '/ui-data.js': ('ui-data.js', 'text/javascript; charset=utf-8'),
          '/workspace.js': ('workspace.js', 'text/javascript; charset=utf-8'),
          '/live-news-ui.js': ('live-news-ui.js', 'text/javascript; charset=utf-8'),
          '/live-news.js': ('live-news.js', 'text/javascript; charset=utf-8'),
          '/newsflow.css': ('newsflow.css', 'text/css; charset=utf-8'),
          '/polish.css': ('polish.css', 'text/css; charset=utf-8'),
          **{f'/icons/{name}.svg': (f'icons/{name}.svg', 'image/svg+xml')
             for name in ['newspaper', 'layers', 'chart-column', 'history', 'workflow']},
          '/style.css': ('style.css', 'text/css; charset=utf-8')}


def batch_source(payload):
    """预览和分类使用同一输入解析，避免两条路径计数不一致。"""
    if 'file' in payload:
        try:
            content = base64.b64decode(payload['file'], validate=True)
        except (ValueError, TypeError, binascii.Error) as error:
            raise ValueError('CSV 内容无法读取') from error
        return parse_csv(content)
    titles = payload.get('titles')
    if not isinstance(titles, list) or not 1 <= len(titles) <= MAX_ROWS or not all(isinstance(t, str) for t in titles):
        raise ValueError('请提交1到5000条文本标题')
    return [{'title': title} for title in titles]


def news_filters(payload, export=False):
    def flag(name):
        value = payload.get(name, False)
        if isinstance(value, bool):
            return value
        if value in {'0', '1', ''}:
            return value == '1'
        raise ValueError('新闻筛选条件格式错误')

    try:
        limit = MAX_ROWS if export else int(payload.get('limit', 50))
        offset = 0 if export else int(payload.get('offset', 0))
    except (ValueError, TypeError) as error:
        raise ValueError('分页参数格式错误') from error
    if not export and not 1 <= limit <= 100:
        raise ValueError('每页应为 1 至 100 条')
    return {'q': payload.get('q', ''), 'category': payload.get('category', ''),
            'source': payload.get('source', ''), 'saved': flag('saved'), 'review': flag('review'),
            'limit': limit, 'offset': offset}


def create_server(port, service, store, artifacts=None, deepseek=None, live=None):
    token = secrets.token_urlsafe(32)
    artifacts = Path(artifacts) if artifacts is not None else ROOT / 'artifacts'
    deepseek = deepseek if deepseek is not None else DeepSeekService()

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(30)

        def log_message(self, format, *args):
            logging.info(format, *args)

        @property
        def origin(self):
            return f'http://127.0.0.1:{self.server.server_port}'

        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def respond(self, data, status=200, kind='application/json; charset=utf-8', download=False):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if download:
                self.send_header('Content-Disposition', 'attachment; filename="news-results.csv"')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.valid_host():
                return self.respond({'error': '只允许本机标准地址访问'}, 403)
            path = urlsplit(self.path).path
            if path == '/api/health':
                return self.respond({'app': APP_ID, 'version': VERSION, 'ready': True})
            if path == '/api/bootstrap':
                return self.respond({'token': token, 'report': service.report, 'categories': CATEGORIES,
                                     'model_names': {**MODEL_NAMES, 'deepseek': MODEL_NAME},
                                     'deepseek': deepseek.metadata(), 'stats': store.counts(), 'version': VERSION,
                                     'live_news': {'enabled': live is not None, 'interval_seconds': 120}})
            if path == '/api/history':
                return self.respond({'rows': store.history(), 'stats': store.counts()})
            if path in {'/api/news', '/api/news/sources', '/api/news/detail'}:
                if live is None:
                    return self.respond({'error': '实时新闻未启用，请用 python run.py 启动新版'}, 503)
                try:
                    query = {key: values[0] for key, values in parse_qs(urlsplit(self.path).query, keep_blank_values=True).items()}
                    if path == '/api/news':
                        return self.respond(live.snapshot(**news_filters(query)))
                    if path == '/api/news/sources':
                        return self.respond({'sources': live.store.sources(live.clock()), 'interval_seconds': 120})
                    return self.respond(live.detail(query.get('id')))
                except (ValueError, TypeError, KeyError) as error:
                    return self.respond({'error': str(error)}, 400)
            if path in STATIC:
                name, kind = STATIC[path]
                return self.respond((ROOT / 'web' / name).read_bytes(), kind=kind)
            return self.respond({'error': '没有这个页面'}, 404)

        def do_POST(self):
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 8 * 1024 * 1024:
                    return self.respond({'error': '请求体为空或超过8 MB'}, 413)
                # Consume bounded input before replying: unread POST bytes can
                # reset the connection on Windows and discard the error response.
                body = self.rfile.read(length)
                if not self.valid_host() or self.headers.get('Origin', self.origin) != self.origin:
                    return self.respond({'error': '跨来源请求被拒绝'}, 403)
                if not secrets.compare_digest(self.headers.get('X-Request-Token', ''), token):
                    return self.respond({'error': '请刷新页面后重试'}, 403)
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    return self.respond({'error': '请使用 JSON 请求'}, 415)
                payload = json.loads(body)
                if not isinstance(payload, dict):
                    raise ValueError('请求应为 JSON 对象')
                model = payload.get('model')
                threshold = payload.get('threshold', .65)
                path = urlsplit(self.path).path
                if path.startswith('/api/news/'):
                    if live is None:
                        return self.respond({'error': '实时新闻未启用，请重新启动新版'}, 503)
                    if path == '/api/news/refresh':
                        return self.respond(live.request_refresh())
                    if path == '/api/news/save':
                        live.store.bookmark(payload.get('id'), payload.get('saved'))
                        return self.respond({'saved': True, 'row': live.store.get(payload.get('id')),
                                             'stats': live.store.stats(live.clock())})
                    if path == '/api/news/feedback':
                        live.store.feedback(payload.get('id'), payload.get('category'))
                        return self.respond({'saved': True, 'row': live.store.get(payload.get('id')),
                                             'stats': live.store.stats(live.clock())})
                    if path == '/api/news/sources':
                        if 'id' in payload:
                            live.store.set_enabled(payload['id'], payload.get('enabled'))
                            added = payload['id']
                        else:
                            from newsroom.feeds import validate_feed_url
                            added = live.store.add_source(payload.get('name'), validate_feed_url(payload.get('url')))
                        update = live.request_refresh()
                        return self.respond({'id': added, 'sources': live.store.sources(live.clock()), 'update': update})
                    if path == '/api/news/export':
                        rows = live.snapshot(**news_filters(payload, export=True))['rows']
                        flat = [{'title': row['title'], 'category': row['category'],
                                 'needs_review': row['needs_review'], 'human_labeled': row['human_labeled'],
                                 'model_prediction': row['result'].get('prediction', ''),
                                 'model_score': row['score'], 'source_name': row['source_name'],
                                 'url': row['url'], 'published_at': row['published_at'],
                                 'fetched_at': row['fetched_at'], 'saved': row['saved']} for row in rows]
                        return self.respond(export_csv(flat), kind='text/csv; charset=utf-8', download=True)
                    return self.respond({'error': '没有这个新闻接口'}, 404)
                if path == '/api/preview':
                    source = batch_source(payload)
                    invalid = sum(bool(title_error(row['title'])) for row in source)
                    preview = [{**row, 'message': title_error(row['title']) or '可分类'} for row in source[:10]]
                    return self.respond({'total': len(source), 'invalid_count': invalid, 'rows': preview})
                if path == '/api/compare':
                    title = payload.get('title')
                    error = title_error(title)
                    if error:
                        raise ValueError(error)
                    rows = [service.predict([title], kind, threshold)[0] for kind in MODEL_NAMES]
                    predictions = {row['prediction'] for row in rows if row['prediction']}
                    return self.respond({'title': title, 'rows': rows, 'agreement': len(predictions) == 1 and all(row['prediction'] for row in rows),
                                         'recommended_model': service.report['recommended_model']})
                if path == '/api/errors':
                    kind = model or service.report['recommended_model']
                    if not isinstance(kind, str) or kind not in MODEL_NAMES:
                        raise ValueError('不支持的模型')
                    try:
                        with (artifacts / f'{kind}_test_predictions.csv').open(encoding='utf-8-sig', newline='') as source:
                            errors = [row for row in csv.DictReader(source) if row['label'] != row['prediction']]
                    except (OSError, KeyError, csv.Error) as error:
                        raise ValueError('完整测试预测文件缺失或格式错误，请重新训练恢复') from error
                    return self.respond(export_csv(errors), kind='text/csv; charset=utf-8', download=True)
                if path == '/api/predict':
                    title = payload.get('title')
                    if not isinstance(title, str):
                        raise ValueError('标题必须是文本')
                    result = (deepseek.predict(title) if model == 'deepseek'
                              else service.predict([title], model, threshold, explain=True)[0])
                    if result['status'] == 'invalid':
                        raise ValueError(result['message'])
                    result['id'] = store.add(result)
                    return self.respond({'result': result, 'stats': store.counts()})
                if path == '/api/batch':
                    if model == 'deepseek':
                        raise ValueError('DeepSeek 目前用于单条分类；批量处理请选择本地算法')
                    source = batch_source(payload)
                    results = service.predict([r['title'] for r in source], model, threshold)
                    labeled = []
                    for original, result in zip(source, results):
                        if 'label' in original:
                            result['label'] = original['label']
                            if original['label'] in CATEGORIES and result['prediction']:
                                labeled.append(result)
                    evaluation = metrics([r['label'] for r in labeled], [r['prediction'] for r in labeled]) if labeled else None
                    return self.respond({'rows': results, 'evaluation': evaluation, 'labeled_count': len(labeled),
                                         'counts': {status: sum(r['status'] == status for r in results) for status in ['ok', 'review', 'invalid', 'unknown']}})
                if path == '/api/feedback':
                    store.feedback(payload.get('id'), payload.get('correction'), payload.get('note', ''))
                    return self.respond({'saved': True, 'stats': store.counts()})
                if path == '/api/export':
                    rows = store.history(5000) if payload.get('history') else payload.get('rows')
                    if not isinstance(rows, list) or len(rows) > MAX_ROWS or not all(isinstance(r, dict) for r in rows):
                        raise ValueError('导出数据错误')
                    columns = ['id', 'title', 'label', 'prediction', 'score', 'status', 'message', 'model',
                               'provider_model', 'category', 'reason', 'correction', 'note', 'created_at']
                    flat = [{k: r[k] for k in columns if k in r and isinstance(r[k], (str, int, float, type(None)))} for r in rows]
                    return self.respond(export_csv(flat), kind='text/csv; charset=utf-8', download=True)
                return self.respond({'error': '没有这个接口'}, 404)
            except DeepSeekError as error:
                return self.respond({'error': str(error)}, error.status)
            except (ValueError, TypeError, KeyError) as error:
                return self.respond({'error': str(error)}, 400)
            except Exception:
                logging.exception('request failed')
                return self.respond({'error': '处理失败，请查看运行窗口并重试'}, 500)

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server
