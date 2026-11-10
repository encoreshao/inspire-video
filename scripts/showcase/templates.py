#!/usr/bin/env python3
"""Showcase templates: whole-video recipes (look, shot palette, pacing) that a user picks for a promo.

  python scripts/showcase/templates.py list [--json]
  python scripts/showcase/templates.py show <id> [--json]
  python scripts/showcase/templates.py validate [<id>]

A template is templates/<id>.yaml. The shots it names live in video/src/showcase/shots.json.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from showcase.manifest import PROMO_SHOTS, THEMES  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "templates"
SAMPLE_DIR = TEMPLATE_DIR / "sample"
DEFAULT_TEMPLATE = "cinematic"
TEMPLATE_STYLES = ("promo",)
TRANSITIONS = ("dissolve",)
TEMPLATE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
KEYS = {"id", "name", "name_zh", "description", "style", "theme", "shots", "opening", "closing", "transition", "pacing"}
MIN_SHOTS, MIN_UNLIMITED_CAMERA = 3, 2


class TemplateError(ValueError):
    pass


def _text(data: dict, key: str, required: bool = True):
    v = data.get(key)
    if v is None and not required:
        return None
    if not isinstance(v, str) or not v.strip():
        raise TemplateError(f"{key} must be a non-empty string")
    return v.strip()


def _int(v, minimum: int = 1) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= minimum


def effective_max(entry: dict) -> int | None:
    """The most times a template's shot entry may appear in one video: its own `max` and the shot's `maxPerVideo`."""
    limits = [x for x in (entry.get("max"), PROMO_SHOTS[entry["id"]]["maxPerVideo"]) if x is not None]
    return min(limits) if limits else None


def validate_template(data, stem: str) -> dict:
    if not isinstance(data, dict):
        raise TemplateError("a template must be a mapping")
    extra = sorted(set(data) - KEYS)
    if extra:
        raise TemplateError(f"unknown key {extra[0]!r}; allowed: {', '.join(sorted(KEYS))}")
    tid = data.get("id")
    if not isinstance(tid, str) or not TEMPLATE_ID.fullmatch(tid):
        raise TemplateError("id must be lowercase letters, digits and '-' (at most 40 characters)")
    if tid != stem:
        raise TemplateError(f"id {tid!r} must equal the file name {stem!r}")
    if data.get("style") not in TEMPLATE_STYLES:
        raise TemplateError(f"style must be one of {TEMPLATE_STYLES}")
    theme = data.get("theme")
    if theme is not None and theme not in THEMES:
        raise TemplateError(f"theme must be one of {THEMES}")
    transition = data.get("transition", "dissolve")
    if transition not in TRANSITIONS:
        raise TemplateError(f"transition must be one of {TRANSITIONS}")
    shots_in = data.get("shots")
    if not isinstance(shots_in, list) or not shots_in:
        raise TemplateError("shots must be a non-empty list of {id, weight, max}")
    shots, seen = [], set()
    for e in shots_in:
        if not isinstance(e, dict) or set(e) - {"id", "weight", "max"}:
            raise TemplateError("each shots entry takes only id, weight and max")
        sid = e.get("id")
        if sid not in PROMO_SHOTS:
            raise TemplateError(f"unknown shot {sid!r}; use one of {', '.join(PROMO_SHOTS)}")
        if sid in seen:
            raise TemplateError(f"shot {sid!r} is listed twice")
        seen.add(sid)
        if not _int(e.get("weight")):
            raise TemplateError(f"the weight of {sid!r} must be a whole number of at least 1")
        if e.get("max") is not None:
            if not _int(e["max"]):
                raise TemplateError(f"the max of {sid!r} must be a whole number of at least 1")
            cap = PROMO_SHOTS[sid]["maxPerVideo"]
            if cap is not None and e["max"] > cap:
                raise TemplateError(f"the max of {sid!r} is {e['max']} but the shot allows only {cap} per video")
        shots.append({"id": sid, "weight": e["weight"], "max": e.get("max")})
    if len(shots) < MIN_SHOTS:
        raise TemplateError(f"a template needs at least {MIN_SHOTS} shots (three, so a video can vary)")
    unlimited = [s for s in shots if effective_max(s) is None and PROMO_SHOTS[s["id"]]["needsTarget"]
                 and not PROMO_SHOTS[s["id"]]["needsTallPage"]]
    if len(unlimited) < MIN_UNLIMITED_CAMERA:
        raise TemplateError(f"a template needs at least {MIN_UNLIMITED_CAMERA} unlimited camera shots that work on any page "
                            f"(hero-push, spotlight-focus), or a video cannot avoid repeating a shot back to back")
    opening, closing = data.get("opening"), data.get("closing")
    for key, sid in (("opening", opening), ("closing", closing)):
        if sid is not None and sid not in seen:
            raise TemplateError(f"{key} {sid!r} is not in the shots list")
    unlimited_ids = {s["id"] for s in unlimited}
    for key, sid in (("opening", opening), ("closing", closing)):
        if sid in unlimited_ids and len(unlimited) < MIN_UNLIMITED_CAMERA + 1:
            raise TemplateError(f"{key} {sid!r} is an unlimited camera shot: with only {len(unlimited)} of them a video of some "
                                f"lengths could not place it without repeating a shot, so add a third unlimited camera shot "
                                f"or use a statement or the punch for the {key}")
    if opening is not None and opening == closing:
        by_id = {s["id"]: s for s in shots}
        limit = effective_max(by_id[opening])
        if limit is not None and limit < 2:
            raise TemplateError(f"closing {closing!r} cannot repeat the opening: the shot is allowed only {limit} time per video")
    pacing = data.get("pacing")
    if pacing is not None:
        bs = pacing.get("beat_seconds") if isinstance(pacing, dict) else None
        ok = (isinstance(bs, list) and len(bs) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in bs)
              and 4 <= bs[0] <= bs[1] <= 20)
        if not ok:
            raise TemplateError("pacing.beat_seconds must be [low, high] with 4 <= low <= high <= 20")
        pacing = {"beat_seconds": [bs[0], bs[1]]}
    return {"id": tid, "name": _text(data, "name"), "name_zh": _text(data, "name_zh", False),
            "description": _text(data, "description"), "style": data["style"], "theme": theme, "shots": shots,
            "opening": opening, "closing": closing, "transition": transition, "pacing": pacing}


def load_templates(directory: Path = TEMPLATE_DIR) -> dict[str, dict]:
    directory = Path(directory)
    if not directory.is_dir():
        return {}
    out = {}
    for path in sorted(directory.glob("*.yaml")):
        try:
            out[path.stem] = validate_template(yaml.safe_load(path.read_text(encoding="utf-8")), path.stem)
        except (TemplateError, yaml.YAMLError, OSError, ValueError, TypeError) as e:   # a typo must name its file, never a traceback
            raise TemplateError(f"{path.name}: {e}") from None
    return dict(sorted(out.items()))


def get_template(template_id, directory: Path = TEMPLATE_DIR) -> dict:
    loaded = load_templates(directory)
    if not isinstance(template_id, str) or template_id not in loaded:
        known = ", ".join(loaded) or "none installed"
        raise TemplateError(f"unknown template {template_id!r}; use one of: {known}")
    return loaded[template_id]


def suggest_shots(template: dict, n: int) -> list[str]:
    """A shot for each of n beats: the opening and closing first, the rest by weight (smooth weighted round robin), never
    the same shot twice in a row and never over a shot's limit. Deterministic."""
    shots = template["shots"]
    weight = {s["id"]: s["weight"] for s in shots}
    limit = {s["id"]: effective_max(s) for s in shots}
    total = sum(weight.values())
    credit = {sid: 0 for sid in weight}
    used, seq = Counter(), []
    opening, closing = template["opening"], template["closing"]
    for i in range(n):
        if i == 0 and opening:
            pick = opening
        elif i == n - 1 and closing:
            pick = closing
        else:
            for sid in credit:
                credit[sid] += weight[sid]

            def ok(sid):
                if seq and seq[-1] == sid:
                    return False
                if sid == closing:                       # keep one use for the closing beat, and never sit next to it
                    return i != n - 2 and (limit[sid] is None or used[sid] < limit[sid] - 1)
                return limit[sid] is None or used[sid] < limit[sid]
            choices = [sid for sid in credit if ok(sid)]
            if not choices:
                raise TemplateError(f"template {template['id']!r} cannot fill {n} beats without repeating a shot back to back")
            pick = max(choices, key=lambda s: credit[s])
            credit[pick] -= total
        seq.append(pick)
        used[pick] += 1
    return seq


