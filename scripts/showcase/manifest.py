#!/usr/bin/env python3
"""The showcase video manifest: validation, beat timing and a scaffold built from brief.json.

  python scripts/showcase/manifest.py scaffold <project-dir> [--beats 16]   # write video_manifest.json to fill in
  python scripts/showcase/manifest.py validate <project-dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from showcase import page_layout as L  # noqa: E402
from showcase.assets import AssetError, image_size  # noqa: E402
from showcase.narrate import BEAT_ID  # noqa: E402
from showcase.timing import LengthError, MAX_TOTAL, MIN_TOTAL, check_total  # noqa: E402

THEMES = ("light", "mist", "ivory", "ink", "sage")
STYLES = ("device", "promo")
# The promo shots. Keep equal to shotMeta() in video/src/showcase/shots.mjs (tests/test_showcase_promo.py compares them).
PROMO_SHOTS = {
    "hero-push": {"minSeconds": 4, "maxPerVideo": None, "needsTallPage": False, "needsTarget": True},
    "spotlight-focus": {"minSeconds": 4, "maxPerVideo": None, "needsTallPage": False, "needsTarget": True},
    "crash-zoom-punch": {"minSeconds": 4, "maxPerVideo": 1, "needsTallPage": False, "needsTarget": True},
    "pan-reveal": {"minSeconds": 5, "maxPerVideo": None, "needsTallPage": True, "needsTarget": True},
    "statement": {"minSeconds": 4, "maxPerVideo": 2, "needsTallPage": False, "needsTarget": False},
}
# The punch rule below mirrors the camera in video/src/showcase/shots.mjs (a test compares them over a grid): the stage
# width, the zoom cap, and the punch's fill (0.7), overshoot (3%) and smallest move (5% above the page-fitting zoom).
STAGE_W = 880
STAGE_H = 960
ZOOM_CAP = 3.2
CRASH_FILL, CRASH_OVERSHOOT, CRASH_MIN_MOVE = 0.7, 0.03, 1.05
STATEMENT_UNITS = 28                                   # the statement's width limit (a Chinese character counts as 2)
TALL_PAGE_PX = round(1.5 * L.VIEWPORT["h"])      # "tall" for a pan: at least one and a half capture viewports
MIN_BEATS, MAX_BEATS = 10, 40                       # 2 to 5 minutes at roughly 7 to 12 seconds a beat
FPS = 30
PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def beat_ids(n: int) -> list[str]:
    """Placeholder ids for a scaffold of n beats: a hook, the problem, what it is, numbered detail beats, proof, a call to action."""
    return ["hook", "problem", "what"] + [f"detail-{i:02d}" for i in range(1, n - 4)] + ["proof", "cta"]



SCREEN_ASPECT = {"browser": 846 / 450, "phone": 219 / 444}   # width / height of the device screens in the composition
CALLOUT_UNITS = 22                                             # a Latin letter counts 1, a CJK character 2
MAX_ZH = 45
TOPIC_UNITS = 28                                               # the optional topic label: same width counting as a statement
TOPIC_PUNCTUATION = " &/-.,'·"


class ManifestError(ValueError):
    pass


def _cjk(ch: str) -> bool:
    return ord(ch) >= 0x2E80


def width_units(s: str) -> int:
    return sum(2 if _cjk(c) else 1 for c in s)


def text_px(s: str, latin: float, cjk: float) -> float:
    """Rough rendered width of a line: the layout cannot wrap these lines, so the estimate gates them."""
    return sum(cjk if _cjk(c) else latin for c in s)


def crash_punch_possible(box: dict, page: dict, scale: float) -> bool:
    """Whether crash-zoom-punch would move at all for this target: a target that already fills the frame cannot be punched in on."""
    base = STAGE_W / page["w"]
    z0 = max(1.0, STAGE_H / base / page["h"])
    cap = max(z0, min(ZOOM_CAP, 0.95 * scale / base))
    fit = min(page["w"] / max(1, box["w"]), (STAGE_H / base) / max(1, box["h"])) * CRASH_FILL
    z_final = min(max(fit, z0), cap / (1 + CRASH_OVERSHOOT))
    return z_final >= z0 * CRASH_MIN_MOVE


def page_info(project, asset: str) -> dict:
    """The page size (CSS px), the capture scale and the layout (None without one) for a beat's image."""
    project = Path(project)
    try:
        layout_file = project / L.layout_path_for(asset)
    except L.LayoutError:
        layout_file = None                                  # a user screenshot has no layout
    if layout_file is not None and layout_file.is_file():
        layout = L.load_layout(layout_file)
        iw, ih = image_size(project / asset)
        want_w, want_h = layout["page"]["w"] * layout["scale"], layout["page"]["h"] * layout["scale"]
        if (iw, ih) != (want_w, want_h):                    # a stale image or layout would silently stretch the picture
            raise ManifestError(f"{asset} is {iw}x{ih} but its layout describes a {layout['page']['w']}x{layout['page']['h']} "
                                f"page at {layout['scale']}x ({want_w}x{want_h}); capture the page again")
        return {"page": dict(layout["page"]), "scale": layout["scale"], "layout": layout}
    iw, ih = image_size(project / asset)
    return {"page": {"w": iw, "h": ih}, "scale": 1, "layout": None}


