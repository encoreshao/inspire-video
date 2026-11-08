import json
import sys

import pytest

from imgs import png
from showcase import capture_page as CP
from showcase import ingest as I
from showcase import webcrawl as W
from showcase.capture import CaptureError

ALLOW = lambda host: True  # noqa: E731


def fetcher(robots=None):
    def fetch(url):
        if not url.endswith("/robots.txt"):
            raise W.CrawlError("HTTP 404")
        if robots is None:
            raise W.CrawlError("HTTP 404")
        if robots == "403":
            raise W.CrawlError("HTTP 403")
        return W.FetchResult(url, "text/plain", robots.encode())
    return fetch


def brief():
    return {"version": 1, "source": {"kind": "website", "url": "https://example.com/", "host": "example.com", "repo_path": ""},
            "created": "2026-11-08", "facts": [], "texts": [], "assets": [], "candidates": [], "rejected_assets": [],
            "skipped": [], "unknowns": [], "rights_unresolved": False, "hints": {"suggested_style": "device"}}


def project(tmp_path, with_brief=True):
    (tmp_path / "assets").mkdir()
    if with_brief:
        (tmp_path / "brief.json").write_text(json.dumps(brief()), encoding="utf-8")
    return tmp_path


def shot(project_dir, n):
    p = project_dir / "assets" / f"promo-{n}@2x.png"
    p.write_bytes(png(640, 400))
    return p


def test_check_url_accepts_a_public_page_that_robots_allows():
    CP.check_url("https://example.com/", fetch=fetcher("User-agent: *\nAllow: /"), host_check=ALLOW)
    CP.check_url("https://example.com/", fetch=fetcher(None), host_check=ALLOW)         # no robots.txt: allowed


@pytest.mark.parametrize("url, robots, message", [
    ("ftp://example.com/", None, "http"),
    ("https://example.com/private", "User-agent: *\nDisallow: /private", "robots.txt"),
    ("https://example.com/", "403", "robots.txt"),
])
def test_check_url_refuses(url, robots, message):
    with pytest.raises(CaptureError, match=message):
        CP.check_url(url, fetch=fetcher(robots), host_check=ALLOW)


def test_check_url_refuses_a_private_host_unless_allowed():
    with pytest.raises(CaptureError, match="public host"):
        CP.check_url("http://127.0.0.1:8000/", fetch=fetcher(None))
    CP.check_url("http://127.0.0.1:8000/", allow_private=True, fetch=fetcher(None))


def test_next_index_follows_the_existing_captures(tmp_path):
    assets = project(tmp_path) / "assets"
    assert CP.next_index(assets) == 1
    shot(tmp_path, 1)
    shot(tmp_path, 4)
    assert CP.next_index(assets) == 5
    assert CP.next_index(tmp_path / "nowhere") == 1


def test_registering_a_capture_adds_an_unresolved_promo_page_asset(tmp_path):
    p = project(tmp_path)
    asset = CP.register_in_brief(p, shot(p, 1), "https://example.com/")
    assert asset["path"] == "assets/promo-1@2x.png" and asset["role"] == "promo-page"
    assert asset["origin"] == "capture" and asset["rights_resolved"] is False and "confirm" in asset["rights"]
    saved = json.loads((p / "brief.json").read_text(encoding="utf-8"))
    assert saved["rights_unresolved"] is True and [a["path"] for a in saved["assets"]] == ["assets/promo-1@2x.png"]
    I.validate_brief(saved)


def test_registering_twice_replaces_the_same_path_and_keeps_both_images(tmp_path):
    p = project(tmp_path)
    CP.register_in_brief(p, shot(p, 1), "https://example.com/")
    CP.register_in_brief(p, shot(p, 1), "https://example.com/")
    CP.register_in_brief(p, shot(p, 2), "https://example.com/pricing")
    saved = json.loads((p / "brief.json").read_text(encoding="utf-8"))
    assert [a["path"] for a in saved["assets"]] == ["assets/promo-1@2x.png", "assets/promo-2@2x.png"]
    assert saved["rights_unresolved"] is True


def test_registering_without_a_brief_says_to_run_ingest_first(tmp_path):
    p = project(tmp_path, with_brief=False)
    with pytest.raises(CaptureError, match="ingest"):
        CP.register_in_brief(p, shot(p, 1), "https://example.com/")


def fake_capture(layout_elements):
    def capture(url, out_dir, index, hide=(), host_check=None, project=None):
        image = out_dir / f"promo-{index}@2x.png"
        image.write_bytes(png(640, 400))
        layout = {"page": {"w": 320, "h": 200}, "elements": layout_elements}
        return {"image": image, "layout": out_dir / f"promo-{index}.layout.json", "layout_data": layout}
    return capture


