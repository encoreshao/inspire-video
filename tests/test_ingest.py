import json
import subprocess
from pathlib import Path

import pytest

from imgs import png
from showcase import ingest as I
from showcase import webcrawl as W

HOME = """<html><head><title>Acme Widgets</title><meta name="description" content="Widgets for everyone"></head>
<body><header><a href="/features">Features</a><a href="/pricing">Pricing</a></header><h1>Build faster</h1></body></html>"""
PAGES = {
    "https://example.com/": HOME,
    "https://example.com/features": "<html><title>Features</title><body><h1>All features</h1></body></html>",
    "https://example.com/pricing": "<html><title>Pricing</title><body><h1>Cheap</h1></body></html>",
}


def fake_fetch(robots=None, pages=PAGES):
    def fetch(url):
        if url.endswith("/robots.txt"):
            if robots is None:
                raise W.CrawlError("HTTP 404")
            return W.FetchResult(url, "text/plain", robots.encode())
        if url not in pages:
            raise W.CrawlError("HTTP 404")
        return W.FetchResult(url, "text/html", pages[url].encode())
    return fetch


class Runner:
    """Fakes Chrome, git and gh in one place and records every call."""
    def __init__(self, gh=None):
        self.calls, self.gh = [], gh

    def __call__(self, argv, **kw):
        self.calls.append(list(argv))
        if argv[0] == "/fake/chrome":
            out = next(a.split("=", 1)[1] for a in argv if a.startswith("--screenshot="))
            w, h = next(a.split("=", 1)[1] for a in argv if a.startswith("--window-size=")).split(",")
            Path(out).write_bytes(png(int(w), int(h)) + out.encode())      # unique bytes per file
            return subprocess.CompletedProcess(argv, 0, "", "")
        if argv[:2] == ["git", "clone"]:
            dest = Path(argv[-1])
            (dest / "docs").mkdir(parents=True)
            (dest / "README.md").write_text("# Widget\nA gadget that does things.")
            (dest / "LICENSE").write_text("MIT License")
            return subprocess.CompletedProcess(argv, 0, "", "")
        if argv[0] == "gh":
            return subprocess.CompletedProcess(argv, 0, json.dumps(self.gh or {}), "")
        raise AssertionError(f"unexpected command {argv}")


def deps(**kw):
    return I.Deps(fetch=kw.pop("fetch", fake_fetch()), host_check=lambda h: True, run=kw.pop("run", Runner()),
                  chrome="/fake/chrome", **kw)


def shots(tmp_path, n=2):
    d = tmp_path / "shots"
    d.mkdir()
    for i in range(1, n + 1):
        (d / f"{i}-screen.png").write_bytes(png(900, 600 + i))
    return d


def repo(tmp_path, with_image=True):
    r = tmp_path / "widget"
    r.mkdir()
    (r / "README.md").write_text("# Widget\nMakes gadgets.\n![hero](shots/hero.png)")
    (r / "package.json").write_text(json.dumps({"name": "widget", "description": "Tiny widgets"}))
    (r / "LICENSE").write_text("MIT License")
    if with_image:
        (r / "shots").mkdir()
        (r / "shots" / "hero.png").write_bytes(png(800, 600))
    return r


def test_case1_website_only_crawls_and_captures(tmp_path):
    runner = Runner()
    brief = I.ingest("https://example.com/", tmp_path / "p", deps=deps(run=runner))
    assert {a["origin"] for a in brief["assets"]} == {"capture"} and len(brief["assets"]) == 4   # home desktop+phone, 2 nav pages desktop
    assert brief["rights_unresolved"] is True and brief["hints"]["suggested_style"] == "device"
    claims = " | ".join(f["claim"] for f in brief["facts"])
    assert "Acme Widgets" in claims and "Widgets for everyone" in claims and "Features" in claims
    assert all(f["source"].startswith("https://example.com") for f in brief["facts"]) and brief["facts"][0]["id"] == "f1"
    assert [t["kind"] for t in brief["texts"]] == ["page", "page", "page"]
    assert all((tmp_path / "p" / a["path"]).exists() and not Path(a["path"]).is_absolute() for a in brief["assets"])
    assert json.loads((tmp_path / "p" / "brief.json").read_text()) == brief
    I.validate_brief(brief)


def test_case2_website_plus_screenshots_uses_only_the_users_images(tmp_path):
    runner = Runner()
    brief = I.ingest("https://example.com/", tmp_path / "p", screenshots=shots(tmp_path), deps=deps(run=runner))
    assert [a["origin"] for a in brief["assets"]] == ["user", "user"] and brief["rights_unresolved"] is False
    assert not any(c[0] == "/fake/chrome" for c in runner.calls) and brief["candidates"] == []
    assert brief["facts"] and brief["texts"]


