import pytest

from showcase import webcrawl as W

HOME = """<html><head><title> Acme  Widgets </title>
<meta name="description" content="Widgets for everyone">
<meta property="og:image" content="/img/og.png">
<style>.x{color:red}</style><script>var secret = 1;</script></head>
<body><header><a href="/">Home</a><a href="/features#top">Features</a></header>
<nav><a href="https://www.example.com/pricing">Pricing</a><a href="mailto:a@b.c">Mail</a>
<a href="https://other.com/x">Elsewhere</a><a href="/guide.pdf">PDF</a><a href="/features">Features again</a></nav>
<h1>Build   faster</h1><h2>Why Acme</h2><p>Body copy here.</p><a href="/hidden">not in nav</a></body></html>"""


def test_parse_page_extracts_the_basics():
    p = W.parse_page(HOME, "https://example.com/")
    assert p.title == "Acme Widgets" and p.description == "Widgets for everyone"
    assert p.og_image == "https://example.com/img/og.png"
    assert p.headings == ["Build faster", "Why Acme"]
    assert "Body copy here." in p.text and "secret" not in p.text and "color:red" not in p.text
    urls = [l["url"] for l in p.nav_links]
    assert "https://example.com/hidden" not in urls and "https://example.com/features#top" in urls


def test_select_nav_links_keeps_same_origin_pages_once():
    p = W.parse_page(HOME, "https://example.com/")
    assert W.select_nav_links(p, 5) == ["https://example.com/features", "https://www.example.com/pricing"]
    assert W.select_nav_links(p, 1) == ["https://example.com/features"]


@pytest.mark.parametrize("host, ok", [
    ("127.0.0.1", False), ("10.0.0.5", False), ("192.168.1.9", False), ("169.254.169.254", False),
    ("::1", False), ("localhost", False), ("printer.local", False), ("", False), ("93.184.216.34", True),
])
def test_is_public_host(host, ok):
    assert W.is_public_host(host) is ok


def site(pages, robots=None):
    def fetch(url):
        if url.endswith("/robots.txt"):
            if robots is None:
                raise W.CrawlError("HTTP 404")
            return W.FetchResult(url, "text/plain", robots.encode())
        if url not in pages:
            raise W.CrawlError("HTTP 404")
        item = pages[url]
        if isinstance(item, Exception):
            raise item
        ctype, body = item if isinstance(item, tuple) else ("text/html", item)
        return W.FetchResult(url, ctype, body.encode())
    return fetch


PAGES = {
    "https://example.com/": HOME,
    "https://example.com/features": "<html><title>Features</title><body><h1>All the features</h1></body></html>",
    "https://www.example.com/pricing": "<html><title>Pricing</title><body><h1>Cheap</h1></body></html>",
}
ANY = lambda host: True


def urls(result):
    return [p.url for p in result.pages]


def test_crawl_visits_the_homepage_and_its_nav_pages():
    r = W.crawl("https://example.com/", fetch=site(PAGES), host_check=ANY)
    assert urls(r) == ["https://example.com/", "https://example.com/features", "https://www.example.com/pricing"]
    assert r.skipped == []


def test_robots_txt_blocks_a_page_and_it_is_not_fetched():
    seen = []
    base = site(PAGES, robots="User-agent: *\nDisallow: /features")

    def spy(url):
        seen.append(url)
        return base(url)

    r = W.crawl("https://example.com/", fetch=spy, host_check=ANY)
    assert "https://example.com/features" not in seen and "https://example.com/features" not in urls(r)
    assert {"url": "https://example.com/features", "reason": "disallowed by robots.txt"} in r.skipped


def test_a_disallowed_homepage_stops_cleanly():
    r = W.crawl("https://example.com/", fetch=site(PAGES, robots="User-agent: *\nDisallow: /"), host_check=ANY)
    assert r.pages == [] and r.skipped[0]["reason"] == "disallowed by robots.txt"


