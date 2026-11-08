import json
import subprocess
from pathlib import Path

import pytest

from imgs import png
from showcase import manifest as M
from showcase import render_showcase as R

BEATS = [("hook", "Make videos from any website."), ("problem", "Screenshots alone do not tell the story."),
         ("what", "It reads the site and writes the beats."), ("cta", "Try it on your own project.")]


def project(tmp_path, with_timings=False, rights_unresolved=False, voice=None):
    p = tmp_path / "proj"
    (p / "assets").mkdir(parents=True)
    beats = []
    for i, (bid, en) in enumerate(BEATS):
        (p / "assets" / f"{i}.png").write_bytes(png(1440, 900) if i % 2 == 0 else png(390, 844))
        beats.append({"id": bid, "en": en, "zh": "这是一句中文。", "asset": f"assets/{i}.png",
                      "focus": {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.4}, "callout": "Look here"})
    m = {"type": "showcase", "project_id": "acme-demo", "style": "device", "theme": "mist",
         "headline": "任何网站都能变成短视频", "subtitle": "Turn any site into a short video", "category": "SHOWCASE",
         "project": {"name": "Acme", "name_zh": "极致", "tagline": "Widgets", "tagline_zh": "小工具"},
         "source": {"kind": "website", "url": "https://example.com/", "label": "example.com"},
         "beats": beats, "provenance": {"rights_confirmed": True, "source_reference": "https://example.com/"}}
    if voice:
        m["voice"] = voice
    (p / "video_manifest.json").write_text(json.dumps(m, ensure_ascii=False))
    if with_timings:
        secs = (12.0, 11.0, 10.0, 9.0)
        (p / "audio").mkdir()
        for b in beats:
            (p / "audio" / f"{b['id']}.wav").write_bytes(b"RIFF")
        (p / "timings.json").write_text(json.dumps({"engine": "say", "voice": voice, "lang": "en", "total": sum(secs), "beats": [
            {"id": b["id"], "audio": f"audio/{b['id']}.wav", "audio_seconds": s - 0.4, "seconds": s} for b, s in zip(beats, secs)]}))
    if rights_unresolved:
        (p / "brief.json").write_text(json.dumps({"rights_unresolved": True}))
    return p, m


class FakeRun:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def __call__(self, argv, **kw):
        self.calls.append((list(argv), kw))
        if self.fail:
            return subprocess.CompletedProcess(argv, 1)
        out = Path(argv[5])                                  # remotion render|still src/index.ts <comp> <out>
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"x")
        return subprocess.CompletedProcess(argv, 0)


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    root = tmp_path / "root"
    (root / "video" / "public").mkdir(parents=True)
    monkeypatch.setattr(R, "ROOT", root)
    monkeypatch.setattr(R, "check_video", lambda *a, **k: [])
    return root


def test_stage_copies_assets_and_audio_with_the_project_prefix(tmp_path, sandbox):
    p, m = project(tmp_path, with_timings=True)
    t = json.loads((p / "timings.json").read_text())
    staged = R.stage(p, sandbox / "video" / "public", m, t)
    assert staged["hook"] == {"asset": "acme-demo-hook.png", "audio": "acme-demo-hook.wav"}
    assert all((sandbox / "video" / "public" / v).exists() for s in staged.values() for v in s.values() if v)
    no_audio = R.stage(p, sandbox / "video" / "public", m, None)
    assert all(s["audio"] is None for s in no_audio.values())


def test_build_props_uses_timings_frames_and_the_staged_names(tmp_path, sandbox):
    p, m = project(tmp_path, with_timings=True)
    t = json.loads((p / "timings.json").read_text())
    staged = R.stage(p, sandbox / "video" / "public", m, t)
    props = R.build_props(m, p, t, staged)
    assert props["theme"] == "mist" and props["name"] == "Acme" and props["nameZh"] == "极致" and props["sourceLabel"] == "example.com"
    b0, b1 = props["beats"][0], props["beats"][1]
    assert (b0["startFrame"], b0["frames"]) == (0, 360) and b1["startFrame"] == 360
    assert (b0["iw"], b0["ih"]) == (1440, 900) and (b1["iw"], b1["ih"]) == (390, 844)
    assert b0["asset"] == "acme-demo-hook.png" and b0["audio"] == "acme-demo-hook.wav" and b0["callout"] == "Look here"
    assert props["durationSeconds"] == 42.0
    cover = R.cover_props(props)
    assert cover["beat"] == props["beats"][0] and "beats" not in cover and cover["headline"] == props["headline"]


