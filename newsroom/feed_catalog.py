"""Validated public feed catalogue; loading it does not require a network."""
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit, urlunsplit

MAX_SOURCES = 128
MAX_CATALOG_BYTES = 512 * 1024
_KEYED_PARAMETERS = {'token', 'access_token', 'api_key', 'apikey', 'key',
                     'auth', 'password', 'secret'}


def is_public_https_url(value):
    if not isinstance(value, str) or len(value) > 2048 or re.search(r'[\x00-\x20\x7f]', value):
        return False
    try:
        parts = urlsplit(value)
        if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
                or parts.port not in {None, 443} or parts.fragment):
            return False
        host = parts.hostname.lower()
        if host == 'localhost' or host.endswith(('.local', '.localhost')):
            return False
        try:
            if not ipaddress.ip_address(host).is_global:
                return False
        except ValueError:
            encoded = host.encode('idna').decode('ascii')
            if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', encoded) or '.' not in encoded:
                return False
        return not any(key.lower() in _KEYED_PARAMETERS
                       for key, _ in parse_qsl(parts.query, keep_blank_values=True))
    except (ValueError, UnicodeError):
        return False


def load_catalog(path=None):
    path = Path(path) if path is not None else Path(__file__).with_name('sources.json')
    if path.stat().st_size > MAX_CATALOG_BYTES:
        raise ValueError('来源目录超过容量上限')
    try:
        rows = json.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError, UnicodeError) as error:
        raise ValueError('来源目录不是有效 JSON') from error
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_SOURCES:
        raise ValueError('来源目录需要包含 1 至 128 个来源')
    ids, urls, result = set(), set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('来源目录条目格式错误')
        source_id = row.get('id')
        if not isinstance(source_id, str) or not re.fullmatch(r'[A-Za-z0-9-]{1,80}', source_id) or source_id in ids:
            raise ValueError('来源编号无效或重复')
        if type(row.get('enabled')) is not bool:
            raise ValueError('来源启用设置需要使用布尔值')
        for field, limit in [('name', 80), ('description', 400), ('group', 80)]:
            value = row.get(field, '')
            if not isinstance(value, str) or len(value) > limit or (field == 'name' and not value.strip()):
                raise ValueError('来源名称或说明格式错误')
        if not is_public_https_url(row.get('url')) or not is_public_https_url(row.get('site_url')):
            raise ValueError('来源需要公开 HTTPS 地址，不能含凭据或付费密钥')
        parts = urlsplit(row['url'])
        host = parts.hostname.lower()
        canonical = urlunsplit(('https', '[' + host + ']' if ':' in host else host,
                               parts.path or '/', parts.query, ''))
        if canonical in urls:
            raise ValueError('订阅地址重复')
        ids.add(source_id)
        urls.add(canonical)
        result.append({key: row[key] for key in ['id', 'name', 'url', 'site_url', 'enabled']}
                      | {'description': row.get('description', ''), 'group': row.get('group', '')})
    return result
