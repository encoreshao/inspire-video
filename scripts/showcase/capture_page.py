#!/usr/bin/env python3
"""Capture a web page at 2x with a layout of its elements, for the promo style.

  python scripts/showcase/capture_page.py <url> --project output/projects/<slug> [--hide CSS]... [--allow-private]

Needs Playwright and an installed Chrome (python3 -m pip install 'playwright>=1.40'; no browser is downloaded).
Writes <project>/assets/promo-<n>@2x.png and promo-<n>.layout.json, and registers the image in brief.json as a
capture whose rights are unresolved.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from showcase import page_layout as L  # noqa: E402
from showcase.capture import CaptureError  # noqa: E402

GOTO_MS = 30_000
IDLE_MS = 8_000
SETTLE_MS = 600
FREEZE_CSS = ("*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}"
              "html{scroll-behavior:auto!important}")
# Scroll down in steps so lazy images load, then back to the top. Never past the capture cap.
SCROLL_JS = ("async () => { const end = Math.min(document.documentElement.scrollHeight, %d);"
             " for (let y = 0; y < end; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }"
             " window.scrollTo(0, 0); }") % L.MAX_PAGE_H


def _check_hide(hide) -> None:
    for selector in hide:
        if not selector.strip() or any(c in selector for c in "{};"):
            raise CaptureError(f"--hide selector {selector!r} must be a plain CSS selector (no braces or semicolons)")


def capture_page(url, out_dir, index: int, hide=(), host_check=None, project=None) -> dict:
    _check_hide(hide)
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeout
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise CaptureError("Playwright is not installed: run python3 -m pip install 'playwright>=1.40' "
                           "(it drives your installed Chrome; no browser is downloaded)") from None
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    image = out_dir / f"promo-{index}{L.SUFFIX}"
    layout_file = L.layout_path_for(image)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            try:
                context = browser.new_context(viewport={"width": L.VIEWPORT["w"], "height": L.VIEWPORT["h"]},
                                              device_scale_factor=L.SCALE, reduced_motion="reduce")
                page = context.new_page()
                page.goto(url, wait_until="load", timeout=GOTO_MS)
                try:
                    page.wait_for_load_state("networkidle", timeout=IDLE_MS)
                except PlaywrightTimeout:
                    pass                                    # a page that never goes idle is still captured
                final = urlsplit(page.url)
                if host_check and final.scheme in ("http", "https") and not host_check(final.hostname or ""):
                    raise CaptureError(f"the page ended up on {final.hostname}, which is not a public host; "
                                       "pass --allow-private only for your own local sites")
                page.add_style_tag(content=FREEZE_CSS)
                if hide:
                    page.add_style_tag(content=", ".join(hide) + " { display: none !important; }")
                page.evaluate(SCROLL_JS)
                page.wait_for_timeout(SETTLE_MS)
                width, height = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight]")
                page_w, page_h = int(width), min(int(height), L.MAX_PAGE_H)
                raw = page.evaluate(L.JS_COLLECT)
                page.screenshot(path=str(image), full_page=True,
                                clip={"x": 0, "y": 0, "width": page_w, "height": page_h})
            finally:
                browser.close()
    except PlaywrightError as e:
        raise CaptureError(f"browser capture failed: {str(e).splitlines()[0] if str(e) else type(e).__name__}") from None
    try:
        rel = image.relative_to(project).as_posix() if project else image.name
    except ValueError:
        rel = image.name
    layout = L.build_layout(raw, url=url, page_w=page_w, page_h=page_h, image=rel)
    L.validate_layout(layout)
    layout_file.write_text(json.dumps(layout, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"image": image, "layout": layout_file, "layout_data": layout}