def beat_target(b: dict, project) -> tuple[dict, dict]:
    """The target box in page CSS px (from the element id or the focus rectangle) and the page info."""
    bid = b.get("id")
    try:
        info = page_info(project, b["asset"])
    except ManifestError as e:
        raise ManifestError(f"beat {bid!r}: {e}") from None
    if b.get("target") is not None:
        if info["layout"] is None:
            raise ManifestError(f"beat {bid!r}: target {b['target']!r} needs a layout file beside {b['asset']!r} "
                                f"(capture the page with capture_page.py), or use focus instead")
        box = L.find_element(info["layout"], b["target"])
        if box is None:
            ids = ", ".join(e["id"] for e in info["layout"]["elements"][:12]) or "none"
            raise ManifestError(f"beat {bid!r}: target {b['target']!r} is not an element of the layout; "
                                f"available: {ids}")
        return dict(box), info
    f, page = b["focus"], info["page"]
    box = {"x": round(f["x"] * page["w"]), "y": round(f["y"] * page["h"]),
           "w": round(f["w"] * page["w"]), "h": round(f["h"] * page["h"])}
    if box["w"] < 1 or box["h"] < 1:
        raise ManifestError(f"beat {bid!r}: the focus rectangle is too small: it rounds to {box['w']}x{box['h']} px on the page")
    return box, info


def _check_layout(m: dict) -> None:
    """Refuse text that would not fit the fixed layout (the speaker pipeline warns about long lines; here it is an error)."""
    px = text_px(m["headline"], 24, 43)
    if m.get("style") == "promo" and px > 774:     # the promo cover sets the headline at 92 px: nine Chinese characters a line
        raise ManifestError(f"headline is too wide for the promo cover (about {px:.0f} px, limit 774): use 18 Chinese characters or fewer")
    if px > 852:
        raise ManifestError(f"headline is too wide for one line (about {px:.0f} px, limit 852): use about 19 Chinese characters or fewer")
    if text_px(m["subtitle"], 23.5, 42) > 1500:
        raise ManifestError("subtitle is too long: it must fit in two lines (about 70 characters)")
    p = m["project"]
    name_px = text_px(p["name"], 21, 38) + (18 + text_px(p["name_zh"], 21, 38) if p.get("name_zh") else 0)
    if name_px > 770:
        raise ManifestError("the project name line is too wide: shorten project.name or project.name_zh")
    for key in ("tagline", "tagline_zh"):
        if text_px(p.get(key) or "", 13.5, 25) > 780:
            raise ManifestError(f"project.{key} is too long for one line: shorten it")
    if text_px(m["source"]["label"], 12.5, 22) > 780:
        raise ManifestError("source.label is too long for one line: shorten it")


def crop_warnings(m: dict, project) -> list[str]:
    """Beats whose image shape is far from the device screen: the picture is cropped to fit (never stretched)."""
    if m.get("style", "device") == "promo":
        return []
    out = []
    for b in m["beats"]:
        iw, ih = image_size(Path(project) / b["asset"])
        kind = "phone" if ih / iw >= 1.3 else "browser"
        target, aspect = SCREEN_ASPECT[kind], iw / ih
        if max(aspect / target, target / aspect) > 1.4:
            shape = "browser window (about 16:10)" if kind == "browser" else "phone screen (about 9:19)"
            out.append(f"beat {b['id']!r}: the {iw}x{ih} image will be cropped a lot to fit the {kind} frame; "
                       f"a screenshot shaped like a {shape} works best")
    return out


def beat_seconds_list(m: dict, timings: dict | None = None) -> list[float]:
    if timings:
        return [float(b["seconds"]) for b in timings["beats"]]
    n = len(m["beats"])
    return [round(max(4.0, MIN_TOTAL / n), 2)] * n