def test_without_timings_the_default_length_is_used(tmp_path, sandbox):
    p, m = project(tmp_path)
    props = R.build_props(m, p, None, R.stage(p, sandbox / "video" / "public", m, None))
    assert props["durationSeconds"] == 40.0 and props["beats"][0]["frames"] == 300 and props["beats"][0]["audio"] is None


def test_final_render_writes_the_video_then_the_cover_and_checks_it(tmp_path, sandbox, monkeypatch):
    p, _ = project(tmp_path, with_timings=True)
    run = FakeRun()
    seen = {}
    monkeypatch.setattr(R, "check_video", lambda path, scale=1.0, duration_range=None, run=None: seen.update(path=path, scale=scale, rng=duration_range) or [])
    assert R.main([str(p)], run=run) == 0
    final = sandbox / "output" / "final" / "acme-demo"
    assert (final / "acme-demo.mp4").exists() and (final / "cover.png").exists()
    kinds = [c[0][2:4] for c in run.calls]
    assert kinds == [["render", "src/index.ts"], ["still", "src/index.ts"]]
    assert run.calls[0][0][4] == "ShowcaseShort" and run.calls[1][0][4] == "ShowcaseCover"
    assert seen["scale"] == 1.0 and seen["rng"] == (40, 150) and (p / "props.json").exists()
    assert run.calls[0][1]["cwd"] == sandbox / "video"


def test_an_existing_final_needs_force(tmp_path, sandbox):
    p, _ = project(tmp_path, with_timings=True)
    assert R.main([str(p)], run=FakeRun()) == 0
    assert R.main([str(p)], run=FakeRun()) == 1
    assert R.main([str(p), "--force"], run=FakeRun()) == 0


def test_preview_is_half_scale_goes_into_the_project_and_skips_the_cover(tmp_path, sandbox, monkeypatch):
    p, _ = project(tmp_path, with_timings=True)
    run = FakeRun()
    seen = {}
    monkeypatch.setattr(R, "check_video", lambda path, scale=1.0, duration_range=None, run=None: seen.update(scale=scale, rng=duration_range) or [])
    assert R.main([str(p), "--preview"], run=run) == 0
    assert (p / "preview.mp4").exists() and len(run.calls) == 1 and "--scale=0.5" in run.calls[0][0]
    assert seen == {"scale": 0.5, "rng": None}


def test_cover_only(tmp_path, sandbox):
    p, _ = project(tmp_path, with_timings=True)
    run = FakeRun()
    assert R.main([str(p), "--cover"], run=run) == 0
    assert len(run.calls) == 1 and run.calls[0][0][2] == "still"


def test_unresolved_rights_block_a_final_render_but_not_a_preview(tmp_path, sandbox, capsys):
    p, _ = project(tmp_path, with_timings=True, rights_unresolved=True)
    run = FakeRun()
    assert R.main([str(p)], run=run) == 1 and run.calls == []
    assert "allow-unresolved-rights" in capsys.readouterr().err
    assert R.main([str(p), "--preview"], run=FakeRun()) == 0
    assert R.main([str(p), "--allow-unresolved-rights"], run=FakeRun()) == 0


def test_a_problem_found_by_the_checks_fails_the_run_but_keeps_the_file(tmp_path, sandbox, monkeypatch, capsys):
    p, _ = project(tmp_path, with_timings=True)
    monkeypatch.setattr(R, "check_video", lambda *a, **k: ["content below y = 1590 (first seen at 3.0 s)"])
    assert R.main([str(p)], run=FakeRun()) == 3
    assert "CHECK FAILED" in capsys.readouterr().out
    assert (sandbox / "output" / "final" / "acme-demo" / "acme-demo.mp4").exists()
    assert R.main([str(p), "--force", "--no-check"], run=FakeRun()) == 0


