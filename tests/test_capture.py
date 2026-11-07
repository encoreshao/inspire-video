import subprocess

import pytest

from imgs import png
from showcase import capture as C


def fake_chrome(calls, fail_for=()):
    def run(argv, **kw):
        calls.append((argv, kw))
        if argv[-1] in fail_for:
            raise subprocess.CalledProcessError(1, argv, "", "boom")
        out = next(a.split("=", 1)[1] for a in argv if a.startswith("--screenshot="))
        w, h = next(a.split("=", 1)[1] for a in argv if a.startswith("--window-size=")).split(",")
        open(out, "wb").write(png(int(w), int(h)))
        return subprocess.CompletedProcess(argv, 0, "", "")
    return run


def test_find_chrome_prefers_known_paths_then_path_names():
    assert C.find_chrome(exists=lambda p: "Chromium" in p, which=lambda n: None).endswith("Chromium")
    assert C.find_chrome(exists=lambda p: False, which=lambda n: "/usr/bin/chromium" if n == "chromium" else None) == "/usr/bin/chromium"
    assert C.find_chrome(exists=lambda p: False, which=lambda n: None) is None


def test_command_is_an_argument_list_with_an_isolated_profile(tmp_path):
    cmd = C.capture_command("/c/chrome", "https://example.com/", tmp_path / "a.png", 1440, 900, tmp_path / "p")
    assert cmd[0] == "/c/chrome" and cmd[-1] == "https://example.com/"
    assert "--headless=new" in cmd and "--window-size=1440,900" in cmd
    assert f"--screenshot={tmp_path / 'a.png'}" in cmd and f"--user-data-dir={tmp_path / 'p'}" in cmd


def test_capture_pages_writes_one_image_per_page_and_size(tmp_path):
    calls = []
    caps, failures = C.capture_pages(["https://example.com/", "https://example.com/f"], tmp_path, chrome="/c/chrome",
                                     run=fake_chrome(calls))
    assert failures == [] and len(caps) == 4
    assert [(c["kind"], c["url"]) for c in caps][:2] == [("desktop", "https://example.com/"), ("phone", "https://example.com/")]
    assert all(c["path"].startswith(str(tmp_path)) and c["path"].endswith(".png") for c in caps)
    assert len({c["path"] for c in caps}) == 4
    assert all(kw["timeout"] == 60 and kw.get("shell") is None for _, kw in calls)


def test_a_failing_page_is_reported_and_the_rest_continue(tmp_path):
    calls = []
    caps, failures = C.capture_pages(["https://bad.example/", "https://ok.example/"], tmp_path, chrome="/c/chrome",
                                     run=fake_chrome(calls, fail_for=("https://bad.example/",)), sizes=(("desktop", 1440, 900),))
    assert [c["url"] for c in caps] == ["https://ok.example/"]
    assert failures == [{"url": "https://bad.example/", "reason": "browser failed: boom"}]


def test_chrome_producing_no_file_is_a_failure(tmp_path):
    run = lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "", "")
    caps, failures = C.capture_pages(["https://x.example/"], tmp_path, chrome="/c/chrome", run=run, sizes=(("desktop", 1440, 900),))
    assert caps == [] and "no screenshot" in failures[0]["reason"]


def test_non_http_urls_never_reach_the_browser(tmp_path):
    calls = []
    caps, failures = C.capture_pages(["file:///etc/passwd", "-remote-debugging-port=1", "javascript:1"], tmp_path,
                                     chrome="/c/chrome", run=fake_chrome(calls))
    assert caps == [] and calls == [] and len(failures) == 3


def test_no_chrome_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "find_chrome", lambda *a, **k: None)
    with pytest.raises(C.CaptureError, match="--screenshots"):
        C.capture_pages(["https://example.com/"], tmp_path)
