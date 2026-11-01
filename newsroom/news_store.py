"""Independent news cache; bookmarks and human labels survive feed refreshes."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from newsroom.data import CATEGORIES
from newsroom.feeds import BUILTIN_SOURCES, canonical_article_url


def utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.astimezone(timezone.utc).isoformat()


class NewsStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS news_sources (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
                site_url TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1, builtin INTEGER NOT NULL DEFAULT 0,
                last_checked_at TEXT, last_success_at TEXT, latest_published_at TEXT,
                last_error TEXT NOT NULL DEFAULT '', item_count INTEGER NOT NULL DEFAULT 0)''')
            db.execute('''CREATE TABLE IF NOT EXISTS news_articles (
                id TEXT PRIMARY KEY, url TEXT NOT NULL UNIQUE, source_id TEXT NOT NULL,
                title TEXT NOT NULL, summary TEXT NOT NULL, published_at TEXT,
                first_seen_at TEXT NOT NULL, fetched_at TEXT NOT NULL, result TEXT NOT NULL,
                saved INTEGER NOT NULL DEFAULT 0, correction TEXT NOT NULL DEFAULT '')''')
            db.execute('CREATE INDEX IF NOT EXISTS news_order ON news_articles(published_at, first_seen_at)')
            for source in BUILTIN_SOURCES:
                db.execute('''INSERT OR IGNORE INTO news_sources(id,name,url,site_url,description,enabled,builtin)
                              VALUES(?,?,?,?,?,?,1)''',
                           (source['id'], source['name'], source['url'], source['site_url'],
                            source['description'], int(source['enabled'])))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def sources(self, now=None):
        now = now or utcnow()
        with self.connect() as db:
            rows = [dict(row) for row in db.execute('SELECT * FROM news_sources ORDER BY builtin DESC, rowid')]
        for row in rows:
            row['enabled'], row['builtin'] = bool(row['enabled']), bool(row['builtin'])
            latest = datetime.fromisoformat(row['latest_published_at']) if row['latest_published_at'] else None
            row['fresh'] = bool(latest and timedelta(minutes=-15) <= now - latest <= timedelta(hours=48))
            row['status'] = ('disabled' if not row['enabled'] else 'error' if row['last_error']
                             else 'pending' if not row['last_checked_at'] else 'empty' if not row['item_count']
                             else 'fresh' if row['fresh'] else 'stale' if latest else 'unknown')
        return rows

    def set_enabled(self, source_id, enabled):
        if not isinstance(source_id, str) or not isinstance(enabled, bool):
            raise ValueError('新闻源设置格式错误')
        with self.connect() as db:
            if db.execute('UPDATE news_sources SET enabled=? WHERE id=?', (int(enabled), source_id)).rowcount != 1:
                raise ValueError('找不到这个新闻源')

    def add_source(self, name, url):
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 40:
            raise ValueError('来源名称需要 1 至 40 个字')
        source_id = 'custom-' + hashlib.sha256(url.encode()).hexdigest()[:16]
        from urllib.parse import urlsplit
        parts = urlsplit(url)
        try:
            with self.connect() as db:
                db.execute('INSERT INTO news_sources(id,name,url,site_url) VALUES(?,?,?,?)',
                           (source_id, name.strip(), url, f'{parts.scheme}://{parts.netloc}'))
        except sqlite3.IntegrityError as error:
            raise ValueError('这个订阅地址已经添加过了') from error
        return source_id

    def finish_source(self, source_id, now, latest=None, count=0, error=''):
        with self.connect() as db:
            if error:
                db.execute('UPDATE news_sources SET last_checked_at=?,last_error=? WHERE id=?',
                           (_iso(now), error[:180], source_id))
            else:
                db.execute('''UPDATE news_sources SET last_checked_at=?,last_success_at=?,
                              latest_published_at=?,item_count=?,last_error='' WHERE id=?''',
                           (_iso(now), _iso(now), latest, count, source_id))

    def ingest(self, source_id, items, predictions, now=None):
        now = now or utcnow()
        if len(items) != len(predictions):
            raise ValueError('新闻与分类结果数量不一致')
        inserted = 0
        with self.connect() as db:
            for item, result in zip(items, predictions):
                url = canonical_article_url(item['url'])
                if not url:
                    continue
                item_id = hashlib.sha256(url.encode()).hexdigest()[:32]
                exists = db.execute('SELECT 1 FROM news_articles WHERE id=?', (item_id,)).fetchone()
                inserted += int(not exists)
                db.execute('''INSERT INTO news_articles(id,url,source_id,title,summary,published_at,first_seen_at,fetched_at,result)
                    VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,summary=excluded.summary,published_at=excluded.published_at,
                    fetched_at=excluded.fetched_at,result=excluded.result''',
                           (item_id, url, source_id, item['title'], item.get('summary', ''),
                            item.get('published_at'), _iso(now), _iso(now),
                            json.dumps(result, ensure_ascii=False, allow_nan=False)))
        return inserted

    @staticmethod
    def _row(record):
        row = dict(record)
        row['result'] = json.loads(row['result'])
        row['saved'] = bool(row['saved'])
        corrected = row['correction'] in CATEGORIES
        row['category'] = row['correction'] if corrected else row['result'].get('prediction', '')
        row['needs_review'] = row['correction'] == '待核对' or not corrected and row['result']['status'] != 'ok'
        row['human_labeled'] = bool(row['correction'])
        row['score'] = row['result'].get('score')
        return row

    def get(self, item_id):
        if not isinstance(item_id, str) or len(item_id) != 32:
            raise ValueError('新闻编号无效')
        with self.connect() as db:
            record = db.execute('''SELECT a.*,s.name source_name FROM news_articles a
                                   JOIN news_sources s ON a.source_id=s.id WHERE a.id=?''', (item_id,)).fetchone()
        if record is None:
            raise ValueError('这条新闻已不存在，请刷新列表')
        return self._row(record)

    def bookmark(self, item_id, saved):
        self.get(item_id)
        if not isinstance(saved, bool):
            raise ValueError('收藏设置格式错误')
        with self.connect() as db:
            db.execute('UPDATE news_articles SET saved=? WHERE id=?', (int(saved), item_id))

    def feedback(self, item_id, category):
        self.get(item_id)
        if not isinstance(category, str) or category not in [*CATEGORIES, '待核对']:
            raise ValueError('请选择五类新闻或待核对')
        with self.connect() as db:
            db.execute('UPDATE news_articles SET correction=? WHERE id=?', (category, item_id))

    def prune(self, now=None):
        now = now or utcnow()
        with self.connect() as db:
            db.execute('DELETE FROM news_articles WHERE saved=0 AND first_seen_at<?', (_iso(now - timedelta(days=7)),))

    def query(self, q='', category='', source='', saved=False, review=False, now=None, hours=72, limit=50, offset=0):
        now = now or utcnow()
        if (not isinstance(q, str) or len(q) > 200 or category not in ['', *CATEGORIES]
                or not isinstance(source, str) or len(source) > 80 or not isinstance(saved, bool)
                or not isinstance(review, bool) or not isinstance(limit, int) or not 1 <= limit <= 5000
                or not isinstance(offset, int) or not 0 <= offset <= 100000):
            raise ValueError('新闻筛选条件格式错误')
        where, values = [], []
        if not saved:
            where.append('(a.published_at>=? OR (a.published_at IS NULL AND a.first_seen_at>=?))')
            cutoff = _iso(now - timedelta(hours=hours))
            values.extend([cutoff, cutoff])
        if source:
            where.append('a.source_id=?')
            values.append(source)
        if saved:
            where.append('a.saved=1')
        if q.strip():
            where.append('(instr(lower(a.title),lower(?))>0 OR instr(lower(a.summary),lower(?))>0)')
            values.extend([q.strip(), q.strip()])
        condition = ' WHERE ' + ' AND '.join(where) if where else ''
        with self.connect() as db:
            records = db.execute('''SELECT a.*,s.name source_name FROM news_articles a
                                    JOIN news_sources s ON a.source_id=s.id''' + condition +
                                 ' ORDER BY COALESCE(a.published_at,a.first_seen_at) DESC,a.id DESC', values)
            rows = [self._row(row) for row in records]
        rows = [row for row in rows if (not category or row['category'] == category) and (not review or row['needs_review'])]
        return {'rows': rows[offset:offset + limit], 'total': len(rows)}

    def stats(self, now=None):
        cutoff = _iso((now or utcnow()) - timedelta(hours=72))
        total, review, counts = 0, 0, {category: 0 for category in CATEGORIES}
        with self.connect() as db:
            saved = db.execute('SELECT COUNT(*) FROM news_articles WHERE saved=1').fetchone()[0]
            records = db.execute('''SELECT result,correction FROM news_articles
                                    WHERE published_at>=? OR (published_at IS NULL AND first_seen_at>=?)''',
                                 (cutoff, cutoff))
            for row in records:
                result = json.loads(row['result'])
                corrected = row['correction'] in CATEGORIES
                category = row['correction'] if corrected else result.get('prediction', '')
                total += 1
                review += int(row['correction'] == '待核对' or not corrected and result['status'] != 'ok')
                if category in counts:
                    counts[category] += 1
        return {'total': total, 'saved': saved, 'review': review, 'categories': counts}
