import shutil
import subprocess

import pytest

import precheck

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
                                reason="ffmpeg and ffprobe are required")


def make(tmp_path, name, seconds, audio=True):
    out = tmp_path / name
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=gray:s=320x240:d={seconds}:r=10"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:d={seconds}", "-c:a", "aac"]
    subprocess.run(cmd + ["-pix_fmt", "yuv420p", "-y", str(out)], check=True)
    return out


def codes(problems):
    return [p.code for p in problems]


def test_a_long_enough_source_with_audio_passes(tmp_path):
    assert precheck.check_source(make(tmp_path, "ok.mp4", 45)) == []


def test_a_source_shorter_than_the_minimum_clip_is_refused(tmp_path):
    problems = precheck.check_source(make(tmp_path, "short.mp4", 20))
    assert codes(problems) == ["source_too_short"]
    assert "40" in problems[0].message


def test_a_source_without_audio_is_refused_unless_subtitles_are_supplied(tmp_path):
    silent = make(tmp_path, "silent.mp4", 45, audio=False)
    assert codes(precheck.check_source(silent)) == ["source_no_audio"]
    assert precheck.check_source(silent, has_subtitles=True) == []


def test_both_problems_are_reported_together(tmp_path):
    assert codes(precheck.check_source(make(tmp_path, "both.mp4", 10, audio=False))) == ["source_too_short", "source_no_audio"]


def test_cli_exit_codes_and_output(tmp_path, capsys):
    assert precheck.main([str(make(tmp_path, "ok.mp4", 45))]) == 0
    assert precheck.main([str(make(tmp_path, "short.mp4", 20))]) == 1
    assert "source_too_short" in capsys.readouterr().out
    assert precheck.main([str(tmp_path / "missing.mp4")]) == 1
    assert "not found" in capsys.readouterr().err
    assert precheck.main([str(make(tmp_path, "silent.mp4", 45, audio=False)), "--has-subtitles"]) == 0
