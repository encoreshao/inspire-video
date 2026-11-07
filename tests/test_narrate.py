import json

import pytest

from fakes import FakeEngine
from showcase import narrate, timing, voices

LO, HI = 0.5, 100.0


def project(tmp_path, beats, **extra):
    p = tmp_path / "proj"
    p.mkdir(exist_ok=True)
    (p / "video_manifest.json").write_text(json.dumps({"beats": beats, **extra}, ensure_ascii=False), encoding="utf-8")
    return p


def run(p, engine, **kw):
    return narrate.narrate(p, engine, min_total=kw.pop("min_total", LO), max_total=kw.pop("max_total", HI), **kw)


BEATS = [{"id": "hook", "en": "Hello there", "zh": "你好"},
         {"id": "end", "en": "Bye now", "zh": "再见"}]


def test_writes_audio_and_timings(tmp_path):
    p = project(tmp_path, BEATS)
    t = run(p, FakeEngine())
    assert (p / "audio" / "hook.wav").exists() and (p / "audio" / "end.wav").exists()
    hook = t["beats"][0]
    assert hook["id"] == "hook" and hook["audio"] == "audio/hook.wav"
    assert hook["audio_seconds"] == 1.1 and hook["seconds"] == 1.5     # 11 chars * 0.1 s, + 0.4
    assert t["total"] == round(1.5 + 1.1, 2) and t["lang"] == "en" and t["engine"] == "fake" and t["voice"] is None
    assert json.loads((p / "timings.json").read_text()) == t


def test_second_run_uses_the_cache(tmp_path):
    p = project(tmp_path, BEATS)
    e = FakeEngine()
    run(p, e)
    run(p, e)
    assert e.calls == 1


def test_only_the_edited_beat_is_regenerated(tmp_path):
    p = project(tmp_path, BEATS)
    e = FakeEngine()
    run(p, e)
    project(tmp_path, [BEATS[0], {"id": "end", "en": "Goodbye for now", "zh": "再见"}])
    run(p, e)
    assert e.texts == ["Hello there", "Bye now", "Goodbye for now"]


def test_replacing_the_voice_clip_regenerates(tmp_path, make_wav):
    clip = make_wav(tmp_path / "a.wav", seconds=5)
    v1 = voices.create_voice("me", clip, "words", root=tmp_path / "v")
    p = project(tmp_path, BEATS)
    e = FakeEngine(needs_voice=True)
    run(p, e, voice=v1)
    make_wav(tmp_path / "b.wav", seconds=9)
    v2 = voices.create_voice("me", tmp_path / "b.wav", "words", overwrite=True, root=tmp_path / "v")
    run(p, e, voice=v2)
    assert e.calls == 2


def test_chinese_and_mixed_text_pass_through_unchanged(tmp_path):
    mixed = "拖延不是懒惰。Procrastination isn't laziness."
    p = project(tmp_path, [{"id": "a", "en": "x", "zh": mixed}], narration_lang="zh")
    e = FakeEngine()
    t = run(p, e)
    assert e.texts == [mixed] and t["lang"] == "zh"


def test_lang_argument_overrides_the_manifest(tmp_path):
    p = project(tmp_path, BEATS, narration_lang="zh")
    e = FakeEngine()
    run(p, e, lang="en")
    assert e.texts[0] == "Hello there"


@pytest.mark.parametrize("bad", ["../evil", "a/b", "", "A", ".hidden", "x" * 49])
def test_bad_beat_ids_are_rejected_before_any_file_is_written(tmp_path, bad):
    p = project(tmp_path, [{"id": bad, "en": "hello"}])
    with pytest.raises(narrate.NarrationError, match="beat id"):
        run(p, FakeEngine())
    assert not (tmp_path / "evil.wav").exists()
    assert not any(tmp_path.rglob("*.wav"))


