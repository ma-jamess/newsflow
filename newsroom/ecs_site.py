"""Initialize a public ECS site, then atomically publish only its news JSON."""
import copy
import json
import math
import os
import re
import tempfile
from pathlib import Path

from newsroom.data import CATEGORIES
from newsroom.feed_catalog import MAX_SOURCES
from newsroom.feeds import fetch_feed
from newsroom.public_site import ROOT, article_link, build_snapshot, public_payload, timestamp, write_site

MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
DEFAULT_SEED = ROOT / 'public_data/news-seed.json'


def read_public_snapshot(path):
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
        if len(raw) > MAX_SNAPSHOT_BYTES:
            return None
        data = json.loads(raw)
        if (not isinstance(data, dict) or data.get('schema_version') != 1
                or not isinstance(data.get('rows'), list) or not 1 <= len(data['rows']) <= 1000
                or not isinstance(data.get('sources'), list) or not 1 <= len(data['sources']) <= MAX_SOURCES
                or not isinstance(data.get('update'), dict) or timestamp(data.get('generated_at')) is None):
            return None
        source_ids = set()
        source_states = ('fresh', 'stale', 'empty', 'error', 'disabled', 'pending', 'unknown')
        for source in data['sources']:
            if (not isinstance(source, dict) or not isinstance(source.get('id'), str)
                    or not re.fullmatch(r'[A-Za-z0-9-]{1,80}', source['id'])
                    or source['id'] in source_ids or not isinstance(source.get('name'), str)
                    or not article_link(source.get('url')) or source.get('status') not in source_states):
                return None
            source_ids.add(source['id'])
        for row in data['rows']:
            if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                    or not re.fullmatch(r'[a-f0-9]{32}', row['id'])
                    or not isinstance(row.get('source_id'), str) or row['source_id'] not in source_ids
                    or not isinstance(row.get('title'), str) or not 1 <= len(row['title']) <= 500
                    or not article_link(row.get('url')) or not isinstance(row.get('result'), dict)):
                return None
            result = row['result']
            probabilities = result.get('probabilities', {})
            if (not isinstance(result.get('prediction'), str)
                    or result['prediction'] not in ['', *CATEGORIES] or not isinstance(probabilities, dict)):
                return None
            if any(not isinstance(value, (int, float)) or isinstance(value, bool)
                   or not 0 <= value <= 1 or not math.isfinite(value) for value in probabilities.values()):
                return None
        return data
    except (OSError, ValueError, UnicodeError):
        return None


def bootstrap_site(output, classifier, *, seed_path=DEFAULT_SEED,
                   repository='ma-jamess/newsflow', interval_seconds=120):
    output = Path(output)
    snapshot = read_public_snapshot(output / 'data/news.json') or read_public_snapshot(seed_path)
    if not snapshot or not snapshot['rows']:
        raise ValueError('没有可用于初次部署的公开快照')
    snapshot = copy.deepcopy(snapshot)
    for row in snapshot['rows']:
        if not isinstance(row, dict):
            raise ValueError('公开快照中的新闻无效')
        row.update(saved=False, correction='', human_labeled=False)
    return write_site(output, snapshot, classifier.report, repository,
                      deployment='ecs', interval_seconds=interval_seconds)


def refresh_site(output, classifier, *, seed_path=DEFAULT_SEED,
                 repository='ma-jamess/newsflow', interval_seconds=120,
                 fetcher=fetch_feed, now=None):
    output = Path(output)
    if not (output / 'index.html').is_file():
        raise ValueError('请先使用 --bootstrap 初始化站点')
    # Check configuration before doing any network or classifier work.
    public_payload({}, repository, deployment='ecs', interval_seconds=interval_seconds)
    previous = read_public_snapshot(output / 'data/news.json') or read_public_snapshot(seed_path)
    snapshot = build_snapshot(classifier, fetcher=fetcher, previous=previous, now=now)
    payload = public_payload(snapshot, repository, deployment='ecs', interval_seconds=interval_seconds)
    target = output / 'data/news.json'
    temporary = None
    try:
        # Same filesystem as the live JSON, outside the web root. A failed write
        # cannot truncate the file Nginx is serving or expose a partial snapshot.
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent,
                                         prefix='.newsflow-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            stream.flush()
            # Nginx runs as another user; mkstemp's private 0600 mode must not
            # replace a previously public, readable news file.
            os.chmod(temporary, 0o644)
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return payload
