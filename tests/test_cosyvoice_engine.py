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