def frame_windows(seconds: list[float], fps: int = FPS) -> list[dict]:
    out, acc, start = [], 0.0, 0
    for s in seconds:
        acc += s * fps
        frames = max(1, round(acc) - start)
        out.append({"start": start, "frames": frames})
        start += frames
    return out


def _text(m: dict, key: str, where: str = "") -> str:
    v = m.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ManifestError(f"{where}{key} is required")
    return v


def _check_focus(f, bid) -> None:
    ok = isinstance(f, dict) and all(isinstance(f.get(k), (int, float)) and not isinstance(f.get(k), bool) for k in "xywh")
    if not ok or not (0 <= f["x"] <= 1 and 0 <= f["y"] <= 1 and 0 < f["w"] <= 1 and 0 < f["h"] <= 1
                      and f["x"] + f["w"] <= 1.001 and f["y"] + f["h"] <= 1.001):
        raise ManifestError(f"beat {bid!r}: focus must be x, y in [0,1], w, h in (0,1] and stay inside the image")


def topic_valid(topic) -> bool:
    """The rule video/src/showcase/transitions.mjs applies to a beat's `topic` label (keep the two equal): letters, digits and
    CJK with a little punctuation, starting with a letter or digit and ending with a letter, digit or '.', at most 28 width units."""
    if not isinstance(topic, str) or not topic:
        return False
    if not topic[0].isalnum() or not (topic[-1].isalnum() or topic[-1] == "."):
        return False
    return all(ch.isalnum() or ch in TOPIC_PUNCTUATION for ch in topic) and width_units(topic) <= TOPIC_UNITS


def _check_beat(b: dict, project: Path, style: str = "device") -> None:
    bid = b.get("id")
    if "topic" in b and not topic_valid(b["topic"]):
        raise ManifestError(f"beat {bid!r}: topic must be a short label of letters, digits and CJK (at most {TOPIC_UNITS} width units, "
                            f"a Chinese character counts as 2), for example 'Our services' or 'Our services · 服务'")
    for key in ("en", "zh"):
        if not isinstance(b.get(key), str) or not b[key].strip():
            raise ManifestError(f"beat {bid!r}: {key} is required")
    if len(b["en"]) > 100:
        raise ManifestError(f"beat {bid!r}: en is {len(b['en'])} characters; keep it to 100 or fewer")
    if re.search(r'[.!?]["”\']?\s+[A-Z“"]', b["en"].strip()):
        raise ManifestError(f"beat {bid!r}: en holds more than one sentence; use one sentence per beat")
    if len(b["zh"]) > MAX_ZH:
        raise ManifestError(f"beat {bid!r}: zh is {len(b['zh'])} characters; keep it to {MAX_ZH} or fewer")
    if style == "promo":
        if b.get("callout") is not None:
            raise ManifestError(f"beat {bid!r}: callout is not used in the promo style (spotlight-focus replaces the ring)")
        if not isinstance(b.get("shot", "hero-push"), str):
            raise ManifestError(f"beat {bid!r}: shot must be one of {', '.join(PROMO_SHOTS)}")
        if PROMO_SHOTS.get(b.get("shot", "hero-push"), {}).get("needsTarget") is False:
            _check_promo_beat(b, project)                  # a statement shows no capture, so there is no asset to check
            return
    else:
        callout = b.get("callout")
        if callout is not None and (not isinstance(callout, str) or width_units(callout) > CALLOUT_UNITS):
            raise ManifestError(f"beat {bid!r}: callout must be short: at most {CALLOUT_UNITS} width units "
                                f"(a Chinese character counts as 2, so about 11 Chinese characters or 22 letters)")
        _check_focus(b.get("focus"), bid)
    asset = b.get("asset")
    if not isinstance(asset, str) or not asset or Path(asset).is_absolute():
        raise ManifestError(f"beat {bid!r}: asset must be a path relative to the project folder")
    path = (project / asset).resolve()
    if not path.is_relative_to(project.resolve()) or not path.is_file():
        raise ManifestError(f"beat {bid!r}: asset {asset!r} is not a file inside the project folder")
    try:
        image_size(path)
    except AssetError as e:
        raise ManifestError(f"beat {bid!r}: asset {asset!r} is not a usable image ({e})") from None
    if style == "promo":
        _check_promo_beat(b, project)