def test_case3_repo_only_uses_repo_images_and_marks_rights(tmp_path):
    brief = I.ingest(str(repo(tmp_path)), tmp_path / "p", deps=deps())
    assert [a["origin"] for a in brief["assets"]] == ["repo"] and "license: MIT" in brief["assets"][0]["rights"]
    assert brief["rights_unresolved"] is True
    claims = " | ".join(f["claim"] for f in brief["facts"])
    assert "Tiny widgets" in claims and "MIT" in claims
    assert brief["texts"][0]["kind"] == "readme" and brief["texts"][0]["source"] == "README.md"
    I.validate_brief(brief)


def test_case3_repo_without_images_suggests_the_terminal_style(tmp_path):
    brief = I.ingest(str(repo(tmp_path, with_image=False)), tmp_path / "p", deps=deps())
    assert brief["assets"] == [] and brief["hints"]["suggested_style"] == "terminal"
    assert any("terminal" in u for u in brief["unknowns"])


def test_case4_repo_plus_screenshots_keeps_repo_images_as_candidates(tmp_path):
    brief = I.ingest(str(repo(tmp_path)), tmp_path / "p", screenshots=shots(tmp_path), deps=deps())
    assert [a["origin"] for a in brief["assets"]] == ["user", "user"] and brief["rights_unresolved"] is False
    assert [c["origin"] for c in brief["candidates"]] == ["repo"]
    assert len(list((tmp_path / "p" / "assets").iterdir())) == 2          # candidates are not copied


def test_github_repo_is_cloned_and_enriched_with_metadata(tmp_path):
    gh = {"description": "A gadget", "stargazerCount": 42, "repositoryTopics": [{"name": "video"}],
          "licenseInfo": {"spdxId": "MIT"}, "latestRelease": {"tagName": "v1.0"}, "homepageUrl": "", "primaryLanguage": {"name": "Python"}}
    runner = Runner(gh=gh)
    brief = I.ingest("https://github.com/acme/widget", tmp_path / "p", screenshots=shots(tmp_path),
                     deps=deps(run=runner), cache_dir=tmp_path / "cache")
    claims = " | ".join(f["claim"] for f in brief["facts"])
    assert "42 stars" in claims and "video" in claims and "v1.0" in claims
    assert brief["source"]["kind"] == "github" and brief["source"]["repo_path"] == "acme/widget"
    assert any(c[:2] == ["git", "clone"] for c in runner.calls)


def test_unreadable_website_without_screenshots_asks_for_screenshots(tmp_path):
    with pytest.raises(I.IngestError, match="--screenshots"):
        I.ingest("https://example.com/", tmp_path / "p", deps=deps(fetch=fake_fetch(robots="User-agent: *\nDisallow: /")))
    assert not (tmp_path / "p" / "brief.json").exists()


def test_unreadable_website_with_screenshots_continues_with_a_note(tmp_path):
    brief = I.ingest("https://example.com/", tmp_path / "p", screenshots=shots(tmp_path),
                     deps=deps(fetch=fake_fetch(robots="User-agent: *\nDisallow: /")))
    assert brief["texts"] == [] and any("website text" in u for u in brief["unknowns"])
    assert brief["skipped"][0]["reason"] == "disallowed by robots.txt"


def test_private_addresses_are_refused_by_default(tmp_path):
    with pytest.raises(W.CrawlError, match="not a public host"):
        I.ingest("http://127.0.0.1:8000/", tmp_path / "p", deps=I.Deps(fetch=fake_fetch()))


def test_rejected_user_images_are_listed(tmp_path):
    d = shots(tmp_path, 1)
    (d / "broken.png").write_bytes(b"not an image")
    brief = I.ingest(str(repo(tmp_path)), tmp_path / "p", screenshots=d, deps=deps())
    assert len(brief["assets"]) == 1 and brief["rejected_assets"][0]["path"].endswith("broken.png")


@pytest.mark.parametrize("mutate, needle", [
    (lambda b: b.pop("facts"), "facts"),
    (lambda b: b.update(version=2), "version"),
    (lambda b: b["facts"].append({"id": "f9", "claim": "", "source": "x"}), "fact"),
    (lambda b: b["assets"].append({"path": "x"}), "asset"),
])
def test_validate_brief_catches_a_damaged_brief(tmp_path, mutate, needle):
    brief = I.ingest(str(repo(tmp_path)), tmp_path / "p", deps=deps())
    mutate(brief)
    with pytest.raises(I.IngestError, match=needle):
        I.validate_brief(brief)


