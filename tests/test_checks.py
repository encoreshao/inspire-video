import shutil
import subprocess

import pytest

from showcase import checks

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
                                reason="ffmpeg and ffprobe are required")


def make(tmp_path, name, graph, size="1080x1920", seconds=2):
    out = tmp_path / name
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"color=c=white:s={size}:d={seconds}:r=30" + (f",{graph}" if graph else ""),
                    "-pix_fmt", "yuv420p", "-y", str(out)], check=True)
    return out


def test_a_clean_flat_video_passes(tmp_path):
    assert checks.check_video(make(tmp_path, "ok.mp4", "")) == []


def test_wrong_size_is_reported(tmp_path):
    problems = checks.check_video(make(tmp_path, "small.mp4", "", size="540x960"))
    assert any("540x960" in p and "1080x1920" in p for p in problems)
    assert checks.check_video(make(tmp_path, "half.mp4", "", size="540x960"), scale=0.5) == []


def test_a_black_first_frame_is_reported(tmp_path):
    out = tmp_path / "black.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                    "color=c=black:s=1080x1920:d=2:r=30", "-pix_fmt", "yuv420p", "-y", str(out)], check=True)
    assert any("first frame" in p for p in checks.check_video(out))


def test_content_below_the_safe_line_is_reported(tmp_path):
    out = make(tmp_path, "low.mp4", "drawbox=x=100:y=1700:w=800:h=120:color=black:t=fill")
    assert any("1590" in p for p in checks.check_video(out))
    high = make(tmp_path, "high.mp4", "drawbox=x=100:y=1500:w=800:h=60:color=black:t=fill")
    assert checks.check_video(high) == []


def test_content_near_the_side_edges_is_reported(tmp_path):
    left = make(tmp_path, "left.mp4", "drawbox=x=10:y=600:w=60:h=300:color=black:t=fill")
    assert any("left" in p for p in checks.check_video(left))
    right = make(tmp_path, "right.mp4", "drawbox=x=1020:y=600:w=40:h=300:color=black:t=fill")
    assert any("right" in p for p in checks.check_video(right))


def test_duration_range_is_checked_only_when_asked(tmp_path):
    out = make(tmp_path, "short.mp4", "")
    assert checks.check_video(out) == []
    assert any("40" in p and "150" in p for p in checks.check_video(out, duration_range=(40, 150)))


def test_cli_exit_codes(tmp_path, capsys):
    ok = make(tmp_path, "ok.mp4", "")
    assert checks.main([str(ok)]) == 0
    bad = make(tmp_path, "bad.mp4", "drawbox=x=100:y=1700:w=800:h=120:color=black:t=fill")
    assert checks.main([str(bad)]) == 1 and "1590" in capsys.readouterr().out
    assert checks.main([str(tmp_path / "missing.mp4")]) == 1


def test_a_soft_shadow_near_the_side_edges_is_not_content(tmp_path):
    # A drop shadow fades into the margin (luma differences of about 10-15); real content differs by 30 or more.
    soft_left = make(tmp_path, "soft-left.mp4", "drawbox=x=40:y=600:w=40:h=300:color=0xEEEEEE:t=fill")
    assert checks.check_video(soft_left) == []
    soft_right = make(tmp_path, "soft-right.mp4", "drawbox=x=1000:y=600:w=40:h=300:color=0xEEEEEE:t=fill")
    assert checks.check_video(soft_right) == []
    strong = make(tmp_path, "strong.mp4", "drawbox=x=40:y=600:w=40:h=300:color=0xCCCCCC:t=fill")
    assert any("left" in p for p in checks.check_video(strong))