def test_duplicate_ids_zero_beats_and_empty_text_name_the_problem(tmp_path):
    with pytest.raises(narrate.NarrationError, match="duplicate"):
        run(project(tmp_path, [{"id": "a", "en": "x"}, {"id": "a", "en": "y"}]), FakeEngine())
    with pytest.raises(narrate.NarrationError, match="no beats"):
        run(project(tmp_path, []), FakeEngine())
    with pytest.raises(narrate.NarrationError, match="'b'.*zh"):
        run(project(tmp_path, [{"id": "b", "en": "x", "zh": "  "}], narration_lang="zh"), FakeEngine())


def test_missing_manifest_is_a_clear_error(tmp_path):
    with pytest.raises(narrate.NarrationError, match="video_manifest.json"):
        run(tmp_path, FakeEngine())


def test_engine_that_needs_a_voice_refuses_without_one(tmp_path):
    with pytest.raises(narrate.NarrationError, match="--voice"):
        run(project(tmp_path, BEATS), FakeEngine(needs_voice=True))


def test_too_long_fails_and_leaves_no_timings(tmp_path):
    p = project(tmp_path, BEATS)
    (p / "timings.json").write_text("{}")             # stale file from an earlier run
    with pytest.raises(timing.LengthError, match="shorten"):
        run(p, FakeEngine(), max_total=1.0)
    assert not (p / "timings.json").exists()


def test_engine_crash_leaves_no_timings_and_no_valid_cache(tmp_path):
    p = project(tmp_path, BEATS)
    with pytest.raises(RuntimeError, match="boom"):
        run(p, FakeEngine(fail_on="Bye"))
    assert not (p / "timings.json").exists()
    assert not list((p / "audio").glob("*.key"))
    e = FakeEngine()
    run(p, e)                                           # recovers: everything regenerated
    assert e.texts == ["Hello there", "Bye now"]


def test_engine_that_writes_nothing_is_an_error(tmp_path):
    with pytest.raises(RuntimeError, match="no audio"):
        run(project(tmp_path, BEATS), FakeEngine(skip=True))


def test_cli_reports_errors_and_success(tmp_path, capsys, monkeypatch):
    p = project(tmp_path, BEATS)
    monkeypatch.setattr(narrate.engines, "get_engine", lambda n: FakeEngine())
    monkeypatch.setattr(narrate, "MIN_TOTAL", LO)
    monkeypatch.setattr(narrate, "MAX_TOTAL", HI)
    assert narrate.main([str(p), "--engine", "say"]) == 0
    assert "2 beats" in capsys.readouterr().out
    assert narrate.main([str(tmp_path / "missing")]) == 1
    assert "error:" in capsys.readouterr().err


@pytest.mark.parametrize("scenario", ["duplicate-ids", "needs-voice", "no-manifest"])
def test_a_stale_timings_file_never_survives_a_failed_run(tmp_path, scenario):
    if scenario == "duplicate-ids":
        p, engine = project(tmp_path, [{"id": "a", "en": "x"}, {"id": "a", "en": "y"}]), FakeEngine()
    elif scenario == "needs-voice":
        p, engine = project(tmp_path, BEATS), FakeEngine(needs_voice=True)
    else:
        p, engine = tmp_path, FakeEngine()
    (p / "timings.json").write_text("{}")
    with pytest.raises(narrate.NarrationError):
        run(p, engine)
    assert not (p / "timings.json").exists()


def test_beat_id_with_a_trailing_newline_is_rejected(tmp_path):
    with pytest.raises(narrate.NarrationError, match="beat id"):
        run(project(tmp_path, [{"id": "intro\n", "en": "hello"}]), FakeEngine())
    assert not any(tmp_path.rglob("*.wav"))


@pytest.mark.parametrize("beats", ["oops", ["intro"], [{"id": "a", "en": "x"}, 3]])
def test_malformed_beats_are_a_clear_error(tmp_path, beats):
    with pytest.raises(narrate.NarrationError, match="list of beat objects"):
        run(project(tmp_path, beats), FakeEngine())


def test_voice_language_is_the_default_narration_language(tmp_path, make_wav):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    zh_voice = voices.create_voice("me", clip, "你好", language="zh", root=tmp_path / "v")
    e = FakeEngine(needs_voice=True)
    t = run(project(tmp_path, BEATS), e, voice=zh_voice)          # manifest has no narration_lang
    assert t["lang"] == "zh" and e.texts == ["你好", "再见"]


