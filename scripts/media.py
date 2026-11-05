#!/usr/bin/env python3
"""Run ffmpeg or ffprobe on files inside this skill's output/ folder only.

Usage:
  python scripts/media.py ffmpeg <ffmpeg arguments...>
  python scripts/media.py ffprobe <ffprobe arguments...>

Same arguments as the real tools. It exists for sandboxed runs (for example the
LoopX Creator page's jobs), where the media tools may not be started directly: it
refuses what could read or write outside the project, so a hostile video title or
transcript cannot turn a cut into something else:

- every file argument must resolve (symlinks followed) inside output/;
- an output may not be a code or config file (py, js, sh, ...);
- no network or pipe protocols, no concat lists, no filter scripts, no filters that
  read files (movie, subtitles, textfile, ...), no log or stats files, no `..`,
  `~` or absolute paths inside filter expressions.

Frames and temporary files go under output/, never /tmp.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
TOOLS = {"ffmpeg", "ffprobe"}

# Options that name an extra file or URL to read or write, or run scripts.
BANNED_OPTIONS = {
    "-filter_script", "-filter_complex_script", "-attach", "-dump_attachment",
    "-passlogfile", "-vstats_file", "-vstats", "-report", "-sdp_file",
    "-protocol_whitelist", "-safe", "-headers", "-user_agent", "-method",
    "-cookies", "-progress", "-readrate_initial_burst", "-init_hw_device",
}
# Filters and parameters that read a file named in the expression.
BANNED_TEXT = (
    "movie=", "amovie=", "subtitles=", "ass=", "textfile=", "file=", "filename=",
    "sendcmd", "zmq", "lut3d", "haldclut", "ref=", "://",
)
BANNED_PROTOCOLS = {
    "file", "pipe", "concat", "subfile", "tcp", "udp", "http", "https", "rtp",
    "rtmp", "rtsp", "ftp", "sftp", "tee", "unix", "data", "crypto", "cache",
    "md5", "hls", "gopher", "srt", "async", "ffrtmphttp", "mmsh", "mmst",
}
CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".sh", ".zsh", ".bash",
    ".command", ".rb", ".pl", ".php", ".plist", ".yaml", ".yml", ".toml", ".cfg",
    ".ini", ".html", ".htm", ".css", ".md", ".env",
}
FILE_SUFFIXES = CODE_SUFFIXES | {
    ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4a", ".m4v", ".mp3", ".wav",
    ".aac", ".flac", ".ogg", ".opus", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".srt", ".vtt", ".txt", ".json", ".log", ".ts", ".mxf",
}
ABSOLUTE_IN_EXPRESSION = re.compile(r"""(^|[=:,'"\s\[(|;])(/|~)""")


def _is_path_like(arg: str) -> bool:
    if arg == "-":
        return False  # stdin / stdout
    if arg.startswith("-") or "=" in arg or "," in arg:
        return False
    return "/" in arg or Path(arg).suffix.lower() in FILE_SUFFIXES


def _inside_output(arg: str) -> str | None:
    """None when `arg` resolves inside output/, else why not."""
    path = Path(arg)
    resolved = (path if path.is_absolute() else ROOT / path).resolve()
    if resolved != OUT and OUT.resolve() not in resolved.parents:
        return f"{arg!r} is outside output/"
    if resolved.suffix.lower() in CODE_SUFFIXES:
        return f"{arg!r} is a code or config file type"
    return None


def validate(tool: str, args: list[str]) -> list[str]:
    """The reasons `tool args` must not run; empty when it may."""
    if tool not in TOOLS:
        return [f"only ffmpeg and ffprobe may be run, not {tool!r}"]
    errors: list[str] = []
    prev = ""
    for arg in args:
        base = arg.split(":", 1)[0]
        if arg.startswith("-") and (base in BANNED_OPTIONS or arg.startswith("-/")):
            errors.append(f"option {arg!r} is not allowed")
        if prev == "-f" and arg in {"concat", "image2pipe", "tee"}:
            errors.append(f"-f {arg} is not allowed")
        if _is_path_like(arg):
            why = _inside_output(arg)
            if why:
                errors.append(why)
            scheme = arg.split(":", 1)[0].lower()
            if ":" in arg and scheme in BANNED_PROTOCOLS:
                errors.append(f"protocol {scheme!r} is not allowed")
        else:
            scheme = arg.split(":", 1)[0].lower()
            if ":" in arg and scheme in BANNED_PROTOCOLS and "=" not in scheme:
                errors.append(f"protocol {scheme!r} is not allowed")
            low = arg.lower()
            for bad in BANNED_TEXT:
                if bad in low:
                    errors.append(f"{bad!r} is not allowed in {arg!r}")
            if ".." in arg or ABSOLUTE_IN_EXPRESSION.search(arg):
                errors.append(f"{arg!r} reaches outside output/")
        prev = arg
    return sorted(set(errors))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    tool, args = argv[0], argv[1:]
    errors = validate(tool, args)
    if errors:
        print("media.py refused this command:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 3
    binary = shutil.which(tool)
    if not binary:
        print(f"{tool} not found on PATH", file=sys.stderr)
        return 127
    os.chdir(ROOT)
    return subprocess.call([binary, *args])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
