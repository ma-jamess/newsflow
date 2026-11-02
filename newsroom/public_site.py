"""Publish a public, classified news snapshot without reading personal runtime."""
import json
import re
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from newsroom.data import title_error
from newsroom.feed_catalog import MAX_SOURCES
from newsroom.feeds import fetch_feed, is_recent_article
from newsroom.live_news import LiveNewsService
from newsroom.news_store import NewsStore

ROOT = Path(__file__).resolve().parents[1]


def article_link(value):
    if not isinstance(value, str) or len(value) > 4096 or re.search(r'[\x00-\x20\x7f]', value):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in {'http', 'https'} and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def build_snapshot(classifier, fetcher=fetch_feed, previous=None, now=None):
    now = now or datetime.now(timezone.utc)
    previous = previous if isinstance(previous, dict) and previous.get('schema_version') == 1 else {}
    with tempfile.TemporaryDirectory(prefix='newsflow-public-') as folder:
        store = NewsStore(Path(folder) / 'news.sqlite3')
        sources = {source['id']: source for source in store.sources(now) if source['enabled']}
        valid = []
        prior_rows = previous.get('rows')
        for row in (prior_rows if isinstance(prior_rows, list) else [])[:1000]:
            if not isinstance(row, dict) or row.get('source_id') not in sources:
                continue
            title = row.get('title')
            published = timestamp(row.get('published_at'))
            first_seen = timestamp(row.get('first_seen_at')) or now
            if not isinstance(title, str) or len(title) > 500 or title_error(title[:200]) or not article_link(row.get('url')):
                continue
            if (published or first_seen) < now - timedelta(days=7) or (published or first_seen) > now + timedelta(minutes=15):
                continue
            if not is_recent_article(row, now):
                continue
            valid.append({'source_id':row['source_id'], 'title':title, 'url':row['url'],
                          'summary':str(row.get('summary', ''))[:400],
                          'published_at':published.isoformat() if published else None,
                          'first_seen_at':first_seen.isoformat()})
        predictions = classifier.predict([row['title'][:200] for row in valid], threshold=.65) if valid else []
        for row, result in zip(valid, predictions):
            store.ingest(row['source_id'], [row], [result], timestamp(row['first_seen_at']))
        prior_sources = previous.get('sources')
        for source in (prior_sources if isinstance(prior_sources, list) else [])[:MAX_SOURCES]:
            if isinstance(source, dict) and source.get('id') in sources:
                success = timestamp(source.get('last_success_at'))
                latest = timestamp(source.get('latest_published_at'))
                if success and success <= now:
                    try:
                        count = max(0, min(80, int(source.get('item_count', 0))))
                    except (ValueError, TypeError, OverflowError):
                        count = 0
                    store.finish_source(source['id'], success, latest=latest.isoformat() if latest else None,
                                        count=count)
        live = LiveNewsService(store, classifier, fetcher=fetcher, clock=lambda: now)
        live.refresh()
        snapshot = live.snapshot(limit=1000, hours=168)
        if snapshot['total'] > 1000:
            # Reserve recent articles per source before filling by overall recency.
            # Query each source so a quiet feed survives even beyond the global cap.
            per_source = min(10, max(1, 1000 // len(sources)))
            retained = {}
            for source_id in sources:
                for row in store.query(source=source_id, now=now, hours=168, limit=per_source)['rows']:
                    retained[row['id']] = row
            for row in snapshot['rows']:
                if len(retained) >= 1000:
                    break
                retained.setdefault(row['id'], row)
            snapshot['rows'] = sorted(retained.values(), key=lambda row:
                                      (timestamp(row['published_at'] or row['first_seen_at']), row['id']), reverse=True)
        if not snapshot['rows']:
            raise ValueError('没有可发布的新闻，保留上一次部署')
        if not snapshot['update']['last_success_at']:
            prior_update = previous.get('update')
            prior_success = timestamp(prior_update.get('last_success_at')) if isinstance(prior_update, dict) else None
            if prior_success and prior_success <= now:
                snapshot['update']['last_success_at'] = prior_success.isoformat()
        explanations = classifier.predict([row['title'][:200] for row in snapshot['rows']], threshold=.65, explain=True)
        for row, explanation in zip(snapshot['rows'], explanations):
            row['summary'] = row['summary'][:400]
            row['saved'], row['correction'], row['human_labeled'] = False, '', False
            explanation.pop('elapsed_ms', None)
            row['result'].pop('elapsed_ms', None)
            row['explanation'] = explanation
        snapshot.update(schema_version=1, generated_at=now.isoformat(), interval_seconds=300,
                        sources=store.sources(now))
        snapshot['sources'] = [source for source in snapshot['sources'] if source['id'] in sources]
        return snapshot


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def write_site(output, snapshot, report, repository):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('仓库名称无效')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'web'
    page = re.search(r'<section id="page-news"(?=[ >]).*?</section>', (source / 'index.html').read_text(encoding='utf-8'), re.S)
    if not page:
        raise ValueError('新闻页模板缺失')
    repo_url = 'https://github.com/' + repository
    html = (source / 'public/index.html').read_text(encoding='utf-8').replace('{{NEWS_PAGE}}', page.group())
    html = html.replace('{{REPO_URL}}', repo_url).replace('每 2 分钟', '约每 5 分钟')
    (output / 'index.html').write_text(html, encoding='utf-8')
    for name in ['style.css','polish.css','newsflow.css','public.css','public-backend.js','public-app.js','live-news-ui.js','live-news.js']:
        shutil.copyfile(source / name, output / name)
    (output / 'icons').mkdir(exist_ok=True)
    for icon in (source / 'icons').glob('*.svg'):
        shutil.copyfile(icon, output / 'icons' / icon.name)
    shutil.copyfile(ROOT / 'LICENSE', output / 'LICENSE')
    shutil.copyfile(ROOT / 'data/raw/LICENSE', output / 'DATA_LICENSE')
    shutil.copyfile(ROOT / 'third_party/lucide/LICENSE', output / 'icons/LICENSE')
    (output / '.nojekyll').write_text('', encoding='utf-8')
    payload = {**snapshot, 'repository':repository, 'source_url':repo_url,
               'download_url':repo_url + '/archive/refs/heads/main.zip'}
    write_json(output / 'data/news.json', payload)
    write_json(output / 'data/report.json', report)
    return output