def test_failures_and_non_html_are_skipped_not_fatal():
    pages = dict(PAGES)
    pages["https://example.com/features"] = W.CrawlError("HTTP 500")
    pages["https://www.example.com/pricing"] = ("application/pdf", "%PDF")
    r = W.crawl("https://example.com/", fetch=site(pages), host_check=ANY)
    assert urls(r) == ["https://example.com/"]
    reasons = {s["url"]: s["reason"] for s in r.skipped}
    assert reasons["https://example.com/features"] == "HTTP 500"
    assert "not an HTML page" in reasons["https://www.example.com/pricing"]


def test_max_pages_and_no_nav_note():
    r = W.crawl("https://example.com/", fetch=site(PAGES), host_check=ANY, max_pages=2)
    assert len(r.pages) == 2
    plain = {"https://example.com/": "<html><title>Solo</title><body>hi</body></html>"}
    r = W.crawl("https://example.com/", fetch=site(plain), host_check=ANY)
    assert len(r.pages) == 1 and any("no navigation links" in s["reason"] for s in r.skipped)


@pytest.mark.parametrize("url", ["http://127.0.0.1:8000/", "http://169.254.169.254/latest/meta-data/", "http://localhost/"])
def test_private_hosts_are_refused_before_any_request(url):
    calls = []
    with pytest.raises(W.CrawlError, match="not a public host"):
        W.crawl(url, fetch=lambda u: calls.append(u))
    assert calls == []


def test_allow_private_bypasses_the_guard():
    pages = {"http://127.0.0.1:8000/": "<html><title>Dev</title><body>x</body></html>"}
    r = W.crawl("http://127.0.0.1:8000/", fetch=site(pages), allow_private=True)
    assert urls(r) == ["http://127.0.0.1:8000/"]


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com/", "example.com"])
def test_non_http_urls_are_refused(url):
    with pytest.raises(W.CrawlError, match="not an http"):
        W.crawl(url, fetch=site({}), host_check=ANY)


def test_a_redirect_to_a_private_address_is_refused():
    handler = W._GuardedRedirect(W.is_public_host)
    with pytest.raises(W.CrawlError, match="refusing to follow"):
        handler.redirect_request(None, None, 302, "Found", {}, "http://169.254.169.254/latest/meta-data/")
    with pytest.raises(W.CrawlError, match="refusing to follow"):
        handler.redirect_request(None, None, 302, "Found", {}, "file:///etc/passwd")


def with_robots(base, mapping):
    def fetch(url):
        if url in mapping:
            v = mapping[url]
            if isinstance(v, Exception):
                raise v
            return W.FetchResult(url, "text/plain", v.encode())
        return base(url)
    return fetch


def test_robots_txt_is_read_for_each_origin():
    fetch = with_robots(site(PAGES), {"https://www.example.com/robots.txt": "User-agent: *\nDisallow: /pricing"})
    r = W.crawl("https://example.com/", fetch=fetch, host_check=ANY)
    assert urls(r) == ["https://example.com/", "https://example.com/features"]
    assert {"url": "https://www.example.com/pricing", "reason": "disallowed by robots.txt"} in r.skipped


def test_a_forbidden_robots_txt_means_disallowed_but_a_server_error_does_not():
    r = W.crawl("https://example.com/", fetch=with_robots(site(PAGES), {"https://example.com/robots.txt": W.CrawlError("HTTP 403")}), host_check=ANY)
    assert r.pages == [] and r.skipped[0]["reason"] == "disallowed by robots.txt"
    r = W.crawl("https://example.com/", fetch=with_robots(site(PAGES), {"https://example.com/robots.txt": W.CrawlError("HTTP 500")}), host_check=ANY)
    assert len(r.pages) == 3


def test_a_homepage_that_redirects_to_another_host_is_checked_against_that_hosts_robots():
    def fetch(url):
        if url == "https://example.com/":
            return W.FetchResult("https://other.example/", "text/html", HOME.encode())
        if url == "https://other.example/robots.txt":
            return W.FetchResult(url, "text/plain", b"User-agent: *\nDisallow: /")
        raise W.CrawlError("HTTP 404")
    r = W.crawl("https://example.com/", fetch=fetch, host_check=ANY)
    assert r.pages == [] and r.skipped[0]["reason"] == "disallowed by robots.txt"
