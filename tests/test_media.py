import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import media  # noqa: E402

OK = [
    ["-ss", "46", "-to", "120", "-i", "output/cache/x/source.mp4", "-vf", "scale=1280:720,fps=30",
     "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
     "output/projects/s/assets/clip.mp4"],
    ["-ss", "46", "-i", "output/projects/s/assets/clip.mp4", "-frames:v", "1", "-q:v", "2",
     "output/projects/s/assets/poster.jpg"],
    ["-i", "output/final/s/s.mp4", "-af", "volumedetect", "-vn", "-f", "null", "-"],
    ["-i", "output/final/s/s.mp4", "-vf", "blackdetect=d=0.5", "-an", "-f", "null", "-"],
    ["-ss", "12", "-i", "output/final/s/s.mp4", "-frames:v", "1", "-vf", "crop=864:1920", "output/projects/s/crop.png"],
    ["-i", "output/projects/s/assets/audio.wav", "-vf", "scale=iw/2:ih/2", "-map", "0:v:0", "output/x.mp4"],
]
ASK = [
    ["-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,r_frame_rate",
     "-of", "json", "output/final/s/s.mp4"],
]


def test_the_skills_own_commands_are_allowed():
    for a in OK:
        assert media.validate("ffmpeg", a) == [], a
    for a in ASK:
        assert media.validate("ffprobe", a) == [], a


def test_only_the_two_media_tools():
    assert media.validate("sh", ["-c", "id"])
    assert media.validate("ffplay", ["output/x.mp4"])


def test_files_must_stay_inside_output():
    for bad in [
        ["-i", "/etc/passwd", "output/a.mp4"],
        ["-i", "output/a.mp4", "/tmp/crop.png"],
        ["-i", "output/../scripts/render.py", "output/a.mp4"],
        ["-i", "output/a.mp4", "scripts/evil.mp4"],
        ["-i", "output/a.mp4", "~/x.mp4"],
        ["-i", "output/a.mp4", "../x.mp4"],
    ]:
        assert media.validate("ffmpeg", bad), bad


def test_an_output_cannot_be_code_or_config():
    for name in ["output/x.py", "output/x.js", "output/x.sh", "output/x.plist", "output/x.html"]:
        assert media.validate("ffmpeg", ["-i", "output/a.mp4", "-f", "data", name]), name


def test_symlinks_out_of_output_are_followed_and_refused(tmp_path):
    link = media.OUT / "_media_test_link"
    media.OUT.mkdir(exist_ok=True)
    try:
        link.symlink_to(tmp_path)
        assert media.validate("ffmpeg", ["-i", "output/_media_test_link/a.mp4", "output/b.mp4"])
    finally:
        if link.is_symlink():
            link.unlink()


def test_protocols_and_file_reading_filters_are_refused():
    for bad in [
        ["-i", "http://example.com/a.mp4", "output/a.mp4"],
        ["-i", "pipe:0", "output/a.mp4"],
        ["-i", "file:/etc/passwd", "output/a.mp4"],
        ["-i", "concat:a.mp4|b.mp4", "output/a.mp4"],
        ["-f", "concat", "-i", "output/list.txt", "output/a.mp4"],
        ["-i", "output/a.mp4", "-vf", "movie=/etc/passwd", "output/b.mp4"],
        ["-i", "output/a.mp4", "-vf", "subtitles=output/s.srt", "output/b.mp4"],
        ["-i", "output/a.mp4", "-vf", "drawtext=textfile=output/a.txt", "output/b.mp4"],
        ["-i", "output/a.mp4", "-vf", "drawtext=text=x:fontfile=/etc/hosts", "output/b.mp4"],
        ["-i", "output/a.mp4", "-filter_complex_script", "output/f.txt", "output/b.mp4"],
        ["-i", "output/a.mp4", "-report", "output/b.mp4"],
        ["-i", "output/a.mp4", "-attach", "output/s.txt", "output/b.mkv"],
        ["-i", "output/a.mp4", "-/filter", "output/f.txt", "output/b.mp4"],
        ["-protocol_whitelist", "file,http", "-i", "output/a.mp4", "output/b.mp4"],
    ]:
        assert media.validate("ffmpeg", bad), bad


def test_a_refused_command_exits_3_without_running(capsys):
    assert media.main(["ffmpeg", "-i", "/etc/passwd", "output/a.mp4"]) == 3
    assert "refused" in capsys.readouterr().err
