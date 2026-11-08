#!/usr/bin/env python3
"""Validate a project's video_manifest.json and render it with Remotion.

Usage: python scripts/render.py <project-dir> [--platform id,id] [--profile id] [--preview] [--force]
Output: output/final/<project-id>/<project-id>.mp4 + cover.png  (or <project-dir>/preview.mp4 with --preview)
With --platform / --profile, every distinct video profile those platforms use is rendered once; profiles other than
the default 9:16 write <project-id>-<profile>.mp4 and cover-<profile>.png (see config/platforms.yaml).
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

import platforms
from zh_break import with_units

MIN_CLIP_SEC, MAX_CLIP_SEC = 120.0, 300.0     # the clip rule: 2 to 5 minutes (keep equal to showcase/timing.py)

def quiet_log() -> list[str]:
    """Remotion prints one progress line per frame (thousands for a 2 to 5 minute video), which buries the real error when
    a tool, a log or an agent keeps only the last part of the output. Outside an interactive terminal, ask for errors only."""
    return [] if sys.stdout.isatty() else ["--log=error"]


ROOT = Path(__file__).resolve().parent.parent


def validate(m: dict, clip_seconds: float | None) -> None:
    import jsonschema
    jsonschema.validate(m, json.loads((ROOT / "schemas/manifest-schema.json").read_text()))
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
    if not MIN_CLIP_SEC <= dur <= MAX_CLIP_SEC:
        raise ValueError(f"clip is {dur:.1f}s; allowed range is {MIN_CLIP_SEC:g}-{MAX_CLIP_SEC:g} s")
    if not m["provenance"]["rights_confirmed"]:
        raise ValueError("provenance.rights_confirmed is false; refusing to render")
    if m["provenance"].get("review_status", "pending") == "rejected":
        raise ValueError("review_status is rejected")


def _is_showcase_project() -> bool:
    """True when a project folder named on the command line holds a showcase manifest.
    Checked before the speaker flags are parsed, so showcase-only flags such as --allow-unresolved-rights work."""
    for arg in sys.argv[1:]:
        if arg.startswith("-"):
            continue
        manifest = Path(arg).resolve() / "video_manifest.json"
        try:
            if manifest.exists() and json.loads(manifest.read_text()).get("type") == "showcase":
                return True
        except (OSError, ValueError):
            pass
    return False


def main() -> int:
    if _is_showcase_project():
        from showcase import render_showcase           # the showcase mode has its own manifest and composition
        return render_showcase.main(sys.argv[1:])
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--preview", action="store_true", help="half-scale draft render")
    ap.add_argument("--theme", choices=["light", "mist", "ivory", "ink", "sage"], help="background theme (default: manifest theme, else light)")
    ap.add_argument("--cover", action="store_true", help="render the cover image only")
    ap.add_argument("--force", action="store_true", help="overwrite existing final file")
    ap.add_argument("--no-zh-breaks", action="store_true", help="wrap Chinese captions between any two characters, as before")
    ap.add_argument("--platform", default="", help="comma-separated platform ids from config/platforms.yaml: render each "
                    "distinct video profile they use, and check their clip-length limits")
    ap.add_argument("--profile", help="render this profile only (for example portrait-4x5), overriding the profiles implied by --platform")
    a = ap.parse_args()

    proj = Path(a.project_dir).resolve()
    m = json.loads((proj / "video_manifest.json").read_text())
    validate(m, None)
    reg = platforms.load()
    platform_ids = [x.strip() for x in a.platform.split(",") if x.strip()]
    clip_seconds = m["source"]["end_seconds"] - m["source"]["start_seconds"]
    problems = platforms.check_duration(reg, platform_ids, clip_seconds)
    if problems:
        raise ValueError("; ".join(problems))
    targets, warnings = platforms.plan_renders(reg, platform_ids, a.profile)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

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
    dur = clip_seconds
    props = {
        "headline": cp["headline_zh"], "subtitle": cp["subtitle_en"],
        "quoteEn": cp["quote_en"], "quoteZh": cp["quote_zh"], "quoteZhUnits": with_units([{"zh": cp["quote_zh"]}], not a.no_zh_breaks)[0].get("zhUnits"),
        "speaker": credit, "speakerZh": cp.get("speaker_name_zh", ""), "role": role_en, "roleZh": role_zh, "source": src_line or "Source unknown",
        "clip": staged, "durationSeconds": dur,
        "category": cp.get("category") or "INSPIRATION / 向上生长",
        "cues": with_units([{k: c[k] for k in ("start", "end", "en", "zh", "speaker") if k in c} for c in m["subtitles"]], not a.no_zh_breaks),
        "people": cp.get("speakers", []),
        "theme": a.theme or m.get("theme", "light"), "videoFit": m["video"].get("fit", "cover"), "cropX": m["video"].get("crop_x", 0.5), "cropY": m["video"].get("crop_y", 0.5),
        "talkTitle": cp.get("talk_title", ""), "excerptLabel": cp.get("excerpt_label", ""),
    }
    for line in (role_en, role_zh):
        if len(line) > 58:
            print(f"WARNING: speaker title/company line is {len(line)} chars and will wrap, which can push the bottom block "
                  f"past the safe area; shorten speaker_title or speaker_org: {line[:60]}", file=sys.stderr)
    poster = proj / "assets/poster.jpg"
    if poster.exists():
        pname = f"{m['project_id']}-poster.jpg"
        shutil.copy2(poster, public / pname)
        props["poster"] = pname
    props_file = proj / "props.json"
    props_file.write_text(json.dumps(props, ensure_ascii=False, indent=2))

    final_dir = ROOT / "output/final" / m["project_id"]
    default_id = platforms.DEFAULT_PROFILE

    if not a.force and not a.preview:  # report every existing output up front, before any minutes-long render starts
        # a video render always overwrites its own cover afterwards, so only the files this run refuses to overwrite count
        name = (lambda pr: platforms.cover_name(pr.id)) if a.cover else (lambda pr: platforms.video_name(m["project_id"], pr.id))
        existing = [f for f in (final_dir / name(pr) for pr in targets) if f.exists()]
        if existing:
            raise FileExistsError("; ".join(f"{f} exists" for f in existing) + "; use --force to overwrite "
                                  "(it re-renders every format listed), or --profile <id> to render a single format")

    def suffixed(name: str, profile) -> str:
        """props.json for the default profile, props-<profile>.json otherwise."""
        stem, ext = name.rsplit(".", 1)
        return name if profile.id == default_id else f"{stem}-{profile.id}.{ext}"

    def render_cover(profile, overwrite: bool = False) -> int:
        out = final_dir / platforms.cover_name(profile.id)
        if out.exists() and not (a.force or overwrite):
            raise FileExistsError(f"{out} exists; use --force to overwrite")
        out.parent.mkdir(parents=True, exist_ok=True)
        cprops = {k: props.get(k) for k in ("headline", "subtitle", "theme", "people", "speaker", "speakerZh", "role", "roleZh", "source", "poster", "talkTitle", "category")}
        if profile.id != default_id:
            cprops["profile"] = profile.props()
        cfile = proj / suffixed("cover_props.json", profile)
        cfile.write_text(json.dumps(cprops, ensure_ascii=False, indent=2))
        r = subprocess.run(["npx", "remotion", "still", "src/index.ts", "InspireCover", str(out), f"--props={cfile}", *quiet_log()],
                           cwd=ROOT / "video")
        if r.returncode == 0:
            print(f"Rendered: {out}")
            return 0
        return cover_frame_grab(profile, out, r.returncode)

    def cover_frame_grab(profile, out, failed_code: int) -> int:
        """A failed cover must not block delivery: use a frame of the finished video (else of the clip)."""
        video = final_dir / platforms.video_name(m["project_id"], profile.id)
        source = video if video.exists() else clip
        g = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", "1", "-i", str(source),
                            "-frames:v", "1", "-y", str(out)])
        if g.returncode != 0:
            return failed_code
        print(f"WARNING: the designed cover failed to render; {out} is a frame grab from {source.name}. "
              "Fix the problem and run --cover --force for the designed cover.", file=sys.stderr)
        return 0

    def render_video(profile) -> int:
        pprops = props if profile.id == default_id else {**props, "profile": profile.props()}
        pfile = proj / suffixed("props.json", profile)
        pfile.write_text(json.dumps(pprops, ensure_ascii=False, indent=2))
        if a.preview:
            out = proj / suffixed("preview.mp4", profile)
        else:
            out = final_dir / platforms.video_name(m["project_id"], profile.id)
            if out.exists() and not a.force:
                raise FileExistsError(f"{out} exists; use --force to overwrite")
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["npx", "remotion", "render", "src/index.ts", "InspireShort", str(out),
               f"--props={pfile}", "--codec=h264", "--crf=18", *quiet_log()]
        if a.preview:
            cmd += ["--scale=0.5"]
        print("+", " ".join(cmd))
        r = subprocess.run(cmd, cwd=ROOT / "video")
        if r.returncode == 0:
            print(f"Rendered: {out}")
            if not a.preview:
                return render_cover(profile, overwrite=True)  # the cover always ships with the video
        return r.returncode

    for profile in targets:
        code = render_cover(profile) if a.cover else render_video(profile)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