def test_cli_writes_the_brief_and_reports_problems(tmp_path, capsys, monkeypatch):
    fake = deps()                                    # build it before patching: deps() itself calls I.Deps
    monkeypatch.setattr(I, "Deps", lambda: fake)
    p = tmp_path / "proj"
    assert I.main([str(repo(tmp_path)), "--project", str(p)]) == 0
    assert (p / "brief.json").exists() and "brief written" in capsys.readouterr().out
    assert I.main(["ftp://example.com/", "--project", str(tmp_path / "x")]) == 1
    assert "error:" in capsys.readouterr().err


def test_reingest_removes_only_the_files_it_created(tmp_path):
    p, d = tmp_path / "p", shots(tmp_path)
    I.ingest("https://example.com/", p, screenshots=d, deps=deps())
    (p / "assets" / "notes.txt").write_text("keep me")
    brief = I.ingest("https://example.com/", p, screenshots=d, deps=deps())
    names = sorted(x.name for x in (p / "assets").iterdir())
    assert "notes.txt" in names and len(names) == 3 and len(brief["assets"]) == 2


def test_screenshots_inside_the_projects_assets_folder_are_refused_and_untouched(tmp_path):
    p = tmp_path / "p"
    (p / "assets").mkdir(parents=True)
    (p / "assets" / "1-a.png").write_bytes(png(900, 600))
    (p / "assets" / "note.txt").write_text("mine")
    with pytest.raises(I.IngestError, match="assets"):
        I.ingest("https://example.com/", p, screenshots=p / "assets", deps=deps())
    assert sorted(x.name for x in (p / "assets").iterdir()) == ["1-a.png", "note.txt"]


def test_capture_candidates_survive_next_to_user_screenshots(tmp_path):
    p = tmp_path / "p"
    brief = I.ingest("https://example.com/", p, screenshots=shots(tmp_path), capture=True, deps=deps())
    assert [a["origin"] for a in brief["assets"]] == ["user", "user"] and brief["rights_unresolved"] is False
    caps = [c for c in brief["candidates"] if c["origin"] == "capture"]
    assert len(caps) == 4 and all((p / c["path"]).is_file() and c["path"].startswith("candidates/") for c in caps)
    assert len(list((p / "assets").iterdir())) == 2


def test_a_failed_rerun_leaves_no_stale_brief(tmp_path):
    p = tmp_path / "p"
    I.ingest("https://example.com/", p, screenshots=shots(tmp_path), deps=deps())
    assert (p / "brief.json").exists()
    with pytest.raises(I.IngestError):
        I.ingest("https://example.com/", p, deps=deps(fetch=fake_fetch(robots="User-agent: *\nDisallow: /")))
    assert not (p / "brief.json").exists()


def test_when_every_screenshot_is_unusable_ingest_stops(tmp_path):
    d = tmp_path / "bad"
    d.mkdir()
    (d / "tiny.png").write_bytes(png(50, 50))
    (d / "fake.png").write_bytes(b"nope")
    with pytest.raises(I.IngestError, match="none of the 2 files"):
        I.ingest(str(repo(tmp_path)), tmp_path / "p", screenshots=d, deps=deps())


def test_a_relative_project_path_works_with_page_capture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    brief = I.ingest("https://example.com/", "proj", deps=deps())
    assert len(brief["assets"]) == 4 and all((tmp_path / "proj" / a["path"]).is_file() for a in brief["assets"])


def test_the_social_preview_image_is_a_fact(tmp_path):
    page = '<html><head><title>T</title><meta property="og:image" content="/og.png"></head><body><h1>x</h1></body></html>'
    brief = I.ingest("https://example.com/", tmp_path / "p", screenshots=shots(tmp_path), deps=deps(fetch=fake_fetch(pages={"https://example.com/": page})))
    assert any(f["claim"] == "Social preview image: https://example.com/og.png" for f in brief["facts"])


def test_cli_warns_about_rejected_images_and_skipped_pages(tmp_path, capsys, monkeypatch):
    d = shots(tmp_path, 1)
    (d / "broken.png").write_bytes(b"not an image")
    fake = deps(fetch=fake_fetch(robots="User-agent: *\nDisallow: /features"))
    monkeypatch.setattr(I, "Deps", lambda: fake)
    assert I.main(["https://example.com/", "--project", str(tmp_path / "p"), "--screenshots", str(d)]) == 0
    err = capsys.readouterr().err
    assert "warning: image not used" in err and "broken.png" in err
    assert "warning: page skipped" in err and "/features" in err
