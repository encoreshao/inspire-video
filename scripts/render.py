#!/usr/bin/env python3
"""Validate a project's video_manifest.json and render it with Remotion.

Usage: python scripts/render.py <project-dir> [--preview] [--force]
Output: output/final/<project-id>.mp4  (or <project-dir>/preview.mp4 with --preview)
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def validate(m: dict, clip_seconds: float | None) -> None:
    import jsonschema
    jsonschema.validate(m, json.loads((ROOT / "references/manifest-schema.json").read_text()))
    s = m["source"]
    if s["end_seconds"] <= s["start_seconds"]:
        raise ValueError("source end_seconds must be after start_seconds")
    dur = s["end_seconds"] - s["start_seconds"]
    for c in m["subtitles"]:
        if c["end"] <= c["start"] or c["end"] > dur + 0.01:
            raise ValueError(f"subtitle cue outside clip or inverted: {c}")
    for c in m["subtitles"]:
        if re.search(r'[.!?]["\u201d\']?\s+[A-Z\u201c"]', c["en"].strip()):
            raise ValueError(f"cue holds more than one sentence; split it so one sentence shows at a time: {c['en'][:60]}...")
    ids = {p["id"] for p in m["copy"].get("speakers", [])}
    for c in m["subtitles"]:
        if len(c["en"]) > 100:
            raise ValueError(f"cue is {len(c['en'])} chars; keep each cue short (<=100) so little text shows at once: {c['en'][:50]}...")
        if "speaker" in c and c["speaker"] not in ids:
            raise ValueError(f"cue speaker '{c['speaker']}' is not listed in copy.speakers")
    prev_end = 0.0
    for c in m["subtitles"]:
        if c["start"] < prev_end - 0.01:
            raise ValueError(f"subtitle cues overlap or are unsorted at {c['start']}")
        prev_end = c["end"]
    if m["subtitles"] and dur - m["subtitles"][-1]["end"] < 0.2:
        raise ValueError("clip ends <0.2s after the last cue: speech may be cut off; extend the tail")
    if m["subtitles"] and m["subtitles"][0]["start"] < 0.1:
        raise ValueError("first cue starts <0.1s into the clip: speech may be cut off; extend the lead-in")
    if not 40 <= dur <= 150:
        raise ValueError(f"clip is {dur:.1f}s; allowed range is 40-150 s")
    if not m["provenance"]["rights_confirmed"]:
        raise ValueError("provenance.rights_confirmed is false; refusing to render")
    if m["provenance"].get("review_status", "pending") == "rejected":
        raise ValueError("review_status is rejected")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--preview", action="store_true", help="half-scale draft render")
    ap.add_argument("--theme", choices=["light", "mist", "ivory", "ink", "sage"], help="background theme (default: manifest theme, else light)")
    ap.add_argument("--cover", action="store_true", help="render the cover image only")
    ap.add_argument("--force", action="store_true", help="overwrite existing final file")
    a = ap.parse_args()

    proj = Path(a.project_dir).resolve()
    m = json.loads((proj / "video_manifest.json").read_text())
    validate(m, None)

    clip = Path(m["video"]["clip_path"])
    clip = clip if clip.is_absolute() else proj / clip
    if not clip.exists():
        raise FileNotFoundError(clip)
    public = ROOT / "video/public"
    public.mkdir(exist_ok=True)
    staged = f"{m['project_id']}-{clip.name}"
    shutil.copy2(clip, public / staged)

    cp = m["copy"]
    role_en = " · ".join(x for x in [cp.get("speaker_title"), cp.get("speaker_org")] if x) or cp.get("speaker_credential", "")
    role_zh = " · ".join(x for x in [cp.get("speaker_title_zh"), cp.get("speaker_org")] if x)
    credit = cp.get("speaker_name") or "Speaker unknown"
    src_line = " · ".join(str(x) for x in [cp.get("source_name"), cp.get("year")] if x)
    dur = m["source"]["end_seconds"] - m["source"]["start_seconds"]
    props = {
        "headline": cp["headline_zh"], "subtitle": cp["subtitle_en"],
        "quoteEn": cp["quote_en"], "quoteZh": cp["quote_zh"],
        "speaker": credit, "speakerZh": cp.get("speaker_name_zh", ""), "role": role_en, "roleZh": role_zh, "source": src_line or "Source unknown",
        "clip": staged, "durationSeconds": dur,
        "category": cp.get("category") or "INSPIRATION / 向上生长",
        "cues": [{k: c[k] for k in ("start", "end", "en", "zh", "speaker") if k in c} for c in m["subtitles"]],
        "people": cp.get("speakers", []),
        "theme": a.theme or m.get("theme", "light"), "videoFit": m["video"].get("fit", "contain"), "cropX": m["video"].get("crop_x", 0.5), "cropY": m["video"].get("crop_y", 0.5),
        "talkTitle": cp.get("talk_title", ""), "excerptLabel": cp.get("excerpt_label", ""),
    }
    poster = proj / "assets/poster.jpg"
    if poster.exists():
        pname = f"{m['project_id']}-poster.jpg"
        shutil.copy2(poster, public / pname)
        props["poster"] = pname
    props_file = proj / "props.json"
    props_file.write_text(json.dumps(props, ensure_ascii=False, indent=2))

    if a.cover:
        out = ROOT / "output/final" / f"{m['project_id']}-cover.png"
        if out.exists() and not a.force:
            raise FileExistsError(f"{out} exists; use --force to overwrite")
        out.parent.mkdir(parents=True, exist_ok=True)
        cprops = {k: props.get(k) for k in ("headline", "subtitle", "theme", "people", "speaker", "speakerZh", "role", "roleZh", "source", "poster", "talkTitle", "category")}
        cfile = proj / "cover_props.json"
        cfile.write_text(json.dumps(cprops, ensure_ascii=False, indent=2))
        r = subprocess.run(["npx", "remotion", "still", "src/index.ts", "InspireCover", str(out), f"--props={cfile}"],
                           cwd=ROOT / "video")
        if r.returncode == 0:
            print(f"Rendered: {out}")
        return r.returncode

    if a.preview:
        out = proj / "preview.mp4"
    else:
        out = ROOT / "output/final" / f"{m['project_id']}.mp4"
        if out.exists() and not a.force:
            raise FileExistsError(f"{out} exists; use --force to overwrite")
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["npx", "remotion", "render", "src/index.ts", "InspireShort", str(out),
           f"--props={props_file}", "--codec=h264", "--crf=18"]
    if a.preview:
        cmd += ["--scale=0.5"]
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT / "video")
    if r.returncode == 0:
        print(f"Rendered: {out}")
    return r.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
