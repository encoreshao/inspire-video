#!/usr/bin/env python3
"""Check a source video before any transcription or editing work (ffprobe only).

Usage:
  python scripts/precheck.py <video> [--has-subtitles]

Refuses a source that cannot give a clip, with a stable code and a plain sentence:
  source_too_short  less than 40 s of material (the renderer's minimum clip length is 40 s)
  source_no_audio   no audio track, and no subtitles supplied to take the words from

Exit 0 when the source passes, 1 otherwise. The idea of failing early with stable codes comes from
autoclip's media_precheck (MIT, https://github.com/zhouxiaoka/autoclip); no code was copied.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MIN_SOURCE_SEC = 40          # keep equal to the lower bound of the 40-150 s clip rule in render.py

SOURCE_TOO_SHORT = "source_too_short"
SOURCE_NO_AUDIO = "source_no_audio"


@dataclass(frozen=True)
class Problem:
    code: str
    message: str


def _probe(path, run):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(path)],
            check=True, capture_output=True, text=True)
    d = json.loads(r.stdout)
    duration = float(d.get("format", {}).get("duration") or 0)
    has_audio = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    return duration, has_audio


def check_source(path, has_subtitles: bool = False, run=subprocess.run) -> list[Problem]:
    duration, has_audio = _probe(path, run)
    problems: list[Problem] = []
    if duration < MIN_SOURCE_SEC:
        problems.append(Problem(SOURCE_TOO_SHORT,
                                f"The source is {duration:.0f} s but a clip needs at least {MIN_SOURCE_SEC} s of material. "
                                "Use a longer video."))
    if not has_audio and not has_subtitles:
        problems.append(Problem(SOURCE_NO_AUDIO,
                                "The source has no audio track, so there is nothing to transcribe. "
                                "Supply subtitles (--has-subtitles) or use a video with sound."))
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check that a source video can give a clip")
    ap.add_argument("video")
    ap.add_argument("--has-subtitles", action="store_true", help="subtitles are supplied, so a silent source is fine")
    a = ap.parse_args(argv)
    if not Path(a.video).is_file():
        print(f"error: {a.video} not found", file=sys.stderr)
        return 1
    try:
        problems = check_source(a.video, a.has_subtitles)
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        print(f"error: could not read {a.video}: {e}", file=sys.stderr)
        return 1
    for p in problems:
        print(f"{p.code}: {p.message}")
    if not problems:
        print("source ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
