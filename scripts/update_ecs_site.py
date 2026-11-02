"""One public-news update for the ECS systemd timer; no private runtime is read."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from newsroom.ecs_site import bootstrap_site, refresh_site
from newsroom.ml import ModelService


def main():
    parser = argparse.ArgumentParser(description='Initialize or update the fixed NewsFlow ECS site')
    parser.add_argument('--site', type=Path, default=Path('/var/lib/newsflow/site'))
    parser.add_argument('--seed', type=Path, default=ROOT / 'public_data/news-seed.json')
    parser.add_argument('--repository', default='ma-jamess/newsflow')
    parser.add_argument('--interval-seconds', type=int, default=120)
    parser.add_argument('--bootstrap', action='store_true', help='Install public assets from a clean seed before enabling the timer')
    args = parser.parse_args()
    classifier = ModelService(ROOT / 'artifacts')
    options = dict(seed_path=args.seed, repository=args.repository, interval_seconds=args.interval_seconds)
    if args.bootstrap:
        output = bootstrap_site(args.site, classifier, **options)
        print(json.dumps({'output': str(output.resolve()), 'initialized': True,
                          'interval_seconds': args.interval_seconds}, ensure_ascii=False))
    else:
        snapshot = refresh_site(args.site, classifier, **options)
        print(json.dumps({'output': str(args.site.resolve()), 'news': len(snapshot['rows']),
                          'sources': len(snapshot['sources']), 'status': snapshot['update']['status'],
                          'generated_at': snapshot['generated_at'], 'interval_seconds': snapshot['interval_seconds']},
                         ensure_ascii=False))


if __name__ == '__main__':
    main()