def test_the_command_captures_twice_with_two_indexes_and_keeps_rights_unresolved(tmp_path, monkeypatch, capsys):
    p = project(tmp_path)
    monkeypatch.setattr(CP, "check_url", lambda *a, **k: None)
    monkeypatch.setattr(CP, "capture_page", fake_capture([{"id": "heading-1", "role": "heading"}]))
    assert CP.main(["https://example.com/", "--project", str(p)]) == 0
    assert CP.main(["https://example.com/pricing", "--project", str(p)]) == 0
    saved = json.loads((p / "brief.json").read_text(encoding="utf-8"))
    assert [a["path"] for a in saved["assets"]] == ["assets/promo-1@2x.png", "assets/promo-2@2x.png"]
    assert saved["rights_unresolved"] is True
    out = capsys.readouterr().out
    assert "1 heading" in out and "rights" in out and "unresolved" in out


def test_the_command_warns_when_a_page_has_no_elements(tmp_path, monkeypatch, capsys):
    p = project(tmp_path)
    monkeypatch.setattr(CP, "check_url", lambda *a, **k: None)
    monkeypatch.setattr(CP, "capture_page", fake_capture([]))
    assert CP.main(["https://example.com/", "--project", str(p)]) == 0
    io = capsys.readouterr()
    assert "elements: none" in io.out and "focus rectangle" in io.err


def test_the_command_reports_a_capture_error_and_exits_1(tmp_path, monkeypatch, capsys):
    p = project(tmp_path)

    def refuse(*a, **k):
        raise CaptureError("not a public host")

    monkeypatch.setattr(CP, "check_url", refuse)
    assert CP.main(["http://127.0.0.1/", "--project", str(p)]) == 1
    assert "error: not a public host" in capsys.readouterr().err


def test_missing_playwright_is_a_clear_one_line_error(tmp_path, monkeypatch, capsys):
    p = project(tmp_path)
    monkeypatch.setattr(CP, "check_url", lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)             # makes the import fail
    assert CP.main(["https://example.com/", "--project", str(p)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error: Playwright is not installed") and "pip install" in err and err.count("\n") == 1


def never_capture(*args, **kwargs):
    raise AssertionError("the browser must not start when the brief cannot take the result")


def test_the_command_checks_the_brief_before_it_captures(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(CP, "check_url", lambda *a, **k: None)
    monkeypatch.setattr(CP, "capture_page", never_capture)
    missing = tmp_path / "a"
    missing.mkdir()
    project(missing, with_brief=False)
    assert CP.main(["https://example.com/", "--project", str(missing)]) == 1
    assert "ingest" in capsys.readouterr().err
    broken = tmp_path / "b"
    broken.mkdir()
    project(broken, with_brief=False)
    (broken / "brief.json").write_text("{not json", encoding="utf-8")
    assert CP.main(["https://example.com/", "--project", str(broken)]) == 1
    assert "brief.json" in capsys.readouterr().err and (broken / "brief.json").read_text(encoding="utf-8") == "{not json"
    keyless = tmp_path / "c"
    keyless.mkdir()
    project(keyless, with_brief=False)
    (keyless / "brief.json").write_text(json.dumps({"version": 1}), encoding="utf-8")
    assert CP.main(["https://example.com/", "--project", str(keyless)]) == 1
    assert "brief" in capsys.readouterr().err


def test_a_failed_brief_write_leaves_the_brief_untouched_and_no_temp_file(tmp_path, monkeypatch):
    p = project(tmp_path)
    before = (p / "brief.json").read_bytes()

    def disk_full(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(CP.os, "replace", disk_full)
    with pytest.raises(OSError, match="disk full"):
        CP.register_in_brief(p, shot(p, 1), "https://example.com/")
    assert (p / "brief.json").read_bytes() == before
    assert not list(p.glob("*.tmp")) and not list(p.glob("brief.json.*"))


@pytest.mark.parametrize("index", ["0", "-1"])
def test_the_index_must_be_at_least_one(tmp_path, monkeypatch, capsys, index):
    p = project(tmp_path)
    monkeypatch.setattr(CP, "check_url", lambda *a, **k: None)
    monkeypatch.setattr(CP, "capture_page", never_capture)
    assert CP.main(["https://example.com/", "--project", str(p), "--index", index]) == 1
    assert "index" in capsys.readouterr().err


def test_a_host_that_does_not_resolve_is_reported_as_a_typo_not_as_private():
    with pytest.raises(CaptureError, match="could not be resolved"):
        CP.check_url("http://no-such-host.invalid/", fetch=fetcher(None))


def test_a_missing_chrome_says_to_install_chrome(tmp_path, monkeypatch):
    import types

    class PWError(Exception):
        pass

    class Chromium:
        def launch(self, **kwargs):
            raise PWError("BrowserType.launch: Chromium distribution 'chrome' is not found at /Applications/Google Chrome.app")

    class PW:
        chromium = Chromium()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    fake = types.ModuleType("playwright.sync_api")
    fake.Error, fake.TimeoutError, fake.sync_playwright = PWError, type("Timeout", (PWError,), {}), lambda: PW()
    monkeypatch.setitem(sys.modules, "playwright", types.ModuleType("playwright"))
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake)
    with pytest.raises(CaptureError, match="Install Google Chrome"):
        CP.capture_page("http://example.com/", tmp_path, 1)
