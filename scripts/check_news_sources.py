"""Audit free Chinese feeds on the current network without publishing a site."""
import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from newsroom.feeds import BUILTIN_SOURCES, fetch_feed, is_recent_article, parse_feed
from newsroom.feed_catalog import MAX_SOURCES, is_public_https_url as safe_input


def audit_sources(sources, fetcher=fetch_feed, now=None):
    if not isinstance(sources, list) or len(sources) > MAX_SOURCES:
        raise ValueError('候选来源需要是最多 128 项的列表')
    now = now or datetime.now(timezone.utc)
    def check(source):
        started = time.monotonic()
        url = source.get('url')
        row = {'id':str(source.get('id', ''))[:80], 'name':str(source.get('name', ''))[:80],
               'url':'', 'available':False, 'status':'invalid', 'latest_published_at':None}
        if not safe_input(url):
            return row
        row['url'] = url
        try:
            content = fetcher(url)
            items = parse_feed(content, url, now)
            chinese = sum(bool(re.search(r'[\u3400-\u9fff]', item['title'])) for item in items)
            dates = [datetime.fromisoformat(item['published_at']) for item in items if item['published_at']]
            eligible = [item for item in items if is_recent_article(item, now)]
            recent_dated = [item for item in eligible if item['published_at']]
            undated = [item for item in items if not item['published_at']]
            eligible_undated = [item for item in eligible if not item['published_at']]
            latest = max(dates, default=None)
            status = ('empty' if not items else 'non_chinese' if chinese/max(1,len(items)) <= .6
                      else 'current' if recent_dated else 'old' if dates or not eligible_undated else 'unknown_time')
            row.update(status=status, available=status in {'current','unknown_time'}, parsed_items=len(items),
                       recent_items=len(recent_dated), undated_items=len(undated),
                       archival_items=len(undated)-len(eligible_undated), chinese_items=chinese, bytes=len(content),
                       latest_published_at=latest.isoformat() if latest else None,
                       sample_title=items[0]['title'] if items else '')
        except Exception:
            row.update(status='error', error='来源未能通过公网 HTTPS、容量或 RSS/Atom 读取检查')
        row['seconds'] = round(time.monotonic()-started, 2)
        return row
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(check, sources))
    return {'checked_at':now.isoformat(), 'checked_count':len(results),
            'available_count':sum(row['available'] for row in results), 'sources':results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help='Public candidate catalogue JSON; defaults to built-in feeds')
    parser.add_argument('--output', default='source-audit.json')
    args = parser.parse_args()
    sources = json.loads(Path(args.input).read_text(encoding='utf-8-sig')) if args.input else BUILTIN_SOURCES
    report = audit_sources(sources)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'checked':report['checked_count'], 'available':report['available_count'],
                      'output':str(destination)}))


if __name__ == '__main__':
    main()
