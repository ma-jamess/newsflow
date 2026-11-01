"""Public RSS/Atom inputs. Article HTML is converted to plain text."""
import ipaddress
import re
import socket
from http.client import HTTPSConnection
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener
from xml.etree import ElementTree

MAX_FEED_BYTES = 1024 * 1024
FETCH_TIMEOUT = 10
MAX_FEED_ITEMS = 80
BUILTIN_SOURCES = [
    {'id': 'ithome', 'name': 'IT之家', 'url': 'https://www.ithome.com/rss/',
     'site_url': 'https://www.ithome.com', 'description': '科技与数码', 'enabled': True},
    {'id': 'sspai', 'name': '少数派', 'url': 'https://sspai.com/feed',
     'site_url': 'https://sspai.com', 'description': '数字生活与文化', 'enabled': True},
    {'id': 'cn-sports', 'name': '中新网 · 体育', 'url': 'https://www.chinanews.com.cn/rss/sports.xml',
     'site_url': 'https://www.chinanews.com.cn', 'description': '体育赛事', 'enabled': True},
    {'id': 'cn-finance', 'name': '中新网 · 财经', 'url': 'https://www.chinanews.com.cn/rss/finance.xml',
     'site_url': 'https://www.chinanews.com.cn', 'description': '财经与产业', 'enabled': True},
    {'id': 'cn-education', 'name': '中新网 · 教育', 'url': 'https://www.chinanews.com.cn/rss/edu.xml',
     'site_url': 'https://www.chinanews.com.cn', 'description': '学校与教育', 'enabled': True},
    {'id': 'cn-latest', 'name': '中新网 · 即时', 'url': 'https://www.chinanews.com.cn/rss/scroll-news.xml',
     'site_url': 'https://www.chinanews.com.cn', 'description': '综合资讯，五类外内容需核对', 'enabled': False},
]


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {'script', 'style'} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value, limit=400):
    parser = _Text()
    parser.feed(unescape(value or ''))
    return re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()[:limit]


def canonical_article_url(value, base=''):
    value = urljoin(base, (value or '').strip())
    if len(value) > 2048 or re.search(r'[\x00-\x20\x7f]', value):
        return ''
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {'http', 'https'} or not parts.hostname or parts.username or parts.password:
            return ''
        port = parts.port
    except ValueError:
        return ''
    host = parts.hostname.lower()
    if ':' in host:
        host = f'[{host}]'
    if port and not (parts.scheme.lower() == 'https' and port == 443 or parts.scheme.lower() == 'http' and port == 80):
        host += f':{port}'
    query = [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith('utm_') and key.lower() not in {'fbclid', 'gclid'}]
    return urlunsplit((parts.scheme.lower(), host, parts.path or '/', urlencode(query), ''))


def _public_addresses(host, port):
    answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if port != 443 or not answers or any(not ipaddress.ip_address(answer[4][0]).is_global for answer in answers):
        raise ValueError('新闻源必须使用公网 HTTPS 地址，不能是内网或本机地址')
    return answers


def _public_connection(address, timeout=FETCH_TIMEOUT, source_address=None):
    # Resolve and validate immediately before connecting; connect to the numeric
    # sockaddr itself so a second DNS lookup cannot rebind it to a private host.
    answers = _public_addresses(*address)
    last_error = None
    for family, kind, protocol, _, sockaddr in answers:
        connection = socket.socket(family, kind, protocol)
        try:
            connection.settimeout(timeout)
            if source_address:
                connection.bind(source_address)
            connection.connect(sockaddr)
            return connection
        except OSError as error:
            connection.close()
            last_error = error
    raise last_error or OSError('无法连接新闻源')


class _PublicHTTPSConnection(HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = _public_connection


class _PublicHTTPSHandler(HTTPSHandler):
    def https_open(self, req):
        # HTTPSConnection retains the original hostname for SNI/certificate checks.
        return self.do_open(_PublicHTTPSConnection, req, context=self._context)


def validate_feed_url(value):
    if not isinstance(value, str) or len(value) > 2048 or re.search(r'[\x00-\x20\x7f]', value):
        raise ValueError('请填写有效的公网 HTTPS 订阅地址')
    try:
        parts = urlsplit(value.strip())
        if (parts.scheme.lower() != 'https' or not parts.hostname or parts.username or parts.password
                or parts.port not in {None, 443}):
            raise ValueError
        host = parts.hostname.lower()
        if host == 'localhost' or host.endswith(('.localhost', '.local')):
            raise ValueError
        _public_addresses(host, 443)
    except (ValueError, OSError) as error:
        raise ValueError('新闻源必须使用公网 HTTPS 地址，不能是内网或本机地址') from error
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or '/', parts.query, ''))


