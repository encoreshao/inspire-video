import subprocess
from pathlib import Path

import pytest

from showcase import engines, timing

NASTY = "x\"; rm -rf ~ $(id) `id` -v Alex\nsecond line"


def test_registry_lists_names_in_the_error():
    with pytest.raises(engines.EngineUnavailable) as e:
        engines.get_engine("nope")
    assert "say" in str(e.value) and "kokoro" in str(e.value)
    assert engines.get_engine("say").name == "say"


def test_say_needs_macos_tools(monkeypatch):
    monkeypatch.setattr(engines.shutil, "which", lambda t: None)
    with pytest.raises(engines.EngineUnavailable, match="macOS"):
        engines.SayEngine().check()


def test_say_passes_text_on_stdin_never_in_argv(monkeypatch, tmp_path):
    monkeypatch.setattr(engines.shutil, "which", lambda t: "/usr/bin/" + t)
    calls = []

    def fake_run(argv, **kw):
        calls.append((argv, kw))
        if argv[0] == "afconvert":
            Path(argv[-1]).write_bytes(b"RIFF")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(engines.subprocess, "run", fake_run)
    out = tmp_path / "audio" / "a.wav"
    engines.SayEngine().synth_batch([engines.Item(NASTY, "en", out)], None)
    say_argv, say_kw = calls[0]
    assert say_argv[0] == "say" and "Samantha" in say_argv
    assert say_argv[-2:] == ["-f", "-"]
    assert all(NASTY not in a and "rm -rf" not in a for a in say_argv)
    assert say_kw["input"] == NASTY.encode("utf-8")
    assert calls[1][0][0] == "afconvert" and calls[1][0][-1] == str(out)


def test_say_picks_a_chinese_voice(monkeypatch, tmp_path):
    monkeypatch.setattr(engines.shutil, "which", lambda t: "/usr/bin/" + t)
    seen = []
    monkeypatch.setattr(engines.subprocess, "run", lambda argv, **kw: seen.append(argv) or subprocess.CompletedProcess(argv, 0))
    engines.SayEngine().synth_batch([engines.Item("你好", "zh", tmp_path / "a.wav")], None)
    assert "Tingting" in seen[0]


def test_kokoro_needs_mlx_audio(monkeypatch):
    monkeypatch.setattr(engines.importlib.util, "find_spec", lambda n: None)
    with pytest.raises(engines.EngineUnavailable, match="mlx-audio"):
        engines.KokoroEngine().check()


def test_kokoro_needs_espeak(monkeypatch, tmp_path):
    monkeypatch.setattr(engines.importlib.util, "find_spec", lambda n: object())
    monkeypatch.setattr(engines, "ESPEAK_LIB", str(tmp_path / "missing.dylib"))
    with pytest.raises(engines.EngineUnavailable, match="espeak-ng"):
        engines.KokoroEngine().check()


def test_kokoro_text_is_one_argument_and_chunks_are_joined(monkeypatch, tmp_path, make_wav):
    lib = tmp_path / "lib.dylib"
    lib.write_bytes(b"")
    monkeypatch.setattr(engines, "ESPEAK_LIB", str(lib))
    monkeypatch.setattr(engines, "ESPEAK_DATA", str(tmp_path))
    monkeypatch.setattr(engines.importlib.util, "find_spec", lambda n: object())
    seen = {}

    def fake_run(argv, **kw):
        seen["argv"], seen["env"] = argv, kw["env"]
        cwd = Path(kw["cwd"])
        make_wav(cwd / "o_000.wav", seconds=1, rate=24000)
        make_wav(cwd / "o_001.wav", seconds=2, rate=24000)
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(engines.subprocess, "run", fake_run)
    out = tmp_path / "a.wav"
    engines.KokoroEngine().synth_batch([engines.Item("-v " + NASTY, "en", out)], None)
    assert f"--text=-v {NASTY}" in seen["argv"]
    assert seen["env"]["PHONEMIZER_ESPEAK_LIBRARY"] == str(lib)
    assert timing.wav_seconds(out) == 3.0


def test_kokoro_fails_loudly_when_no_audio_appears(monkeypatch, tmp_path):
    lib = tmp_path / "lib.dylib"
    lib.write_bytes(b"")
    monkeypatch.setattr(engines, "ESPEAK_LIB", str(lib))
    monkeypatch.setattr(engines, "ESPEAK_DATA", str(tmp_path))
    monkeypatch.setattr(engines.importlib.util, "find_spec", lambda n: object())
    monkeypatch.setattr(engines.subprocess, "run", lambda argv, **kw: subprocess.CompletedProcess(argv, 0))
    with pytest.raises(RuntimeError, match="no audio"):
        engines.KokoroEngine().synth_batch([engines.Item("hi", "en", tmp_path / "a.wav")], None)


def test_concat_joins_and_rejects_mismatched_formats(tmp_path, make_wav):
    a = make_wav(tmp_path / "a.wav", seconds=1, rate=24000)
    b = make_wav(tmp_path / "b.wav", seconds=2, rate=24000)
    engines._concat_wavs([a, b], tmp_path / "ab.wav")
    assert timing.wav_seconds(tmp_path / "ab.wav") == 3.0
    c = make_wav(tmp_path / "c.wav", seconds=1, rate=16000)
    with pytest.raises(ValueError, match="format"):
        engines._concat_wavs([a, c], tmp_path / "ac.wav")