def catalogue(directory: Path = TEMPLATE_DIR) -> list[dict]:
    directory = Path(directory)
    rows = []
    for t in load_templates(directory).values():
        cover = directory / "covers" / f"{t['id']}.png"
        clip = directory / "covers" / f"{t['id']}.mp4"
        rows.append({**t, "cover": f"templates/covers/{t['id']}.png" if cover.is_file() else None,
                     "preview": f"templates/covers/{t['id']}.mp4" if clip.is_file() else None})
    return rows


# What each shot films in a preview: the text of the element it lands on in the bundled sample page, and its caption.
SAMPLE_BEATS = {
    "hero-push": ("Ship launches", "A slow push lands on the headline.", "缓缓推近，落在标题上。"),
    "spotlight-focus": ("Plan", "Everything else dims, so one card is read.", "其余变暗，只读这一张卡。"),
    "crash-zoom-punch": ("Start free", "One punch makes this moment land.", "一记冲击，让此刻落地。"),
    "pan-reveal": ("launch analytics chart", "Travel down the page to the chart.", "沿页面一路滑到图表。"),
    "pull-back-isolate": ("98%", "Pull back and only one thing is left.", "拉远之后，只剩这一件事。"),
    "crane-rise": ("12k teams", "From one number to the whole page.", "从一个数字升到整页。"),
    "cursor-tour": ("See a demo", "A cursor shows where to click.", "光标指出该点哪里。"),
    "scroll-brake": ("Make your next launch", "A fast scroll brakes on the call to action.", "快速下滑，停在行动号召上。"),
    "statement": ("", "A launch day, handled.", "发布日，从容应对。"),
}


