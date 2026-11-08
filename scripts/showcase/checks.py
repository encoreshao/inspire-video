#!/usr/bin/env python3
"""Post-render checks for a showcase video, using ffprobe and ffmpeg's signalstats (no extra dependencies).

  python scripts/showcase/checks.py <video.mp4> [--preview] [--final] [--sheet sheet.png]

Checks: size, a bright first frame and last frame, nothing below y = 1590, nothing within 100 px of the side edges.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SAFE_BOTTOM_Y = 1590
EDGE = 100
FLAT = 8                                   # a flat background strip varies by at most this much in luma
SIDE_FLAT = 24                             # side strips also see the panel's soft drop shadow (about 10-15); content is 30+
STATS = re.compile(r"lavfi\.signalstats\.(YMIN|YMAX|YAVG)=([\d.]+)")


def _probe(path, run):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height:format=duration", "-of", "json", str(path)],
            check=True, capture_output=True, text=True)
    d = json.loads(r.stdout)
    return int(d["streams"][0]["width"]), int(d["streams"][0]["height"]), float(d["format"]["duration"])


def _stats(path, vf, at, run):
    chain = ",".join(x for x in (vf, "signalstats", "metadata=print:file=-") if x)
    seek = ["-sseof", f"{at:.3f}"] if at < 0 else ["-ss", f"{at:.3f}"]   # a negative time counts back from the end
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", *seek, "-i", str(path), "-vf", chain,
             "-frames:v", "1", "-f", "null", "-"], check=True, capture_output=True, text=True)
    found = {k: float(v) for k, v in STATS.findall(r.stdout)}
    if not {"YMIN", "YMAX", "YAVG"} <= found.keys():
        raise RuntimeError(f"ffmpeg returned no frame statistics at {at:.2f} s")
    return found


def check_video(path, scale: float = 1.0, duration_range=None, run=subprocess.run) -> list[str]:
    path = Path(path)
    problems: list[str] = []
    w, h, dur = _probe(path, run)
    ew, eh = round(1080 * scale), round(1920 * scale)
    if (w, h) != (ew, eh):
        problems.append(f"the video is {w}x{h} but {ew}x{eh} is expected")
    if duration_range and not duration_range[0] <= dur <= duration_range[1]:
        problems.append(f"the video is {dur:.1f} s but it must be {duration_range[0]:g} to {duration_range[1]:g} s")
    if _stats(path, "", 0, run)["YAVG"] < 20:          # pure black is 16 in video luma; the dark "ink" theme is about 37
        problems.append("the first frame is black (the video must not fade in from black)")
    last = _stats(path, "", -0.04, run)["YAVG"]
    before = _stats(path, "", max(0.0, dur - 1.0), run)["YAVG"]
    if last < 20 or last < 0.7 * before:     # a fade never quite reaches black on its last frame, so also compare with 1 s earlier
        problems.append("the last frame is black or faded (the video must hold its last image, not fade out)")
    bottom_y, edge = round(h * SAFE_BOTTOM_Y / 1920), max(2, round(w * EDGE / 1080))   # from the real size, so a wrong size cannot crash ffmpeg
    strips = {
        f"content below y = {SAFE_BOTTOM_Y}": (f"crop={w}:{max(1, h - bottom_y)}:0:{bottom_y}", FLAT),
        f"content within {EDGE} px of the left edge": (f"crop={edge}:{h}:0:0", SIDE_FLAT),
        f"content within {EDGE} px of the right edge": (f"crop={edge}:{h}:{w - edge}:0", SIDE_FLAT),
    }
    hit: dict[str, float] = {}
    for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
        at = dur * frac
        for label, (crop, tolerance) in strips.items():
            s = _stats(path, crop, at, run)
            if label not in hit and s["YMAX"] - s["YMIN"] > tolerance:
                hit[label] = at
    problems += [f"{label} (first seen at {at:.1f} s)" for label, at in hit.items()]
    return problems


def contact_sheet(path, out, frames: int = 12, run=subprocess.run) -> Path:
    """Write a PNG grid of `frames` evenly spaced frames, for the independent review (references/final-review.md)."""
    if frames < 1:
        raise ValueError("frames must be at least 1")
    _, _, dur = _probe(path, run)
    cols = min(frames, 4)
    rows = -(-frames // cols)
    vf = f"fps={frames / dur:.6f},scale=270:-1,tile={cols}x{rows}"      # one frame per dur / frames seconds
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vf", vf, "-frames:v", "1", "-y", str(out)],
        check=True, capture_output=True, text=True)
    return Path(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check a rendered showcase video")
    ap.add_argument("video")
    ap.add_argument("--preview", action="store_true", help="half-scale draft render")
    ap.add_argument("--final", action="store_true", help="also require a 120-300 s duration")
    ap.add_argument("--sheet", metavar="PNG", help="also write a contact sheet of 12 frames for the independent review")
    a = ap.parse_args(argv)
    try:
        if a.sheet:
            print(f"contact sheet: {contact_sheet(a.video, a.sheet)}")
        problems = check_video(a.video, 0.5 if a.preview else 1.0, (120, 300) if a.final else None)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for p in problems:
        print(f"CHECK FAILED: {p}")
    if not problems:
        print("all checks passed")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
