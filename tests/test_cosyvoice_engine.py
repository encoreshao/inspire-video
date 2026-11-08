import json
import subprocess
from pathlib import Path

import pytest

from showcase import cosyvoice_engine as cv
from showcase import engines, voices


def setup_home(tmp_path):
    home = tmp_path / "cv"
    (home / "venv" / "bin").mkdir(parents=True)
    (home / "venv" / "bin" / "python").write_text("")
    model = home / "repo" / "pretrained_models" / "Fun-CosyVoice3-0.5B"
    model.mkdir(parents=True)
    (model / "llm.pt").write_text("")
    return home


def test_not_set_up_names_the_fix(tmp_path, monkeypatch):
    monkeypatch.setenv("INSPIRE_CV_HOME", str(tmp_path / "nothing"))
    with pytest.raises(engines.EngineUnavailable, match="setup_cosyvoice.sh"):
        cv.CosyVoiceEngine().check()


def test_home_defaults_outside_the_repo(monkeypatch):
    monkeypatch.delenv("INSPIRE_CV_HOME", raising=False)
    assert ".cache/inspire-video/cosyvoice" in str(cv.cv_home())


def test_needs_a_voice(tmp_path, monkeypatch):
    monkeypatch.setenv("INSPIRE_CV_HOME", str(setup_home(tmp_path)))
    with pytest.raises(engines.EngineUnavailable, match="voice"):
        cv.CosyVoiceEngine().synth_batch([engines.Item("hi", "en", tmp_path / "a.wav")], None)


def test_one_subprocess_for_the_whole_batch_with_a_job_file(tmp_path, monkeypatch, make_wav):
    home = setup_home(tmp_path)
    monkeypatch.setenv("INSPIRE_CV_HOME", str(home))
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    voice = voices.create_voice("me", clip, "你好，世界。", root=tmp_path / "v")
    seen = []

    def fake_run(argv, **kw):
        job = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        seen.append((argv, kw, job))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(cv.subprocess, "run", fake_run)
    items = [engines.Item("第一句 -v $(id)", "zh", tmp_path / "a.wav"), engines.Item("two", "en", tmp_path / "b.wav")]
    cv.CosyVoiceEngine().synth_batch(items, voice)
    assert len(seen) == 1
    argv, kw, job = seen[0]
    assert argv[0] == str(home / "venv" / "bin" / "python") and argv[1].endswith("cosyvoice_runner.py")
    assert kw["cwd"] == home / "repo" and kw["env"]["PYTORCH_ENABLE_MPS_FALLBACK"] == "1"
    assert job["prompt_wav"] == str(voice.prompt_wav) and job["prompt_text"] == "你好，世界。" and job["speed"] == 1.0
    assert [i["text"] for i in job["items"]] == ["第一句 -v $(id)", "two"]
    assert [i["out"] for i in job["items"]] == [str(tmp_path / "a.wav"), str(tmp_path / "b.wav")]


def test_registry_returns_the_engine():
    assert engines.get_engine("cosyvoice").name == "cosyvoice"


def test_relative_output_paths_become_absolute_in_the_job(tmp_path, monkeypatch, make_wav):
    # The runner starts in the CosyVoice repo, so a relative path would be written there.
    monkeypatch.setenv("INSPIRE_CV_HOME", str(setup_home(tmp_path)))
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    voice = voices.create_voice("me", clip, "words", root=tmp_path / "v")
    jobs = []
    monkeypatch.setattr(cv.subprocess, "run", lambda argv, **kw: jobs.append(json.loads(Path(argv[2]).read_text(encoding="utf-8"))) or subprocess.CompletedProcess(argv, 0))
    monkeypatch.chdir(tmp_path)
    cv.CosyVoiceEngine().synth_batch([engines.Item("hi", "en", Path("output/projects/p/audio/a.wav"))], voice)
    out = jobs[0]["items"][0]["out"]
    assert Path(out).is_absolute() and out == str((tmp_path / "output/projects/p/audio/a.wav").resolve())


def _capture_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("INSPIRE_CV_HOME", str(setup_home(tmp_path)))
    jobs = []
    monkeypatch.setattr(cv.subprocess, "run", lambda argv, **kw: jobs.append(json.loads(Path(argv[2]).read_text(encoding="utf-8"))) or subprocess.CompletedProcess(argv, 0))
    return jobs


def test_default_delivery_is_an_instruction_per_item(tmp_path, monkeypatch, make_wav):
    jobs = _capture_jobs(tmp_path, monkeypatch)
    voice = voices.create_voice("me", make_wav(tmp_path / "in.wav", seconds=12), "words", root=tmp_path / "v")
    cv.CosyVoiceEngine().synth_batch([engines.Item("你好", "zh", tmp_path / "a.wav"), engines.Item("hi", "en", tmp_path / "b.wav")], voice)
    for it in jobs[0]["items"]:
        assert it["instruct"].startswith("You are a helpful assistant. ") and it["instruct"].endswith("<|endofprompt|>")
        assert it["instruct"].count("<|endofprompt|>") == 1


def test_voice_style_replaces_the_default_instruction(tmp_path, monkeypatch, make_wav):
    jobs = _capture_jobs(tmp_path, monkeypatch)
    voice = voices.create_voice("me", make_wav(tmp_path / "in.wav", seconds=12), "words", root=tmp_path / "v")
    voice = voices.VoiceProfile(**{**voice.__dict__, "style": "Speak calmly.<|endofprompt|>"})
    cv.CosyVoiceEngine().synth_batch([engines.Item("hi", "en", tmp_path / "b.wav")], voice)
    assert jobs[0]["items"][0]["instruct"] == "You are a helpful assistant. Speak calmly.<|endofprompt|>"


def test_zero_shot_delivery_sends_no_instruction(tmp_path, monkeypatch, make_wav):
    jobs = _capture_jobs(tmp_path, monkeypatch)
    voice = voices.create_voice("me", make_wav(tmp_path / "in.wav", seconds=12), "words", root=tmp_path / "v")
    voice = voices.VoiceProfile(**{**voice.__dict__, "delivery": "zero_shot"})
    cv.CosyVoiceEngine().synth_batch([engines.Item("hi", "en", tmp_path / "b.wav")], voice)
    assert "instruct" not in jobs[0]["items"][0]


def test_version_tracks_the_default_instructions(monkeypatch):
    before = cv.CosyVoiceEngine.version
    assert "instruct-" in before and "polish" in before
    import hashlib
    changed = {**cv.DEFAULT_STYLES, "zh": "别的语气。"}
    assert hashlib.sha256(json.dumps(changed, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:8] not in before


def test_synthesized_clips_are_polished_in_place(tmp_path, monkeypatch, make_wav):
    import array, math, wave
    monkeypatch.setenv("INSPIRE_CV_HOME", str(setup_home(tmp_path)))
    voice = voices.create_voice("me", make_wav(tmp_path / "in.wav", seconds=12), "words", root=tmp_path / "v")
    out = tmp_path / "a.wav"

    def fake_run(argv, **kw):
        job = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        s = array.array("h", [0] * 24000 + [int(3000 * math.sin(i / 5)) for i in range(24000)] + [0] * 24000)
        with wave.open(job["items"][0]["out"], "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(s.tobytes())
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(cv.subprocess, "run", fake_run)
    cv.CosyVoiceEngine().synth_batch([engines.Item("hi", "en", out)], voice)
    with wave.open(str(out)) as w:
        assert w.getframerate() == 24000 and w.getnchannels() == 1 and w.getsampwidth() == 2
        assert 0.9 < w.getnframes() / 24000 < 1.3          # about 1 s of tone plus the small kept margins