def test_a_failed_remotion_run_is_reported(tmp_path, sandbox):
    p, _ = project(tmp_path, with_timings=True)
    assert R.main([str(p)], run=FakeRun(fail=True)) == 1


def test_a_voice_without_timings_and_an_invalid_manifest_stop_before_rendering(tmp_path, sandbox, capsys):
    p, _ = project(tmp_path, voice="encore")
    run = FakeRun()
    assert R.main([str(p)], run=run) == 1 and run.calls == [] and "narrate" in capsys.readouterr().err


def test_render_py_delegates_showcase_projects(tmp_path, monkeypatch):
    import render
    p, _ = project(tmp_path)
    called = []
    monkeypatch.setattr(R, "main", lambda argv=None, run=None: called.append(argv) or 7)
    monkeypatch.setattr("sys.argv", ["render.py", str(p), "--preview"])
    assert render.main() == 7 and called == [[str(p), "--preview"]]


def test_render_py_passes_the_showcase_flags_through(tmp_path, monkeypatch):
    import render
    p, _ = project(tmp_path)
    called = []
    monkeypatch.setattr(R, "main", lambda argv=None, run=None: called.append(argv) or 0)
    monkeypatch.setattr("sys.argv", ["render.py", "--theme", "ink", str(p), "--allow-unresolved-rights", "--no-check"])
    assert render.main() == 0
    assert called == [["--theme", "ink", str(p), "--allow-unresolved-rights", "--no-check"]]


def test_a_narrated_beat_without_its_wav_is_an_error(tmp_path, sandbox):
    p, m = project(tmp_path, with_timings=True)
    (p / "audio" / "hook.wav").unlink()
    t = json.loads((p / "timings.json").read_text())
    with pytest.raises(M.ManifestError, match="hook"):
        R.stage(p, sandbox / "video" / "public", m, t)


def test_malformed_timings_give_a_message_not_a_traceback(tmp_path, sandbox, capsys):
    p, m = project(tmp_path)
    (p / "timings.json").write_text(json.dumps({"beats": [{"id": b["id"]} for b in m["beats"]]}))
    assert R.main([str(p)], run=FakeRun()) == 1
    assert "error:" in capsys.readouterr().err


def test_an_existing_cover_is_noticed_before_the_long_render(tmp_path, sandbox, capsys):
    p, _ = project(tmp_path, with_timings=True)
    cover = sandbox / "output" / "final" / "acme-demo" / "cover.png"
    cover.parent.mkdir(parents=True)
    cover.write_bytes(b"x")
    run = FakeRun()
    assert R.main([str(p)], run=run) == 1 and run.calls == []
    assert "cover.png" in capsys.readouterr().err


def test_a_missing_npx_is_reported(tmp_path, sandbox, capsys):
    p, _ = project(tmp_path, with_timings=True)

    def boom(argv, **kw):
        raise FileNotFoundError("npx")

    assert R.main([str(p)], run=boom) == 1
    assert "npx" in capsys.readouterr().err


def test_crop_warnings_are_printed_at_render_time(tmp_path, sandbox, capsys):
    p, _ = project(tmp_path, with_timings=True)
    (p / "assets" / "0.png").write_bytes(png(1000, 1000))
    assert R.main([str(p), "--preview"], run=FakeRun()) == 0
    err = capsys.readouterr().err
    assert "warning:" in err and "cropped" in err


def test_build_props_adds_chinese_break_units_unless_disabled(tmp_path, sandbox):
    p, m = project(tmp_path)
    staged = R.stage(p, sandbox / "video" / "public", m, None)
    on = R.build_props(m, p, None, staged)["beats"][0]
    assert "".join(on["zhUnits"]) == on["zh"]
    assert "zhUnits" not in R.build_props(m, p, None, staged, zh_breaks=False)["beats"][0]