def _check_promo_beat(b: dict, project: Path) -> None:
    bid = b.get("id")
    shot = b.get("shot", "hero-push")
    if shot not in PROMO_SHOTS:
        raise ManifestError(f"beat {bid!r}: unknown shot {shot!r}; use one of {', '.join(PROMO_SHOTS)}")
    has_target, has_focus = b.get("target") is not None, b.get("focus") is not None
    if not PROMO_SHOTS[shot]["needsTarget"]:
        for key in ("asset", "target", "focus"):
            if b.get(key) is not None:
                raise ManifestError(f"beat {bid!r}: a {shot} beat shows no capture; remove {key}")
        text = b.get("statement")
        if not isinstance(text, str) or not text.strip():
            raise ManifestError(f"beat {bid!r}: a {shot} beat needs its statement text")
        if width_units(text) > STATEMENT_UNITS:
            raise ManifestError(f"beat {bid!r}: the statement is too wide ({width_units(text)} width units, at most "
                                f"{STATEMENT_UNITS}: about 14 Chinese characters or 28 letters)")
        return
    if b.get("statement") is not None:
        raise ManifestError(f"beat {bid!r}: statement is only for the statement shot")
    if has_target == has_focus:
        raise ManifestError(f"beat {bid!r}: give exactly one of target (an element id) and focus (a rectangle)")
    if has_target and (not isinstance(b["target"], str) or not b["target"].strip()):
        raise ManifestError(f"beat {bid!r}: target must be an element id such as heading-1")
    if has_focus:
        _check_focus(b["focus"], bid)
    try:
        box, info = beat_target(b, project)               # the element and the layout must exist and be valid
    except L.LayoutError as e:
        raise ManifestError(f"beat {bid!r}: {e}") from None
    if shot == "crash-zoom-punch" and not crash_punch_possible(box, info["page"], info["scale"]):
        raise ManifestError(f"beat {bid!r}: the target is too large for crash-zoom-punch (the camera would not move and the "
                            f"once-per-video punch would be wasted); pick a smaller element, or use hero-push")
    if PROMO_SHOTS[shot]["needsTallPage"] and info["page"]["h"] < TALL_PAGE_PX:
        raise ManifestError(f"beat {bid!r}: shot {shot!r} needs a tall page (at least {TALL_PAGE_PX} px) but this one is "
                            f"{info['page']['h']} px; use hero-push or spotlight-focus instead")


def _check_promo_sequence(beats: list, seconds: list) -> None:
    shots = [b.get("shot", "hero-push") for b in beats]
    for before, after, a, c in zip(beats, beats[1:], shots, shots[1:]):
        if a == c:
            raise ManifestError(f"beats {before['id']!r} and {after['id']!r} use the same shot {a!r} back to back; "
                                f"one idea per beat, so vary the shot")
    for name, meta in PROMO_SHOTS.items():
        limit = meta["maxPerVideo"]
        if limit is not None and shots.count(name) > limit:
            raise ManifestError(f"shot {name!r} is used {shots.count(name)} times; use it at most {limit} time(s) per video")
    for beat, secs, shot in zip(beats, seconds, shots):
        if secs < PROMO_SHOTS[shot]["minSeconds"]:
            raise ManifestError(f"beat {beat['id']!r} is {secs:g} s but shot {shot!r} needs at least "
                                f"{PROMO_SHOTS[shot]['minSeconds']} s")


