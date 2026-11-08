#!/usr/bin/env python3
"""Repair a chosen clip range so it starts and ends on transcript cue edges and fits the 120-300 s rule.

Usage:
  python scripts/refine_segment.py <project-dir> --start <seconds> --end <seconds> [--write]

The agent picks the range from `transcript.json`; this script does the arithmetic the agent should not guess:
snap both ends to cue boundaries, extend a short range over adjacent cues (never across a pause longer than
5 s), trim a long range back one cue at a time, and warn when the clip begins or ends mid-sentence. It prints a
JSON report (final start/end/duration, what changed, warnings); --write also saves it as <project-dir>/segment_report.json.
Review the report before using the range: a warning means read the first and last lines again.

Exit 0 on success, 1 when the range cannot be repaired. Same idea as autoclip's `refine_timeline` (MIT,
https://github.com/zhouxiaoka/autoclip); written for one contiguous clip, no code copied.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

MIN_SEC = 120.0              # keep equal to the clip rule in render.py
MAX_SEC = 300.0
SNAP_WINDOW = 3.0            # a boundary this close to a cue edge snaps to it
GAP = 5.0                    # extension never crosses a pause longer than this
SENTENCE_END = (".", "?", "!", "…", "。", "？", "！", '"', "”", "’", ")")


class RefineError(ValueError):
    pass


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


@dataclass
class Result:
    start: float
    end: float
    duration: float
    actions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_cues(path) -> list[Cue]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cues = []
    for s in data.get("segments", []):
        try:
            start, end, text = float(s["start"]), float(s["end"]), str(s.get("text", "")).strip()
        except (KeyError, TypeError, ValueError):
            continue
        if end > start and text:
            cues.append(Cue(start, end, text))
    return sorted(cues, key=lambda c: c.start)


def _snap(sec, cues, edge, window):
    """Index of the cue whose start (edge='start') or end (edge='end') is nearest to sec, within the window.
    Otherwise the cue that contains sec, or the nearest cue after (start) or before (end) it."""
    pick = (lambda c: c.start) if edge == "start" else (lambda c: c.end)
    i = min(range(len(cues)), key=lambda k: abs(pick(cues[k]) - sec))
    if abs(pick(cues[i]) - sec) <= window:
        return i
    if edge == "start":
        return next((k for k, c in enumerate(cues) if c.end >= sec), len(cues) - 1)
    return next((k for k in range(len(cues) - 1, -1, -1) if cues[k].start <= sec), 0)


def refine(start, end, cues, min_sec=MIN_SEC, max_sec=MAX_SEC, snap_window=SNAP_WINDOW, gap=GAP) -> Result:
    if not cues:
        raise RefineError("the transcript has no cues")
    if end <= start:
        raise RefineError(f"end ({end:g}) must be after start ({start:g})")
    si, ei = _snap(start, cues, "start", snap_window), _snap(end, cues, "end", snap_window)
    if ei < si:
        raise RefineError("the range does not cover a whole cue")
    actions: list[str] = []
    if cues[si].start != start:
        actions.append(f"snapped start {start:g} -> {cues[si].start:g}")
    if cues[ei].end != end:
        actions.append(f"snapped end {end:g} -> {cues[ei].end:g}")

    before = ei
    while cues[ei].end - cues[si].start < min_sec and ei + 1 < len(cues) and cues[ei + 1].start - cues[ei].end <= gap:
        ei += 1
    if ei != before:
        actions.append(f"extended end to {cues[ei].end:g}")
    grown_back = False
    while cues[ei].end - cues[si].start < min_sec and si > 0 and cues[si].start - cues[si - 1].end <= gap:
        si -= 1
        grown_back = True
    if grown_back:
        actions.append(f"extended start to {cues[si].start:g}")
    if cues[ei].end - cues[si].start < min_sec:
        raise RefineError(f"only {cues[ei].end - cues[si].start:.1f} s of connected speech around the range; "
                          f"a clip needs at least {min_sec:g} s")

    trimmed = False
    while cues[ei].end - cues[si].start > max_sec and ei > si:
        ei -= 1
        trimmed = True
    if cues[ei].end - cues[si].start > max_sec:
        raise RefineError(f"one cue is longer than the {max_sec:g} s maximum; choose another range")
    if trimmed:
        actions.append(f"trimmed end to {cues[ei].end:g}")
    if cues[ei].end - cues[si].start < min_sec:
        raise RefineError(f"trimming to {max_sec:g} s left less than {min_sec:g} s; choose a tighter range")

    warnings = []
    if not cues[ei].text.rstrip().endswith(SENTENCE_END):
        warnings.append(f"the clip ends mid-sentence: \"{cues[ei].text[-40:]}\"")
    if cues[si].text[:1].islower():
        warnings.append(f"the clip starts mid-sentence: \"{cues[si].text[:40]}\"")
    return Result(cues[si].start, cues[ei].end, round(cues[ei].end - cues[si].start, 3), actions, warnings)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Snap a clip range to cue edges and enforce 120-300 s")
    ap.add_argument("project")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--write", action="store_true", help="also save segment_report.json in the project folder")
    a = ap.parse_args(argv)
    transcript = Path(a.project) / "transcript.json"
    try:
        result = refine(a.start, a.end, load_cues(transcript))
    except (OSError, json.JSONDecodeError, RefineError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    report = json.dumps(asdict(result), ensure_ascii=False, indent=1)
    print(report)
    if a.write:
        (Path(a.project) / "segment_report.json").write_text(report + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
