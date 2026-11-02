"""One refresh coordinator owns the application's periodic public feed jobs."""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from newsroom.feeds import fetch_feed, is_recent_article, parse_feed
from newsroom.news_store import utcnow

REFRESH_SECONDS = 120
MANUAL_COOLDOWN = 30


class LiveNewsService:
    def __init__(self, store, classifier, fetcher=fetch_feed, clock=utcnow):
        self.store, self.classifier = store, classifier
        self.fetcher, self.clock = fetcher, clock
        self._lock = threading.Lock()
        self._stopped = threading.Event()
        self._scheduler = None
        self._job = None
        self._update = {'refreshing': False, 'status': 'idle', 'last_started_at': None,
                        'last_finished_at': None, 'last_success_at': None, 'new_count': 0, 'errors': 0}

    def start(self):
        with self._lock:
            if self._scheduler is not None or self._stopped.is_set():
                return
            self._scheduler = threading.Thread(target=self._loop, name='newsflow-scheduler', daemon=True)
            self._scheduler.start()

    def _loop(self):
        while not self._stopped.is_set():
            self.refresh()
            self._stopped.wait(REFRESH_SECONDS)

    def _begin(self, manual=False):
        with self._lock:
            return self._begin_locked(manual)

    def _begin_locked(self, manual=False):
        now = self.clock()
        last = self._update['last_started_at']
        remaining = max(0, MANUAL_COOLDOWN - int((now - last).total_seconds())) if last else 0
        if self._stopped.is_set() or self._update['refreshing'] or manual and remaining:
            return {'started': False, 'refreshing': self._update['refreshing'], 'cooldown_seconds': remaining}
        self._update.update(refreshing=True, status='refreshing', last_started_at=now, new_count=0, errors=0)
        return {'started': True, 'refreshing': True, 'cooldown_seconds': 0}

    def request_refresh(self):
        with self._lock:
            result = self._begin_locked(manual=True)
            if result['started']:
                self._job = threading.Thread(target=self._perform_refresh, name='newsflow-update', daemon=True)
                self._job.start()
        return result

    def refresh(self):
        result = self._begin()
        if result['started']:
            self._perform_refresh()
        return result

    def _fetch_source(self, source, now):
        rows = parse_feed(self.fetcher(source['url']), source['url'], now)
        latest = max((row['published_at'] for row in rows if row['published_at']), default=None)
        recent = [row for row in rows if is_recent_article(row, now)]
        return recent, latest, len(rows)

    def _perform_refresh(self):
        now = self.clock()
        errors, succeeded, inserted = 0, 0, 0
        try:
            sources = [s for s in self.store.sources(now) if s['enabled']]
            with ThreadPoolExecutor(max_workers=3, thread_name_prefix='newsflow-feed') as pool:
                jobs = {pool.submit(self._fetch_source, source, now): source for source in sources}
                for future in as_completed(jobs):
                    source = jobs[future]
                    try:
                        rows, latest, count = future.result()
                        predictions = self.classifier.predict([row['title'][:200] for row in rows], threshold=.65)
                        inserted += self.store.ingest(source['id'], rows, predictions, now)
                        self.store.finish_source(source['id'], now, latest=latest, count=count)
                        succeeded += 1
                    except Exception:
                        # Never include upstream response bodies or credential-bearing URLs.
                        self.store.finish_source(source['id'], now, error='来源暂时无法读取，稍后刷新可重试')
                        errors += 1
            self.store.prune(now)
            with self._lock:
                self._update.update(status='partial' if errors and succeeded else 'error' if errors else 'success',
                                    new_count=inserted, errors=errors)
                if succeeded:
                    self._update['last_success_at'] = now
        finally:
            with self._lock:
                self._update.update(refreshing=False, last_finished_at=self.clock())

    def snapshot(self, **filters):
        now = self.clock()
        data = self.store.query(now=now, **filters)
        with self._lock:
            update = {key: value.isoformat() if hasattr(value, 'isoformat') else value
                      for key, value in self._update.items()}
        data.update(stats=self.store.stats(now), update=update, interval_seconds=REFRESH_SECONDS,
                    server_time=now.isoformat())
        return data

    def detail(self, item_id):
        row = self.store.get(item_id)
        row['explanation'] = self.classifier.predict([row['title'][:200]], threshold=.65, explain=True)[0]
        return row

    def stop(self):
        with self._lock:
            self._stopped.set()
            threads = [self._scheduler, self._job]
        for thread in threads:
            if thread is not None and thread is not threading.current_thread():
                thread.join()