def test_promo_props_carry_the_shot_target_page_and_scale(tmp_path, sandbox):
    from promo_fixtures import promo_project
    p, m = promo_project(tmp_path)
    props = R.build_props(m, p, None, R.stage(p, sandbox / "video" / "public", m, None))
    b0, b1 = props["beats"][0], props["beats"][1]
    assert (b0["shot"], b1["shot"]) == ("hero-push", "spotlight-focus")
    assert b0["box"] == {"x": 100, "y": 100, "w": 600, "h": 80}
    assert b0["page"] == {"w": 1440, "h": 1500} and b0["imageScale"] == 2
    assert (b0["iw"], b0["ih"]) == (2880, 3000) and b0["asset"] == "acme-promo-hook.png"


def test_a_promo_beat_without_a_layout_uses_the_image_as_the_page(tmp_path, sandbox):
    from promo_fixtures import promo_project
    p, m = promo_project(tmp_path)
    (p / "assets" / "shot.png").write_bytes(png(1440, 900))
    beat = {k: v for k, v in m["beats"][0].items() if k != "target"}
    m["beats"][0] = {**beat, "asset": "assets/shot.png", "focus": {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.4}}
    b0 = R.build_props(m, p, None, R.stage(p, sandbox / "video" / "public", m, None))["beats"][0]
    assert b0["page"] == {"w": 1440, "h": 900} and b0["imageScale"] == 1
    assert b0["box"] == {"x": 144, "y": 90, "w": 720, "h": 360}


def test_device_props_are_unchanged_by_the_promo_fields(tmp_path, sandbox):
    p, m = project(tmp_path)
    b0 = R.build_props(m, p, None, R.stage(p, sandbox / "video" / "public", m, None))["beats"][0]
    assert not {"shot", "box", "page", "imageScale"} & set(b0)


def test_the_composition_follows_the_style(tmp_path, sandbox):
    from promo_fixtures import promo_project
    device, _ = project(tmp_path / "d")
    fake = FakeRun()
    assert R.main([str(device), "--preview"], run=fake) == 0
    assert fake.calls[0][0][4] == "ShowcaseShort"
    promo, _ = promo_project(tmp_path / "p")
    fake = FakeRun()
    assert R.main([str(promo), "--preview"], run=fake) == 0
    assert fake.calls[0][0][4] == "ShowcasePromo"


def test_promo_props_tell_the_composition_how_many_subtitle_lines_there_are(tmp_path, sandbox):
    from promo_fixtures import promo_project
    p, m = promo_project(tmp_path)
    staged = R.stage(p, sandbox / "video" / "public", m, None)
    assert R.build_props(m, p, None, staged)["subtitleLines"] == 1
    m["subtitle"] = "A local-first AI agent app that runs AI agents on a schedule"
    assert R.build_props(m, p, None, staged)["subtitleLines"] == 2


def test_device_props_have_no_subtitle_lines(tmp_path, sandbox):
    p, m = project(tmp_path)
    assert "subtitleLines" not in R.build_props(m, p, None, R.stage(p, sandbox / "video" / "public", m, None))


def test_a_statement_beat_needs_no_capture_and_carries_its_text_in_units(tmp_path, sandbox):
    from promo_fixtures import promo_project
    p, m = promo_project(tmp_path)
    keep = {k: v for k, v in m["beats"][0].items() if k not in ("asset", "target", "focus")}
    m["beats"][0] = {**keep, "shot": "statement", "statement": "Calm work, done for you."}
    staged = R.stage(p, sandbox / "video" / "public", m, None)
    assert staged["hook"] == {"asset": None, "audio": None} and staged["problem"]["asset"] == "acme-promo-problem.png"
    b0 = R.build_props(m, p, None, staged)["beats"][0]
    assert b0["shot"] == "statement" and b0["statement"] == "Calm work, done for you." and b0["asset"] == ""
    assert b0["statementUnits"] == ["Calm ", "work, ", "done ", "for ", "you."]
    assert not {"box", "page", "imageScale"} & set(b0) and (b0["iw"], b0["ih"]) == (0, 0)
    m["beats"][0]["statement"] = "琐事交给 LoopX，你专注真正的工作"
    units = R.build_props(m, p, None, staged)["beats"][0]["statementUnits"]
    assert "".join(units) == "琐事交给 LoopX，你专注真正的工作" and "交给 " in units
