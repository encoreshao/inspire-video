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
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from showcase.manifest import PROMO_SHOTS, THEMES  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "templates"
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
        rows.append({**t, "cover": f"templates/covers/{t['id']}.png" if cover.is_file() else None})
    return rows


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
