import pytest

from showcase import voices


def test_create_then_load_round_trip(tmp_path, make_wav):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    p = voices.create_voice("encore", clip, "你好，世界。", root=tmp_path / "v")
    assert p.name == "encore" and p.language == "zh" and p.engine == "cosyvoice" and p.speed == 1.0
    assert p.prompt_text == "你好，世界。"
    assert p.prompt_wav == tmp_path / "v" / "encore" / "prompt.wav" and p.prompt_wav.exists()
    assert voices.load_voice("encore", root=tmp_path / "v") == p


@pytest.mark.parametrize("kwargs, needle", [
    ({"seconds": 12, "rate": 44100}, "16000"),
    ({"seconds": 12, "channels": 2}, "mono"),
    ({"seconds": 1}, "3"),
    ({"seconds": 45}, "30"),
])
def test_bad_clip_is_rejected_with_the_ffmpeg_fix(tmp_path, make_wav, kwargs, needle):
    clip = make_wav(tmp_path / "in.wav", **kwargs)
    with pytest.raises(voices.VoiceError) as e:
        voices.create_voice("encore", clip, "text", root=tmp_path / "v")
    assert needle in str(e.value)
    if "rate" in kwargs or "channels" in kwargs:
        assert "ffmpeg -i" in str(e.value) and "-ar 16000 -ac 1" in str(e.value)
    assert not (tmp_path / "v" / "encore").exists()


def test_non_wav_file_is_rejected_with_the_fix(tmp_path):
    clip = tmp_path / "in.m4a"
    clip.write_bytes(b"not a wav")
    with pytest.raises(voices.VoiceError, match="ffmpeg -i"):
        voices.create_voice("encore", clip, "text", root=tmp_path / "v")


def test_missing_file_is_a_voice_error(tmp_path):
    with pytest.raises(voices.VoiceError):
        voices.create_voice("encore", tmp_path / "nope.wav", "text", root=tmp_path / "v")


@pytest.mark.parametrize("name", ["../x", "A b", "", "-x", "a" * 33, "a/b"])
def test_bad_names_are_rejected(tmp_path, make_wav, name):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    with pytest.raises(voices.VoiceError, match="invalid voice name"):
        voices.create_voice(name, clip, "text", root=tmp_path / "v")


def test_empty_transcript_is_rejected(tmp_path, make_wav):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    with pytest.raises(voices.VoiceError, match="transcript"):
        voices.create_voice("encore", clip, "   ", root=tmp_path / "v")


def test_existing_voice_needs_overwrite(tmp_path, make_wav):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    voices.create_voice("encore", clip, "one", root=tmp_path / "v")
    with pytest.raises(voices.VoiceError, match="already exists"):
        voices.create_voice("encore", clip, "two", root=tmp_path / "v")
    p = voices.create_voice("encore", clip, "two", overwrite=True, root=tmp_path / "v")
    assert p.prompt_text == "two"


def test_loading_a_missing_voice_names_it(tmp_path):
    with pytest.raises(voices.VoiceError, match="encore"):
        voices.load_voice("encore", root=tmp_path / "v")


def test_cli_add_and_list(tmp_path, make_wav, capsys):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    txt = tmp_path / "t.txt"
    txt.write_text("hello there", encoding="utf-8")
    root = str(tmp_path / "v")
    assert voices.main(["--root", root, "add", "--name", "encore", "--wav", str(clip), "--text-file", str(txt), "--lang", "en"]) == 0
    assert voices.main(["--root", root, "list"]) == 0
    assert "encore" in capsys.readouterr().out
    assert voices.main(["--root", root, "add", "--name", "encore", "--wav", str(clip), "--text-file", str(txt)]) == 1


def test_voice_name_with_trailing_newline_is_rejected(tmp_path, make_wav):
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    with pytest.raises(voices.VoiceError, match="invalid voice name"):
        voices.create_voice("a\n", clip, "text", root=tmp_path / "v")


def test_new_profile_fields_default_for_old_meta_and_load_when_present(tmp_path, make_wav):
    import json
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    p = voices.create_voice("me", clip, "words", root=tmp_path / "v")
    assert p.delivery == "instruct" and p.style == ""
    meta = tmp_path / "v" / "me" / "meta.json"
    data = json.loads(meta.read_text())
    meta.write_text(json.dumps({**data, "delivery": "zero_shot", "style": " Speak calmly. "}))
    q = voices.load_voice("me", root=tmp_path / "v")
    assert q.delivery == "zero_shot" and q.style == "Speak calmly."


@pytest.mark.parametrize("extra", [{"delivery": "shout"}, {"style": 3}])
def test_bad_delivery_or_style_is_a_clear_error(tmp_path, make_wav, extra):
    import json
    clip = make_wav(tmp_path / "in.wav", seconds=12)
    voices.create_voice("me", clip, "words", root=tmp_path / "v")
    meta = tmp_path / "v" / "me" / "meta.json"
    meta.write_text(json.dumps({**json.loads(meta.read_text()), **extra}))
    with pytest.raises(voices.VoiceError, match="delivery|style"):
        voices.load_voice("me", root=tmp_path / "v")
