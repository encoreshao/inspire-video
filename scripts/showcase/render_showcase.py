#!/usr/bin/env python3
"""Render a showcase project with Remotion.

  python scripts/render.py <project-dir> [--preview] [--cover] [--theme T] [--force] [--allow-unresolved-rights]

Reads video_manifest.json (type "showcase"), timings.json (narration) and brief.json (rights). Output:
output/final/<project_id>/<project_id>.mp4 + cover.png, or <project-dir>/preview.mp4 with --preview.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zh_break import with_units, zh_units  # noqa: E402
from showcase.assets import image_size  # noqa: E402
from showcase.checks import check_video  # noqa: E402
from showcase.timing import MAX_TOTAL, MIN_TOTAL  # noqa: E402
from showcase.manifest import FPS, ManifestError, beat_seconds_list, beat_target, crop_warnings, frame_windows, validate_showcase  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def stage(project: Path, public: Path, m: dict, timings: dict | None) -> dict:
    """Copy each beat's image (and narration audio) into Remotion's public folder."""
    public.mkdir(parents=True, exist_ok=True)
    pid, out = m["project_id"], {}
    for b in m["beats"]:
        asset = None                                       # a statement beat has no capture
        if b.get("asset"):
            src = project / b["asset"]
            asset = f"{pid}-{b['id']}{src.suffix.lower()}"
            shutil.copy2(src, public / asset)
        audio = None
        if timings:
            wav = project / "audio" / f"{b['id']}.wav"
            if not wav.is_file():
                raise ManifestError(f"the narration audio for beat {b['id']!r} is missing ({wav}): run narrate again")
            audio = f"{pid}-{b['id']}.wav"
            shutil.copy2(wav, public / audio)
        out[b["id"]] = {"asset": asset, "audio": audio}
    return out


def statement_units(text: str) -> list[str]:
    """The pieces of a statement that arrive one after another: words (Chinese: zh_break units), each keeping its space."""
    return zh_units(text) or re.findall(r"\S+\s*", text)


def composition_for(m: dict) -> str:
    return "ShowcasePromo" if m.get("style", "device") == "promo" else "ShowcaseShort"


def build_props(m: dict, project: Path, timings: dict | None, staged: dict, zh_breaks: bool = True) -> dict:
    seconds = beat_seconds_list(m, timings)
    windows = frame_windows(seconds, FPS)
    promo = m.get("style", "device") == "promo"
    beats = []
    for b, w in zip(m["beats"], windows):
        iw, ih = image_size(project / b["asset"]) if b.get("asset") else (0, 0)
        entry = {"id": b["id"], "en": b["en"], "zh": b["zh"], "asset": staged[b["id"]]["asset"] or "", "iw": iw, "ih": ih,
                 "focus": b.get("focus") or {"x": 0, "y": 0, "w": 1, "h": 1}, "callout": b.get("callout"),
                 "audio": staged[b["id"]]["audio"], "startFrame": w["start"], "frames": w["frames"]}
        if b.get("topic"):
            entry["topic"] = b["topic"]                    # the transitions and the topic label key off it
        if promo and b.get("shot") == "statement":
            entry.update({"shot": "statement", "statement": b["statement"], "statementUnits": statement_units(b["statement"])})
        elif promo:
            box, info = beat_target(b, project)
            entry.update({"shot": b.get("shot", "hero-push"), "box": box, "page": info["page"], "imageScale": info["scale"]})
        beats.append(entry)
    beats = with_units(beats, zh_breaks)
    p = m["project"]
    props = {"headline": m["headline"], "subtitle": m["subtitle"], "category": m.get("category") or ("PROMO / 产品宣传" if promo else "SHOWCASE / 项目展示"),
             "theme": m.get("theme") or ("ink" if promo else "light"), "name": p["name"], "nameZh": p.get("name_zh", ""),
             "tagline": p.get("tagline", ""), "taglineZh": p.get("tagline_zh", ""), "sourceLabel": m["source"]["label"],
             "beats": beats, "durationSeconds": round(sum(w["frames"] for w in windows) / FPS, 2)}
    return props


def cover_props(props: dict) -> dict:
    keys = ("headline", "subtitle", "category", "theme", "name", "nameZh", "tagline", "taglineZh", "sourceLabel")
    return {**{k: props[k] for k in keys}, "beat": props["beats"][0]}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main(argv=None, run=subprocess.run) -> int:
    ap = argparse.ArgumentParser(description="Render a showcase project")
    ap.add_argument("project_dir")
    ap.add_argument("--preview", action="store_true", help="half-scale draft render")
    ap.add_argument("--cover", action="store_true", help="render the cover image only")
    ap.add_argument("--theme", choices=["light", "mist", "ivory", "ink", "sage"])
    ap.add_argument("--force", action="store_true", help="overwrite existing final files")
    ap.add_argument("--allow-unresolved-rights", action="store_true",
                    help="render a final video although some asset rights are unresolved (you have confirmed them)")
    ap.add_argument("--no-check", action="store_true", help="skip the output checks")
    ap.add_argument("--no-zh-breaks", action="store_true", help="wrap Chinese captions between any two characters, as before")
    a = ap.parse_args(argv)
    try:
        project = Path(a.project_dir).resolve()
        m = json.loads((project / "video_manifest.json").read_text(encoding="utf-8"))
        if a.theme:
            m["theme"] = a.theme
        timings = _load(project / "timings.json")
        validate_showcase(m, project, timings)
        brief = _load(project / "brief.json")
        if brief and brief.get("rights_unresolved") and not a.preview and not a.allow_unresolved_rights:
            raise ManifestError("some assets have unresolved rights: confirm you may reuse them, then pass "
                                "--allow-unresolved-rights (preview renders are exempt)")
        for w in crop_warnings(m, project):
            print(f"warning: {w}", file=sys.stderr)
        final_dir = ROOT / "output" / "final" / m["project_id"]
        if not a.preview and not a.cover and (final_dir / "cover.png").exists() and not a.force:
            raise ManifestError(f"{final_dir / 'cover.png'} exists; use --force to overwrite")     # before the long render
        staged = stage(project, ROOT / "video" / "public", m, timings)
        props = build_props(m, project, timings, staged, not a.no_zh_breaks)
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except (KeyError, AttributeError, TypeError) as e:
        print(f"error: a project file is malformed ({type(e).__name__}: {e}); check video_manifest.json and timings.json",
              file=sys.stderr)
        return 1
    props_file = project / "props.json"
    props_file.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    video_cwd = ROOT / "video"

    def go(cmd) -> int:
        try:
            return run(cmd, cwd=video_cwd).returncode
        except OSError as e:
            print(f"error: could not run {cmd[0]}: {e}", file=sys.stderr)
            return 1

    def render_cover() -> int:
        out = final_dir / "cover.png"
        if out.exists() and not a.force:
            print(f"error: {out} exists; use --force to overwrite", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        cfile = project / "cover_props.json"
        cfile.write_text(json.dumps(cover_props(props), ensure_ascii=False, indent=2), encoding="utf-8")
        rc = go(["npx", "remotion", "still", "src/index.ts", "ShowcaseCover", str(out), f"--props={cfile}"])
        if rc == 0:
            print(f"Rendered: {out}")
        return rc

    if a.cover:
        return render_cover()
    out = project / "preview.mp4" if a.preview else final_dir / f"{m['project_id']}.mp4"
    if not a.preview and out.exists() and not a.force:
        print(f"error: {out} exists; use --force to overwrite", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["npx", "remotion", "render", "src/index.ts", composition_for(m), str(out), f"--props={props_file}",
           "--codec=h264", "--crf=18"] + (["--scale=0.5"] if a.preview else [])
    print("+", " ".join(cmd))
    rc = go(cmd)
    if rc != 0:
        return rc
    print(f"Rendered: {out}")
    if not a.no_check:
        problems = check_video(out, 0.5 if a.preview else 1.0, None if a.preview else (MIN_TOTAL, MAX_TOTAL))
        for p in problems:
            print(f"CHECK FAILED: {p}")
        if problems:
            if not a.preview:
                print("note: the cover was not rendered; fix the problem, render again with --force, or run --cover")
            return 3
    return 0 if a.preview else render_cover()


if __name__ == "__main__":
    sys.exit(main())
