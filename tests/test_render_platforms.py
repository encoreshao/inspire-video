import json
import shutil
import sys
from pathlib import Path

import pytest

import platforms
import render

REAL_ROOT = Path(__file__).resolve().parent.parent


def make_project(root: Path, seconds=60) -> Path:
    (root / "schemas").mkdir(exist_ok=True)
    shutil.copy(REAL_ROOT / "schemas/manifest-schema.json", root / "schemas/manifest-schema.json")
    (root / "video").mkdir(exist_ok=True)
    proj = root / "output/projects/demo"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "clip.mp4").write_bytes(b"x")
    manifest = {
        "project_id": "demo",
        "settings": {"width": 1080, "height": 1920, "fps": 30},
        "source": {"path": "x.mp4", "start_seconds": 0, "end_seconds": seconds},
        "copy": {"headline_zh": "先行动，再自信", "subtitle_en": "Act First", "quote_en": "Hello there.", "quote_zh": "你好。"},
        "video": {"clip_path": "clip.mp4"},
        "subtitles": [{"start": 1.0, "end": 50.0, "en": "Hello there.", "zh": "你好。"}],
        "provenance": {"rights_confirmed": True, "source_reference": "x", "review_status": "approved"},
    }
    (proj / "video_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False))
    return proj


@pytest.fixture
def run(tmp_path, monkeypatch):
    calls = []

    class Done:
        returncode = 0

    def fake_run(cmd, cwd=None, **kw):
        calls.append(cmd)
        return Done()

    monkeypatch.setattr(render, "ROOT", tmp_path)
    monkeypatch.setattr(render.subprocess, "run", fake_run)

    def go(*args):
        proj = make_project(tmp_path)
        monkeypatch.setattr(sys, "argv", ["render.py", str(proj), *args])
        rc = render.main()
        return rc, calls, proj

    go.root = tmp_path
    go.calls = calls
    return go


def outputs(calls):
    return [(c[2], c[5].split("output/")[-1]) for c in calls]


def test_without_flags_nothing_changes(run):
    rc, calls, proj = run()
    assert rc == 0
    assert outputs(calls) == [("render", "final/demo/demo.mp4"), ("still", "final/demo/cover.png")]
    assert calls[0][4] == "InspireShort" and calls[1][4] == "InspireCover"
    assert "profile" not in json.loads((proj / "props.json").read_text())


def test_platforms_sharing_a_profile_render_once(run):
    rc, calls, _ = run("--platform", "wechat_channels,douyin,rednote,bilibili")
    assert rc == 0
    assert outputs(calls) == [("render", "final/demo/demo.mp4"), ("still", "final/demo/cover.png")]


def test_another_profile_gets_its_own_files_and_props(run):
    rc, calls, proj = run("--platform", "douyin,linkedin,facebook")
    assert rc == 0
    assert outputs(calls) == [
        ("render", "final/demo/demo.mp4"), ("still", "final/demo/cover.png"),
        ("render", "final/demo/demo-portrait-4x5.mp4"), ("still", "final/demo/cover-portrait-4x5.png")]
    props = json.loads((proj / "props-portrait-4x5.json").read_text())
    assert props["profile"]["id"] == "portrait-4x5" and (props["profile"]["width"], props["profile"]["height"]) == (1080, 1350)
    assert "profile" not in json.loads((proj / "props.json").read_text())
    cover_props = json.loads((proj / "cover_props-portrait-4x5.json").read_text())
    assert cover_props["profile"]["height"] == 1350
    assert any(a == f"--props={proj / 'props-portrait-4x5.json'}" for a in calls[2])


def test_an_unsupported_profile_falls_back_with_a_visible_warning(run, capsys):
    rc, calls, _ = run("--profile", "square-1x1")
    assert rc == 0
    assert outputs(calls) == [("render", "final/demo/demo-portrait-4x5.mp4"), ("still", "final/demo/cover-portrait-4x5.png")]
    err = capsys.readouterr().err
    assert "square-1x1" in err and "portrait-4x5" in err


def test_preview_and_cover_only_respect_the_profile(run):
    rc, calls, proj = run("--platform", "linkedin", "--preview")
    assert rc == 0 and len(calls) == 1
    assert calls[0][5] == str(proj / "preview-portrait-4x5.mp4") and "--scale=0.5" in calls[0]
    calls.clear()
    rc, calls, _ = run("--platform", "linkedin", "--cover")
    assert rc == 0 and outputs(calls) == [("still", "final/demo/cover-portrait-4x5.png")]


def test_an_unknown_platform_is_an_error_that_lists_the_known_ones(run):
    with pytest.raises(platforms.RegistryError, match=r"unknown platform 'tiktok'.*douyin"):
        run("--platform", "tiktok")


def test_a_showcase_project_rejects_the_platform_flag(tmp_path, monkeypatch):
    proj = tmp_path / "showcase"
    proj.mkdir()
    (proj / "video_manifest.json").write_text(json.dumps({"type": "showcase"}))
    monkeypatch.setattr(sys, "argv", ["render.py", str(proj), "--platform", "linkedin"])
    with pytest.raises(SystemExit) as e:
        render.main()
    assert e.value.code == 2


def test_existing_outputs_are_all_reported_before_any_render(run):
    final = run.root / "output/final/demo"
    final.mkdir(parents=True)
    (final / "demo-portrait-4x5.mp4").write_bytes(b"x")
    (final / "cover.png").write_bytes(b"x")
    with pytest.raises(FileExistsError) as e:
        run("--platform", "douyin,linkedin")
    msg = str(e.value)
    assert "demo-portrait-4x5.mp4 exists" in msg and "cover.png exists" in msg
    assert "--force" in msg and "--profile" in msg
    assert "demo.mp4" not in msg.replace("demo-portrait-4x5.mp4", "")
    assert run.calls == []


def test_force_renders_every_format_over_existing_files(run):
    final = run.root / "output/final/demo"
    final.mkdir(parents=True)
    (final / "demo-portrait-4x5.mp4").write_bytes(b"x")
    rc, calls, _ = run("--platform", "douyin,linkedin", "--force")
    assert rc == 0
    assert outputs(calls) == [
        ("render", "final/demo/demo.mp4"), ("still", "final/demo/cover.png"),
        ("render", "final/demo/demo-portrait-4x5.mp4"), ("still", "final/demo/cover-portrait-4x5.png")]
