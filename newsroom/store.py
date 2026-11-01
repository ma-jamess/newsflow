"""本项目自己的 SQLite 历史；纠错不自动更改训练数据或模型。"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from newsroom.data import CATEGORIES


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                title TEXT NOT NULL, prediction TEXT NOT NULL, score REAL,
                status TEXT NOT NULL, model TEXT NOT NULL, correction TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '')''')
            columns = {row['name'] for row in db.execute('PRAGMA table_info(history)')}
            for name in ['provider_model', 'reason', 'category']:
                if name not in columns:
                    db.execute(f"ALTER TABLE history ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def add(self, result):
        with self.connect() as db:
            cursor = db.execute('INSERT INTO history(created_at,title,prediction,score,status,model,provider_model,reason,category) VALUES(?,?,?,?,?,?,?,?,?)',
                                (datetime.now(timezone.utc).isoformat(), result['title'], result['prediction'],
                                 result['score'], result['status'], result['model'],
                                 result.get('provider_model', ''), result.get('reason', ''), result.get('category', '')))
            return cursor.lastrowid

    def feedback(self, index, correction, note):
        if correction not in CATEGORIES or not isinstance(note, str) or len(note) > 500:
            raise ValueError('请选择五类中的正确类别，备注最多500字')
        if not isinstance(index, int) or isinstance(index, bool):
            raise ValueError('记录编号错误')
        with self.connect() as db:
            cursor = db.execute('UPDATE history SET correction=?, note=? WHERE id=?', (correction, note, index))
            if cursor.rowcount != 1:
                raise ValueError('找不到该条历史记录')

    def history(self, limit=1000):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM history ORDER BY id DESC LIMIT ?', (limit,))]

    def counts(self):
        with self.connect() as db:
            row = db.execute("SELECT COUNT(*) total, SUM(correction != '') corrected FROM history").fetchone()
            return {'total': row['total'], 'corrected': row['corrected'] or 0}