def test_voice_profile_with_an_engine_that_cannot_use_it_is_refused(tmp_path, make_wav):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    v = voices.create_voice("me", clip, "words", root=tmp_path / "v")
    with pytest.raises(narrate.NarrationError, match="does not use voice profiles"):
        run(project(tmp_path, BEATS), FakeEngine(), voice=v)


def _cli_setup(tmp_path, monkeypatch, make_wav, **extra):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    voices.create_voice("me", clip, "words", root=tmp_path / "v")
    voices.create_voice("other", clip, "words", root=tmp_path / "v")
    p = project(tmp_path, BEATS, **extra)
    monkeypatch.setattr(narrate.engines, "get_engine", lambda n: FakeEngine(needs_voice=True))
    monkeypatch.setattr(narrate, "load_voice", lambda n: voices.load_voice(n, root=tmp_path / "v"))
    monkeypatch.setattr(narrate, "MIN_TOTAL", LO)
    monkeypatch.setattr(narrate, "MAX_TOTAL", HI)
    return p


def test_cli_uses_the_manifest_voice_and_the_flag_overrides_it(tmp_path, monkeypatch, make_wav):
    p = _cli_setup(tmp_path, monkeypatch, make_wav, voice="me", narration_lang="en")
    assert narrate.main([str(p), "--engine", "cosyvoice"]) == 0
    assert json.loads((p / "timings.json").read_text())["voice"] == "me"
    assert narrate.main([str(p), "--engine", "cosyvoice", "--voice", "other"]) == 0
    assert json.loads((p / "timings.json").read_text())["voice"] == "other"


class JunkWavEngine(FakeEngine):
    def synth_batch(self, items, voice):
        for it in items:
            it.out.parent.mkdir(parents=True, exist_ok=True)
            it.out.write_bytes(b"not a wav")


class CrashingEngine(FakeEngine):
    def synth_batch(self, items, voice):
        import subprocess
        raise subprocess.CalledProcessError(3, ["say"])


@pytest.mark.parametrize("engine_cls, needle", [(JunkWavEngine, "error:"), (CrashingEngine, "say engine failed")])
def test_cli_turns_engine_failures_into_a_message_not_a_traceback(tmp_path, capsys, monkeypatch, engine_cls, needle):
    p = project(tmp_path, BEATS)
    monkeypatch.setattr(narrate.engines, "get_engine", lambda n: engine_cls())
    assert narrate.main([str(p), "--engine", "say"]) == 1
    assert needle in capsys.readouterr().err


def test_short_narration_is_held_long_enough_to_reach_the_minimum_total(tmp_path):
    # Two 11-character beats narrate to 1.1 s each (+0.4 s), but the total must reach min_total:
    # each beat is held for at least min_total / number_of_beats seconds. The audio itself is not stretched.
    p = project(tmp_path, [{"id": "a", "en": "Hello there"}, {"id": "b", "en": "Hello there"}])
    t = run(p, FakeEngine(), min_total=10.0)
    assert [b["seconds"] for b in t["beats"]] == [5.0, 5.0] and t["total"] == 10.0
    assert [b["audio_seconds"] for b in t["beats"]] == [1.1, 1.1]


def test_the_hold_floor_never_rounds_below_the_minimum(tmp_path):
    p = project(tmp_path, [{"id": f"b{i}", "en": "Hi"} for i in range(3)])
    t = run(p, FakeEngine(), min_total=40.0)
    assert t["total"] >= 40.0 and all(b["seconds"] >= 13.33 for b in t["beats"])


def test_long_narration_is_not_shortened_by_the_floor(tmp_path):
    p = project(tmp_path, [{"id": "a", "en": "x" * 100}, {"id": "b", "en": "x" * 100}])
    t = run(p, FakeEngine(), min_total=5.0)
    assert [b["seconds"] for b in t["beats"]] == [10.4, 10.4]
