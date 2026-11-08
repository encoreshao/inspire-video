"""Polite, same-origin website crawl: the homepage plus the pages in its navigation."""
from __future__ import annotations

import ipaddress
import re
import socket
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit

USER_AGENT = "InspireVideoBot/0.1 (+local showcase tool)"
MAX_PAGES = 10
MAX_BYTES = 2_000_000
MAX_TEXT = 4000
SKIP_EXT = (".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".mov", ".dmg",
            ".exe", ".gz", ".xml", ".json", ".css", ".js")
HTML_TYPES = ("text/html", "application/xhtml+xml")
IGNORED_TAGS = ("script", "style", "noscript", "svg", "template")


class CrawlError(RuntimeError):
    pass


@dataclass
class Page:
    url: str
    title: str = ""
    description: str = ""
    og_image: str = ""
    headings: list = field(default_factory=list)
    text: str = ""
    nav_links: list = field(default_factory=list)       # [{"text", "url"}]


@dataclass
class FetchResult:
    url: str
    content_type: str
    body: bytes
    charset: str = ""


@dataclass
class CrawlResult:
    pages: list
    skipped: list                                         # [{"url", "reason"}]


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def is_public_host(host: str) -> bool:
    host = (host or "").strip("[]").lower()
    if not host or host == "localhost" or host.endswith((".localhost", ".local")):
        return False
    try:
        addrs = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
        except OSError:
            return False
        addrs = [ipaddress.ip_address(i[4][0].split("%")[0]) for i in infos]
    return bool(addrs) and all(a.is_global for a in addrs)


class _Extractor(HTMLParser):
    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.title = self.description = self.og_image = ""
        self.headings, self.nav_links, self.text = [], [], []
        self._in_title, self._skip, self._nav = False, 0, 0
        self._head, self._head_buf = None, []
        self._href, self._a_buf = None, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in IGNORED_TAGS:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            content = (a.get("content") or "").strip()
            if name in ("description", "og:description") and content and not self.description:
                self.description = content
            elif name == "og:image" and content and not self.og_image:
                self.og_image = urljoin(self.base, content)
        elif tag in ("nav", "header"):
            self._nav += 1
        elif tag in ("h1", "h2", "h3"):
            self._head, self._head_buf = tag, []
        elif tag == "a" and self._nav and a.get("href"):
            self._href, self._a_buf = urljoin(self.base, a["href"]), []

    def handle_endtag(self, tag):
        if tag in IGNORED_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag == "title":
            self._in_title = False
        elif tag in ("nav", "header"):
            self._nav = max(0, self._nav - 1)
        elif tag == self._head:
            text = _clean(" ".join(self._head_buf))
            if text and len(self.headings) < 12:
                self.headings.append(text[:120])
            self._head = None
        elif tag == "a" and self._href is not None:
            self.nav_links.append({"text": _clean(" ".join(self._a_buf))[:60], "url": self._href})
            self._href = None

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_title:
            self.title += data
        if self._head:
            self._head_buf.append(data)
        if self._href is not None:
            self._a_buf.append(data)
        self.text.append(data)


def parse_page(html: str, url: str) -> Page:
    x = _Extractor(url)
    x.feed(html)
    x.close()
    return Page(url=url, title=_clean(x.title)[:200], description=_clean(x.description)[:400],
                og_image=x.og_image, headings=x.headings, text=_clean(" ".join(x.text))[:MAX_TEXT],
                nav_links=x.nav_links)


def _norm(url: str) -> str:
    return urldefrag(url)[0].rstrip("/")


def _origin(url: str) -> str:
    return urlsplit(url).netloc.lower().removeprefix("www.")


def select_nav_links(page: Page, limit: int) -> list[str]:
    home, picked = _norm(page.url), []
    for link in page.nav_links:
        url = urldefrag(link["url"])[0]
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or _origin(url) != _origin(page.url):
            continue
        if parts.path.lower().endswith(SKIP_EXT) or _norm(url) == home:
            continue
        if _norm(url) not in [_norm(u) for u in picked]:
            picked.append(url)
    return picked[:max(0, limit)]


class _GuardedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, host_check):
        self.host_check = host_check

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urlsplit(newurl)
        if parts.scheme not in ("http", "https") or not self.host_check(parts.hostname or ""):
            raise CrawlError(f"refusing to follow a redirect to {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def make_fetcher(host_check=is_public_host, timeout: float = 10):
    opener = urllib.request.build_opener(_GuardedRedirect(host_check))

    def fetch(url: str) -> FetchResult:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain;q=0.5"})
        try:
            with opener.open(req, timeout=timeout) as r:
                body = r.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise CrawlError(f"larger than {MAX_BYTES // 1_000_000} MB")
                return FetchResult(r.geturl(), r.headers.get_content_type(), body,
                                   r.headers.get_content_charset() or "")
        except urllib.error.HTTPError as e:
            raise CrawlError(f"HTTP {e.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise CrawlError(str(getattr(e, "reason", e))) from None

    return fetch


def _decode(r: FetchResult) -> str:
    try:
        return r.body.decode(r.charset or "utf-8", errors="replace")
    except LookupError:
        return r.body.decode("utf-8", errors="replace")


def crawl(url, fetch=None, host_check=is_public_host, max_pages=MAX_PAGES, allow_private=False) -> CrawlResult:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise CrawlError(f"not an http(s) URL: {url}")
    check = (lambda host: True) if allow_private else host_check
    if not check(parts.hostname):
        raise CrawlError(f"{parts.hostname} is not a public host; pass --allow-private to crawl local or private addresses")
    fetch = fetch or make_fetcher(check)
    skipped, pages = [], []

    robots_by_origin: dict = {}

    def robots_for(u: str):
        """robots.txt of the URL's own origin: 401/403 mean disallowed, other failures mean allowed."""
        p = urlsplit(u)
        key = f"{p.scheme}://{p.netloc.lower()}"
        if key not in robots_by_origin:
            rp = urllib.robotparser.RobotFileParser()
            try:
                rp.parse(_decode(fetch(f"{key}/robots.txt")).splitlines())
            except CrawlError as e:
                rp.parse(["User-agent: *", "Disallow: /"] if str(e) in ("HTTP 401", "HTTP 403") else [])
            except Exception:
                rp.parse([])
            robots_by_origin[key] = rp
        return robots_by_origin[key]

    def get(u: str):
        if not robots_for(u).can_fetch(USER_AGENT, u):
            skipped.append({"url": u, "reason": "disallowed by robots.txt"})
            return None
        try:
            r = fetch(u)
        except CrawlError as e:
            skipped.append({"url": u, "reason": str(e)})
            return None
        if urlsplit(r.url).netloc.lower() != urlsplit(u).netloc.lower() and not robots_for(r.url).can_fetch(USER_AGENT, r.url):
            skipped.append({"url": u, "reason": "disallowed by robots.txt"})     # redirected to a host that forbids it
            return None
        if r.content_type not in HTML_TYPES:
            skipped.append({"url": u, "reason": f"not an HTML page ({r.content_type})"})
            return None
        return parse_page(_decode(r), r.url)

    home = get(url)
    if home is None:
        return CrawlResult([], skipped)
    pages.append(home)
    if not home.nav_links:
        skipped.append({"url": url, "reason": "no navigation links found on the homepage"})
    for link in select_nav_links(home, max_pages - 1):
        if not check(urlsplit(link).hostname or ""):
            skipped.append({"url": link, "reason": "not a public host"})
            continue
        page = get(link)
        if page:
            pages.append(page)
    return CrawlResult(pages, skipped)