def validate_showcase(m: dict, project, timings: dict | None = None) -> None:
    project = Path(project)
    if m.get("type") != "showcase":
        raise ManifestError("type must be 'showcase'")
    if not isinstance(m.get("project_id"), str) or not PROJECT_ID.fullmatch(m["project_id"]):
        raise ManifestError("project_id must be lowercase letters, digits and '-' (at most 64 characters)")
    style = m.get("style", "device")
    if style not in STYLES:
        raise ManifestError(f"style must be one of {STYLES}")
    if m.get("theme", "light") not in THEMES:
        raise ManifestError(f"theme must be one of {THEMES}")
    _text(m, "headline")
    _text(m, "subtitle")
    proj = m.get("project")
    if not isinstance(proj, dict) or not isinstance(proj.get("name"), str) or not proj["name"].strip():
        raise ManifestError("project.name is required")
    src = m.get("source")
    if not isinstance(src, dict) or not all(isinstance(src.get(k), str) and src.get(k) for k in ("kind", "url", "label")):
        raise ManifestError("source needs kind, url and label")
    _check_layout(m)
    beats = m.get("beats")
    if not isinstance(beats, list) or not all(isinstance(b, dict) for b in beats) or not MIN_BEATS <= len(beats) <= MAX_BEATS:
        raise ManifestError(f"a showcase needs {MIN_BEATS} to {MAX_BEATS} beats")
    seen = set()
    for b in beats:
        bid = b.get("id")
        if not isinstance(bid, str) or not BEAT_ID.fullmatch(bid):
            raise ManifestError(f"invalid beat id {bid!r}")
        if bid in seen:
            raise ManifestError(f"duplicate beat id {bid!r}")
        seen.add(bid)
        _check_beat(b, project, style)
    prov = m.get("provenance")
    if not isinstance(prov, dict) or prov.get("rights_confirmed") is not True:
        raise ManifestError("provenance.rights_confirmed is not true; refusing to render")
    if m.get("voice") and not timings:
        raise ManifestError("the manifest names a voice but there is no timings.json: run narrate first")
    if timings:
        ids = [b.get("id") for b in timings.get("beats", [])]
        if ids != [b["id"] for b in beats]:
            raise ManifestError(f"timings.json is for different beats ({ids}); run narrate again")
        if (m.get("voice") or None) != (timings.get("voice") or None):
            raise ManifestError(f"the manifest names voice {m.get('voice')!r} but timings.json was made with "
                                f"{timings.get('voice')!r}: run narrate again with the same voice")
        lang = timings.get("lang", "en")
        for b, row in zip(beats, timings["beats"]):
            sha = row.get("text_sha")
            if sha and sha != hashlib.sha256((b.get(lang) or "").strip().encode("utf-8")).hexdigest():
                raise ManifestError(f"narration for beat {b['id']!r} is out of date (its text changed): run narrate again")
    if style == "promo":
        _check_promo_sequence(beats, beat_seconds_list(m, timings))
    try:
        check_total(beat_seconds_list(m, timings), MIN_TOTAL, MAX_TOTAL)
    except LengthError as e:
        raise ManifestError(str(e)) from None


def scaffold_manifest(brief: dict, project_id: str, n_beats: int = 16) -> dict:
    assets = [a["path"] for a in brief.get("assets", []) if a.get("role") != "promo-page"]
    if not assets:
        raise ManifestError("the brief has no assets: provide screenshots (or use the terminal style when it exists)")
    n = max(MIN_BEATS, min(MAX_BEATS, n_beats))
    src = brief["source"]
    if src["kind"] == "local":                     # never put a filesystem path into the video
        label = Path(src["url"]).name or "local repository"
    else:
        label = (src.get("repo_path") and f"{src['host']}/{src['repo_path']}") or src.get("host") or src["url"]
    ids = beat_ids(n)
    beats = [{"id": ids[i], "en": "", "zh": "", "asset": assets[i % len(assets)],
              "focus": {"x": 0, "y": 0, "w": 1, "h": 1}} for i in range(n)]
    return {"type": "showcase", "project_id": project_id, "style": "device",
            "headline": "", "subtitle": "", "project": {"name": "", "tagline": ""},
            "source": {"kind": src["kind"], "url": src["url"], "label": label},
            "beats": beats, "provenance": {"rights_confirmed": False, "source_reference": src["url"],
                                           "review_status": "pending"}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Showcase manifest helpers")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("scaffold")
    sc.add_argument("project_dir")
    sc.add_argument("--beats", type=int, default=16)
    va = sub.add_parser("validate")
    va.add_argument("project_dir")
    a = ap.parse_args(argv)
    project = Path(a.project_dir).resolve()
    target = project / "video_manifest.json"
    try:
        if a.cmd == "scaffold":
            if target.exists():
                raise ManifestError(f"{target} already exists; edit it instead")
            brief = json.loads((project / "brief.json").read_text(encoding="utf-8"))
            slug = re.sub(r"[^a-z0-9]+", "-", project.name.lower()).strip("-")[:64] \
                or "showcase-" + hashlib.sha1(project.name.encode("utf-8")).hexdigest()[:8]
            m = scaffold_manifest(brief, slug, a.beats)
            target.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"scaffold written to {target}: fill in headline, subtitle, project, and each beat's en, zh, focus")
        else:
            m = json.loads(target.read_text(encoding="utf-8"))
            tfile = project / "timings.json"
            timings = json.loads(tfile.read_text(encoding="utf-8")) if tfile.exists() else None
            validate_showcase(m, project, timings)
            print("manifest is valid")
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
