"""Build GitHub Pages output using only public data and local models."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from newsroom.feeds import fetch_feed, validate_feed_url
from newsroom.ml import ModelService
from newsroom.public_site import build_snapshot, write_site, write_json


def load_previous_snapshot(url):
    # Public JSON holds up to 1,000 explained articles; RSS retains its 1 MiB budget.
    return json.loads(fetch_feed(validate_feed_url(url), max_bytes=8 * 1024 * 1024))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='site')
    parser.add_argument('--repository', default='ma-jamess/newsflow')
    parser.add_argument('--previous-url')
    parser.add_argument('--save-seed', action='store_true')
    args = parser.parse_args()
    previous = None
    if args.previous_url:
        try:
            previous = load_previous_snapshot(args.previous_url)
        except Exception:
            print('Previous published snapshot unavailable; using public seed if present.')
    seed = ROOT / 'public_data/news-seed.json'
    if previous is None and seed.exists():
        previous = json.loads(seed.read_text(encoding='utf-8'))
    classifier = ModelService(ROOT / 'artifacts')
    snapshot = build_snapshot(classifier, previous=previous)
    output = write_site(Path(args.output), snapshot, classifier.report, args.repository)
    if args.save_seed:
        write_json(seed, snapshot)
    print(json.dumps({'output':str(output.resolve()), 'news':len(snapshot['rows']),
                      'status':snapshot['update']['status'], 'sources':len(snapshot['sources'])}))


if __name__ == '__main__':
    main()