class _PublicRedirect(HTTPRedirectHandler):
    max_redirections = 3
    max_repeats = 2

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, validate_feed_url(newurl))


def fetch_feed(url, *, max_bytes=MAX_FEED_BYTES):
    if not isinstance(max_bytes, int) or not 1 <= max_bytes <= 8 * 1024 * 1024:
        raise ValueError('读取容量上限无效')
    url = validate_feed_url(url)
    request = Request(url, headers={'User-Agent': 'NewsFlow/1.4 (personal RSS reader)',
                                   'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml',
                                   'Accept-Encoding': 'identity'})
    try:
        with build_opener(ProxyHandler({}), _PublicHTTPSHandler(), _PublicRedirect()).open(request, timeout=FETCH_TIMEOUT) as response:
            validate_feed_url(response.geturl())
            data = response.read(max_bytes + 1)
    except HTTPError as error:
        raise ValueError(f'来源暂时无法读取（HTTP {error.code}）') from error
    except (URLError, OSError, TimeoutError) as error:
        raise ValueError('来源连接失败或超时，可稍后刷新') from error
    if len(data) > max_bytes:
        raise ValueError(f'内容超过 {max_bytes / (1024 * 1024):g} MiB 上限')
    return data


def _date(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value.strip())
    except (ValueError, TypeError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
        except (ValueError, TypeError, OverflowError):
            return None
    if parsed.tzinfo is None:
        from datetime import timedelta
        parsed = parsed.replace(tzinfo=timezone(timedelta(hours=8)))
    return parsed.astimezone(timezone.utc).isoformat()


def _child(node, names):
    for name in names:
        for child in node:
            if child.tag.rsplit('}', 1)[-1] == name:
                return ''.join(child.itertext()).strip()
    return ''


def parse_feed(data, feed_url, now=None):
    if not isinstance(data, bytes) or len(data) > MAX_FEED_BYTES:
        raise ValueError('订阅内容格式错误或超过大小上限')
    try:
        if data.startswith((b'\xff\xfe', b'\xfe\xff')):
            text = data.decode('utf-16')
        else:
            declaration = re.search(br'encoding=["\']([^"\']+)["\']', data[:160], re.I)
            encoding = declaration.group(1).decode('ascii') if declaration else 'utf-8-sig'
            text = data.decode(encoding)
        if re.search(r'<!\s*(?:DOCTYPE|ENTITY)\b', text, re.I):
            raise ValueError('订阅不支持 DTD 或实体声明')
        root = ElementTree.fromstring(text)
    except (ElementTree.ParseError, UnicodeError, LookupError) as error:
        raise ValueError('来源返回的内容不是有效 RSS 或 Atom') from error
    kind = root.tag.rsplit('}', 1)[-1]
    if kind == 'rss':
        channel = next((child for child in root if child.tag.rsplit('}', 1)[-1] == 'channel'), None)
        if channel is None:
            raise ValueError('RSS 缺少频道')
        entries = [child for child in channel if child.tag.rsplit('}', 1)[-1] == 'item']
    elif kind in {'feed', 'RDF'}:
        entries = [child for child in root if child.tag.rsplit('}', 1)[-1] in {'entry', 'item'}]
    else:
        raise ValueError('来源返回的内容不是 RSS 或 Atom')
    result = []
    for entry in entries[:MAX_FEED_ITEMS]:
        title = plain_text(_child(entry, ['title']), 500)
        link = _child(entry, ['link'])
        if not link:
            link = next((child.get('href', '') for child in entry
                         if child.tag.rsplit('}', 1)[-1] == 'link' and child.get('rel', 'alternate') == 'alternate'), '')
        url = canonical_article_url(link, feed_url)
        if not title or not url:
            continue
        result.append({'title': title, 'url': url,
                       'summary': plain_text(_child(entry, ['description', 'summary', 'encoded', 'content'])),
                       'published_at': _date(_child(entry, ['pubDate', 'published', 'date', 'updated']))})
    return result
