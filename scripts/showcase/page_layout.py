"""The layout of a captured page: element boxes in page pixels, the contract between capture and the promo style.

A layout file sits beside its image: assets/promo-1@2x.png has assets/promo-1.layout.json. The capture step
(capture_page.py) collects raw rectangles in the browser with JS_COLLECT; build_layout turns them into the file.
Everything here is pure, so it is tested without a browser.
"""
from __future__ import annotations

import json
from pathlib import Path

VERSION = 1
SCALE = 2
VIEWPORT = {"w": 1440, "h": 900}
MAX_PAGE_H = 6000          # CSS px; the image is twice that. A taller page is cut here.
MAX_ELEMENTS = 40
MAX_TEXT = 80
MIN_W, MIN_H = 24, 16      # smaller boxes are not worth a camera move
MERGE_IOU = 0.9            # boxes overlapping more than this (intersection over union) are one element
ROLES = ("heading", "button", "card", "image", "code", "nav")      # priority order: earlier wins a duplicate
SUFFIX = "@2x.png"

# Runs in the page (Playwright page.evaluate). Returns visible elements as page-coordinate rectangles.
JS_COLLECT = r"""() => {
  const SELECTORS = [
    ["heading", "h1, h2, h3"],
    ["button", "button, [role=button], a[class*=btn], a[class*=button]"],
    ["card", "article, [class*=card]"],
    ["image", "img, picture, video"],
    ["code", "pre"],
    ["nav", "nav"],
  ];
  const seen = new Set();
  const out = [];
  for (const [role, selector] of SELECTORS) {
    for (const el of document.querySelectorAll(selector)) {
      if (seen.has(el)) continue;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      if (s.display === "none" || s.visibility === "hidden" || parseFloat(s.opacity) === 0) continue;
      if (r.width <= 0 || r.height <= 0) continue;
      seen.add(el);
      const text = (el.innerText || el.alt || el.getAttribute("aria-label") || "").replace(/\s+/g, " ").trim().slice(0, 200);
      out.push({role, text, x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height});
    }
  }
  return out;
}"""


class LayoutError(ValueError):
    pass


def _iou(a: dict, b: dict) -> float:
    ix = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    inter = ix * iy
    union = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / union if union else 0.0


def build_layout(raw: list[dict], *, url: str, page_w: int, page_h: int, image: str) -> dict:
    kept = []
    for r in raw:
        if r.get("role") not in ROLES:
            continue
        x0, y0 = max(0.0, float(r["x"])), max(0.0, float(r["y"]))
        x1, y1 = min(float(page_w), float(r["x"]) + float(r["w"])), min(float(page_h), float(r["y"]) + float(r["h"]))
        x, y = round(x0), round(y0)
        w, h = round(x1) - x, round(y1) - y
        if w < MIN_W or h < MIN_H:
            continue
        text = " ".join(str(r.get("text", "")).split())[:MAX_TEXT]
        kept.append({"role": r["role"], "text": text, "box": {"x": x, "y": y, "w": w, "h": h}})
    kept.sort(key=lambda e: (ROLES.index(e["role"]), -e["box"]["w"] * e["box"]["h"]))
    chosen: list[dict] = []
    for e in kept:
        if not any(_iou(e["box"], c["box"]) > MERGE_IOU for c in chosen):
            chosen.append(e)
    chosen = chosen[:MAX_ELEMENTS]
    chosen.sort(key=lambda e: (e["box"]["y"], e["box"]["x"]))
    counts: dict[str, int] = {}
    elements = []
    for e in chosen:
        counts[e["role"]] = counts.get(e["role"], 0) + 1
        elements.append({"id": f"{e['role']}-{counts[e['role']]}", **e})
    return {"version": VERSION, "url": url, "scale": SCALE, "viewport": dict(VIEWPORT),
            "page": {"w": int(page_w), "h": int(page_h)}, "image": image, "elements": elements}


def validate_layout(layout: dict) -> None:
    if not isinstance(layout, dict) or layout.get("version") != VERSION:
        raise LayoutError(f"layout version must be {VERSION}")
    if not isinstance(layout.get("scale"), int) or layout["scale"] < 1:
        raise LayoutError("layout scale must be a positive integer")
    for key in ("viewport", "page"):
        v = layout.get(key)
        if not (isinstance(v, dict) and all(isinstance(v.get(k), int) and v[k] > 0 for k in ("w", "h"))):
            raise LayoutError(f"layout {key} needs positive integer w and h")
    if not isinstance(layout.get("url"), str) or not isinstance(layout.get("image"), str):
        raise LayoutError("layout url and image must be strings")
    elements = layout.get("elements")
    if not isinstance(elements, list):
        raise LayoutError("layout elements must be a list")
    seen: set[str] = set()
    page = layout["page"]
    for e in elements:
        if e.get("role") not in ROLES:
            raise LayoutError(f"element {e.get('id')!r}: unknown role {e.get('role')!r}")
        if e.get("id") in seen:
            raise LayoutError(f"duplicate element id {e['id']!r}")
        seen.add(e["id"])
        b = e.get("box")
        ok = isinstance(b, dict) and all(isinstance(b.get(k), int) for k in ("x", "y", "w", "h"))
        if not ok or b["x"] < 0 or b["y"] < 0 or b["w"] <= 0 or b["h"] <= 0 \
                or b["x"] + b["w"] > page["w"] or b["y"] + b["h"] > page["h"]:
            raise LayoutError(f"element {e['id']!r}: box is outside the page")


def load_layout(path) -> dict:
    try:
        layout = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise LayoutError(f"cannot read the layout file {path}: {e}") from None
    validate_layout(layout)
    return layout


def find_element(layout: dict, element_id: str) -> dict | None:
    for e in layout["elements"]:
        if e["id"] == element_id:
            return e["box"]
    return None


def layout_path_for(image) -> Path:
    name = str(image)
    if not name.endswith(SUFFIX):
        raise LayoutError(f"{name} is not a promo capture: its name must end with {SUFFIX}")
    return Path(name[: -len(SUFFIX)] + ".layout.json")