def preview_shots(template: dict) -> list[str]:
    """The shots a preview films: the opening, each other shot of the palette once (heaviest first), the closing."""
    ends = {template["opening"], template["closing"]} - {None}
    middle = [s["id"] for s in sorted(template["shots"], key=lambda s: -s["weight"]) if s["id"] not in ends]
    return ([template["opening"]] if template["opening"] else []) + middle + ([template["closing"]] if template["closing"] else [])


def build_sample_project(template: dict, dest: Path) -> Path:
    """A throwaway promo project of the bundled sample page, with one beat for each shot of the template's palette."""
    from showcase import page_layout as L
    dest = Path(dest)
    (dest / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SAMPLE_DIR / "page@2x.png", dest / "assets" / "page@2x.png")
    shutil.copy2(SAMPLE_DIR / "page.layout.json", dest / "assets" / "page.layout.json")
    layout = L.load_layout(dest / "assets" / "page.layout.json")
    seen: Counter = Counter()
    beats, seconds = [], []
    for shot in preview_shots(template):
        needle, en, zh = SAMPLE_BEATS[shot]
        seen[shot] += 1
        beat = {"id": shot if seen[shot] == 1 else f"{shot}-{seen[shot]}", "en": en, "zh": zh, "shot": shot}
        if PROMO_SHOTS[shot]["needsTarget"]:
            element = next((e for e in layout["elements"] if needle.lower() in e["text"].lower()), layout["elements"][0])
            beat.update(asset="assets/page@2x.png", target=element["id"])
        else:
            beat["statement"] = "Launch day, handled."
        beats.append(beat)
        seconds.append(float(max(PROMO_SHOTS[shot]["minSeconds"], 4 if shot == "statement" else 6)))
    m = {"type": "showcase", "project_id": f"preview-{template['id']}", "style": template["style"], "template": template["id"],
         "sample": True, "sample_seconds": seconds, "headline": "每一次发布都值得记住", "subtitle": f"Template preview: {template['name']}",
         "project": {"name": "Northwind", "name_zh": "北风", "tagline": "Plan, write, publish", "tagline_zh": "计划、撰写、发布"},
         "source": {"kind": "website", "url": "https://northwind.example/", "label": "northwind.example"},
         "beats": beats, "provenance": {"rights_confirmed": True, "source_reference": "templates/sample (drawn for this tool)"}}
    if template["theme"]:
        m["theme"] = template["theme"]
    (dest / "video_manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return dest


def preview(template_id, directory: Path = TEMPLATE_DIR) -> Path:
    """Render the template's sample clip (half scale) and a cover frame into <directory>/covers/. Returns the clip's path."""
    from showcase import render_showcase as R
    t = get_template(template_id, directory)
    if shutil.which("ffmpeg") is None:
        raise TemplateError("ffmpeg is needed to write the preview cover")
    covers = Path(directory) / "covers"
    covers.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        project = build_sample_project(t, Path(tmp) / "proj")
        rc = R.main([str(project), "--preview"])
        if rc != 0:
            raise TemplateError(f"the preview render of {t['id']!r} failed (exit {rc})")
        clip = covers / f"{t['id']}.mp4"
        shutil.copy2(project / "preview.mp4", clip)
        m = json.loads((project / "video_manifest.json").read_text(encoding="utf-8"))
    start = 0.0
    for beat, secs in zip(m["beats"], m["sample_seconds"]):
        if beat["shot"] != "statement":
            start += 0.7 * secs                       # inside the first camera move, after it has travelled
            break
        start += secs
    still = covers / f"{t['id']}.png"
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-i", str(clip), "-frames:v", "1", str(still)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise TemplateError(f"could not write the cover frame: {r.stderr.strip()[:200]}")
    return clip


def _print_template(t: dict) -> None:
    zh = f" / {t['name_zh']}" if t.get("name_zh") else ""
    print(f"{t['id']}  {t['name']}{zh}\n  {t['description']}\n  style {t['style']}, theme {t['theme'] or 'default'}, "
          f"shots: {', '.join(s['id'] for s in t['shots'])}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Showcase templates")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--json", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("id")
    sh.add_argument("--json", action="store_true")
    va = sub.add_parser("validate")
    va.add_argument("id", nargs="?")
    pv = sub.add_parser("preview", help="render the short sample clip and cover of a template into templates/covers/")
    pv.add_argument("id", nargs="?")
    pv.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "list":
            rows = catalogue()
            if a.json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
            else:
                for r in rows:
                    _print_template(r)
        elif a.cmd == "show":
            t = get_template(a.id)
            if a.json:
                print(json.dumps(t, ensure_ascii=False, indent=1))
            else:
                _print_template(t)
        elif a.cmd == "preview":
            ids = list(load_templates()) if a.all else [a.id]
            if not ids or ids == [None]:
                raise TemplateError("give a template id, or --all")
            for tid in ids:
                get_template(tid)
            for tid in ids:
                print(f"preview written: {preview(tid)}")
        else:
            loaded = load_templates()
            if a.id:
                get_template(a.id)
            print(f"{1 if a.id else len(loaded)} template(s) valid")
    except TemplateError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
