import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from showcase import capture_page as CP
from showcase import page_layout as L
from showcase import webcrawl as W
from showcase.assets import image_size
from showcase.capture import CaptureError


def _browser_works() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(channel="chrome").close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _browser_works(), reason="Playwright with an installed Chrome is required")

HOME = """<!doctype html><html><body style="margin:0;font-family:sans-serif">
<div class="banner" style="height:60px;background:#fc0">Cookies!</div>
<h1 style="margin:40px">Hello promo</h1>
<button style="margin:0 40px;padding:20px 40px">Download</button>
<div class="card" style="margin:40px;height:600px;background:#eee">card</div>
<img alt="logo" width="200" height="120" style="margin:0 40px;background:#ccc"
 src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">
</body></html>"""
PAGES = {
    "/": HOME,
    "/tall": "<html><body style='margin:0'><h1>Tall</h1><div style='height:7000px'></div></body></html>",
    "/blank": "<html><body style='margin:0;height:1200px'></body></html>",
}


@pytest.fixture
def site():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = PAGES.get(self.path.split("?")[0])
            self.send_response(200 if body else 404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write((body or "").encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_a_capture_writes_a_2x_image_and_a_matching_layout(site, tmp_path):
    r = CP.capture_page(site + "/", tmp_path / "assets", 1, project=tmp_path)
    layout = r["layout_data"]
    assert r["image"].name == "promo-1@2x.png" and r["layout"].name == "promo-1.layout.json"
    assert image_size(r["image"]) == (layout["page"]["w"] * 2, layout["page"]["h"] * 2)
    assert layout["image"] == "assets/promo-1@2x.png" and layout["scale"] == 2
    assert json.loads(r["layout"].read_text(encoding="utf-8")) == layout
    L.validate_layout(layout)
    els = {e["id"]: e for e in layout["elements"]}
    assert set(els) == {"heading-1", "button-1", "card-1", "image-1"}
    assert els["heading-1"]["text"] == "Hello promo" and els["button-1"]["text"] == "Download"
    assert abs(els["heading-1"]["box"]["y"] - 100) <= 2 and abs(els["heading-1"]["box"]["x"] - 40) <= 2


def test_hide_removes_an_element_from_the_picture_and_moves_the_layout(site, tmp_path):
    r = CP.capture_page(site + "/", tmp_path, 1, hide=(".banner",))
    heading = next(e for e in r["layout_data"]["elements"] if e["id"] == "heading-1")
    assert abs(heading["box"]["y"] - 40) <= 2           # the 60 px banner is gone


def test_a_page_taller_than_the_cap_is_cut_and_stays_valid(site, tmp_path):
    r = CP.capture_page(site + "/tall", tmp_path, 1)
    assert r["layout_data"]["page"]["h"] == L.MAX_PAGE_H
    assert image_size(r["image"])[1] == L.MAX_PAGE_H * 2
    L.validate_layout(r["layout_data"])


def test_a_page_with_no_elements_gives_an_empty_valid_layout(site, tmp_path):
    r = CP.capture_page(site + "/blank", tmp_path, 1)
    assert r["layout_data"]["elements"] == [] and r["layout_data"]["page"]["h"] == 1200
    L.validate_layout(r["layout_data"])


def test_a_final_page_on_a_private_host_is_refused_before_anything_is_written(site, tmp_path):
    with pytest.raises(CaptureError, match="public host"):
        CP.capture_page(site + "/", tmp_path / "out", 1, host_check=W.is_public_host)    # 127.0.0.1 is not public
    assert not list((tmp_path / "out").glob("*"))
    assert CP.capture_page(site + "/", tmp_path / "ok", 1, host_check=lambda host: True)["image"].exists()


@pytest.mark.parametrize("selector", ["a{color:red}", ".x; y", "", "  ", ".a}"])
def test_hide_selectors_that_could_break_the_style_rule_are_rejected_before_the_browser_starts(site, tmp_path, selector):
    with pytest.raises(CaptureError, match="selector"):
        CP.capture_page(site + "/", tmp_path, 1, hide=(selector,))


@pytest.fixture
def spy():
    """A second local server that records every request it receives."""
    hits = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "image/gif")
            self.end_headers()
            self.wfile.write(b"GIF89a")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield hits, server.server_port
    server.shutdown()
    server.server_close()


def test_sub_resources_on_hosts_the_check_refuses_are_never_requested(site, spy, tmp_path):
    hits, port = spy
    PAGES["/embeds"] = (f"<html><body style='margin:0'><h1>Embeds</h1>"
                        f"<img src='http://localhost:{port}/hit' width='60' height='40'></body></html>")
    try:
        CP.capture_page(site + "/embeds", tmp_path / "blocked", 1, host_check=lambda host: host == "127.0.0.1")
        assert hits == []                                    # the request to localhost never left the browser
        CP.capture_page(site + "/embeds", tmp_path / "open", 1, host_check=lambda host: True)
        assert hits == ["/hit"]                              # control: without the guard the same page requests it
    finally:
        PAGES.pop("/embeds", None)


def test_a_page_that_ends_on_a_non_web_url_is_refused(site, tmp_path):
    PAGES["/away"] = "<html><body><script>setTimeout(() => { location.href = 'about:blank'; }, 100)</script>moving</body></html>"
    try:
        with pytest.raises(CaptureError, match="public"):
            CP.capture_page(site + "/away", tmp_path / "out", 1, host_check=lambda host: True)
        assert not list((tmp_path / "out").glob("*"))
    finally:
        PAGES.pop("/away", None)


def test_a_redirect_after_the_first_check_is_caught_before_the_screenshot(site, spy, tmp_path, monkeypatch):
    hits, port = spy
    monkeypatch.setattr(CP, "SETTLE_MS", 2500)               # the redirect fires inside the settle window
    PAGES["/late"] = (f"<html><body><h1>Late</h1><script>setTimeout(() => {{ location.href = "
                      f"'http://localhost:{port}/x'; }}, 1500)</script></body></html>")
    try:
        with pytest.raises(CaptureError, match="public"):
            CP.capture_page(site + "/late", tmp_path / "out", 1, host_check=lambda host: host == "127.0.0.1")
        assert not list((tmp_path / "out").glob("*")) and hits == []
    finally:
        PAGES.pop("/late", None)
