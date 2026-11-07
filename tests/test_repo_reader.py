import json
import os
import subprocess

import pytest

from imgs import png
from showcase import repo_reader as R
from showcase.sources import Source


def make_repo(tmp_path):
    root = tmp_path / "widget"
    (root / "screenshots").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "src").mkdir()
    (root / "node_modules" / "x").mkdir(parents=True)
    (root / "screenshots" / "home.png").write_bytes(png(800, 600))
    (root / "docs" / "guide.md").write_text("# Guide")
    (root / "src" / "a.py").write_text("print(1)")
    (root / "src" / "b.py").write_text("print(2)")
    (root / "src" / "c.ts").write_text("export {}")
    (root / "node_modules" / "x" / "skip.js").write_text("x")
    (root / "LICENSE").write_text("MIT License\n\nPermission is hereby granted, free of charge")
    (root / "package.json").write_text(json.dumps({"name": "widget", "description": "Tiny widgets", "version": "1.2.0",
                                                   "scripts": {"build": "x", "test": "y"}, "dependencies": {"left-pad": "1"}}))
    (root / "pyproject.toml").write_text('[project]\nname = "widget-py"\ndescription = "Py widgets"\nversion = "0.3"\n')
    (root / "outside.png").write_bytes(png(800, 600))
    (root / "README.md").write_text(
        "# Widget\n\n![hero](screenshots/home.png)\n![web](https://example.com/x.png)\n![gone](missing.png)\n"
        '![escape](../../etc/passwd.png)\n<img src="docs/../outside.png?raw=1" alt="x">\n')
    return root


def test_read_repo_collects_the_facts(tmp_path):
    info = R.read_repo(make_repo(tmp_path))
    assert info["name"] == "widget"
    assert info["readme"]["path"] == "README.md" and info["readme"]["text"].startswith("# Widget")
    assert "src/a.py" in info["tree"] and not any(t.startswith("node_modules") for t in info["tree"])
    assert info["manifests"]["package.json"] == {"name": "widget", "description": "Tiny widgets", "version": "1.2.0",
                                                 "scripts": ["build", "test"], "dependencies": ["left-pad"]}
    assert info["manifests"]["pyproject.toml"]["name"] == "widget-py"
    assert info["docs"] == ["docs/guide.md"] and info["license"] == "MIT"
    assert info["languages"][0] == {"language": "Python", "files": 2}
    assert info["image_candidates"][:2] == ["screenshots/home.png", "outside.png"]
    assert not any("passwd" in c for c in info["image_candidates"])


def test_files_outside_the_repo_are_never_read(tmp_path):
    root = make_repo(tmp_path)
    secret = tmp_path / "secret.png"
    secret.write_bytes(png(800, 600))
    (root / "link.png").symlink_to(secret)
    (root / "README.md").unlink()
    outside_readme = tmp_path / "outside-readme.md"
    outside_readme.write_text("# stolen\n![x](link.png)")
    (root / "README.md").symlink_to(outside_readme)
    info = R.read_repo(root)
    assert info["readme"] is None
    assert "link.png" not in info["image_candidates"] and "link.png" not in info["tree"]


def test_empty_repo_still_reads(tmp_path):
    (tmp_path / "empty").mkdir()
    info = R.read_repo(tmp_path / "empty")
    assert info["readme"] is None and info["license"] == "unknown" and info["languages"] == []


def test_clone_uses_dashdash_no_prompt_and_a_safe_folder(tmp_path):
    calls = []

    def run(argv, **kw):
        calls.append((argv, kw))
        os.makedirs(argv[-1])
        return subprocess.CompletedProcess(argv, 0, "", "")

    src = Source("gitlab", "https://gitlab.acme.io/team/app", "gitlab.acme.io", "team/app")
    dest = R.clone_repo(src, tmp_path / "cache", run=run)
    argv, kw = calls[0]
    assert argv[:5] == ["git", "clone", "--depth", "1", "--"] and argv[5] == src.url and argv[-1] == str(dest)
    assert kw["env"]["GIT_TERMINAL_PROMPT"] == "0" and dest.parent == tmp_path / "cache"
    assert dest.name == "gitlab.acme.io-team__app"


def test_existing_clone_is_updated_not_recloned(tmp_path):
    src = Source("github", "https://github.com/a/b", "github.com", "a/b")
    dest = tmp_path / "cache" / "github.com-a__b"
    (dest / ".git").mkdir(parents=True)
    calls = []
    R.clone_repo(src, tmp_path / "cache", run=lambda argv, **kw: calls.append(argv) or subprocess.CompletedProcess(argv, 0, "", ""))
    assert calls and calls[0][:4] == ["git", "-C", str(dest), "pull"]


def test_clone_failure_mentions_credentials(tmp_path):
    def run(argv, **kw):
        raise subprocess.CalledProcessError(128, argv, "", "fatal: could not read Username")

    with pytest.raises(R.RepoError, match="credentials"):
        R.clone_repo(Source("github", "https://github.com/a/b", "github.com", "a/b"), tmp_path / "c", run=run)


GH = {"description": "A gadget", "stargazerCount": 42, "repositoryTopics": [{"name": "video"}, {"topic": {"name": "tts"}}],
      "licenseInfo": {"spdxId": "MIT", "name": "MIT License"}, "latestRelease": {"tagName": "v1.0"},
      "homepageUrl": "https://gadget.dev", "primaryLanguage": {"name": "Python"}}


def test_github_metadata_via_gh():
    seen = []

    def run(argv, **kw):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, json.dumps(GH), "")

    meta, note = R.fetch_metadata(Source("github", "https://github.com/a/b", "github.com", "a/b"), run=run)
    assert note is None and seen[0][:4] == ["gh", "repo", "view", "a/b"]
    assert meta == {"description": "A gadget", "stars": 42, "topics": ["video", "tts"], "license": "MIT",
                    "latest_release": "v1.0", "homepage": "https://gadget.dev", "primary_language": "Python"}


def test_gitlab_metadata_via_glab_uses_the_host_and_an_encoded_path():
    seen = []

    def run(argv, **kw):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, json.dumps({"description": "Team app", "star_count": 3, "topics": ["x"], "web_url": "https://gitlab.acme.io/team/app"}), "")

    meta, note = R.fetch_metadata(Source("gitlab", "https://gitlab.acme.io/team/app", "gitlab.acme.io", "team/app"), run=run)
    assert seen[0] == ["glab", "api", "--hostname", "gitlab.acme.io", "projects/team%2Fapp"]
    assert meta["stars"] == 3 and meta["description"] == "Team app" and note is None


@pytest.mark.parametrize("exc", [FileNotFoundError("gh"), subprocess.CalledProcessError(1, ["gh"], "", "not logged in"), subprocess.TimeoutExpired(["gh"], 30)])
def test_metadata_problems_become_a_note(exc):
    def run(argv, **kw):
        raise exc

    meta, note = R.fetch_metadata(Source("github", "https://github.com/a/b", "github.com", "a/b"), run=run)
    assert meta == {} and note.startswith("repository metadata unavailable")


def test_a_relative_dot_path_still_gets_the_folder_name(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    monkeypatch.chdir(root)
    assert R.read_repo(".")["name"] == "widget"
