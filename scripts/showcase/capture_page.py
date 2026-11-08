#!/usr/bin/env python3
"""Capture a web page at 2x with a layout of its elements, for the promo style.

  python scripts/showcase/capture_page.py <url> --project output/projects/<slug> [--hide CSS]... [--allow-private]
                                          [--nav N]

--nav N also captures up to N pages that the site's header navigation links to (the same site only, public hosts,
robots.txt respected), one capture each, so a 2 to 5 minute video can show a different page for each topic.

Needs Playwright and an installed Chrome (python3 -m pip install 'playwright>=1.40'; no browser is downloaded).
Writes <project>/assets/promo-<n>@2x.png and promo-<n>.layout.json, and registers the image in brief.json as a
capture whose rights are unresolved.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from showcase import assets as A  # noqa: E402
from showcase import ingest as I  # noqa: E402
from showcase import page_layout as L  # noqa: E402
from showcase import webcrawl as W  # noqa: E402
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


def _refuse(host) -> CaptureError:
    return CaptureError(f"{host} is not a public host; pass --allow-private only for your own local sites")


def _check_final(page, host_check) -> None:
    """The page the browser ended up on must be a web page on an allowed host (checked again right before the shot)."""
    if not host_check:
        return
    final = urlsplit(page.url)
    if final.scheme not in ("http", "https"):
        raise CaptureError(f"the page ended up on a non-web address ({final.scheme or 'unknown'}:), "
                           "which is not a public web page; nothing was captured")
    if not host_check(final.hostname or ""):
        raise CaptureError(f"the page ended up on {final.hostname}, which is not a public host; "
                           "pass --allow-private only for your own local sites")


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
    blocked: list[str] = []                       # hosts the guard refused, for the error message
    allowed: dict[str, bool] = {}

    def guard(route):
        """With a host check, the browser may only request web addresses on allowed hosts: no redirect hop,
        sub-resource, frame or script request reaches a private address from the user's machine."""
        target = urlsplit(route.request.url)
        if target.scheme in ("data", "blob", "about"):
            return route.continue_()
        host = target.hostname or ""
        if target.scheme in ("http", "https"):
            if host not in allowed:
                allowed[host] = bool(host_check(host))
            if allowed[host]:
                return route.continue_()
        blocked.append(host or f"{target.scheme}:")
        return route.abort()

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome")
            except PlaywrightError as e:
                raise CaptureError(f"could not start Chrome ({str(e).splitlines()[0]}). Install Google Chrome: this tool drives "
                                   "the installed Chrome and downloads no browser") from None
            try:
                context = browser.new_context(viewport={"width": L.VIEWPORT["w"], "height": L.VIEWPORT["h"]},
                                              device_scale_factor=L.SCALE, reduced_motion="reduce")
                if host_check:
                    context.route("**/*", guard)
                page = context.new_page()
                try:
                    page.goto(url, wait_until="load", timeout=GOTO_MS)
                except PlaywrightError:
                    if blocked:                       # the start page itself was refused by the guard
                        raise _refuse(blocked[0]) from None
                    raise
                try:
                    page.wait_for_load_state("networkidle", timeout=IDLE_MS)
                except PlaywrightTimeout:
                    pass                                    # a page that never goes idle is still captured
                _check_final(page, host_check)
                page.add_style_tag(content=FREEZE_CSS)
                if hide:
                    for selector in hide:                    # one invalid selector would silently disable them all
                        if not page.evaluate("(sel) => { try { document.querySelectorAll(sel); return true; } catch (e) { return false; } }", selector):
                            raise CaptureError(f"--hide selector {selector!r} is not valid CSS")
                    page.add_style_tag(content=", ".join(hide) + " { display: none !important; }")
                page.evaluate(SCROLL_JS)
                page.wait_for_timeout(SETTLE_MS)
                _check_final(page, host_check)            # a script may have navigated away since the first check
                width, height = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.scrollHeight]")
                page_w, page_h = min(int(width), L.MAX_PAGE_W), min(int(height), L.MAX_PAGE_H)
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


def _why_not_public(host: str) -> str:
    """A host the check refuses is either private or simply mistyped; say which."""
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        try:
            socket.getaddrinfo(host, None)
        except OSError:
            return f"{host} could not be resolved: check the address for a typo"
    return f"{host} is not a public host; pass --allow-private only for your own local sites"


def check_url(url, allow_private=False, fetch=None, host_check=None) -> None:
    """The same rules as ingest's crawl: http(s) only, a public host, and robots.txt must allow the page."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise CaptureError("only http(s) pages can be captured")
    if allow_private:
        check = host_check or (lambda host: True)
    else:
        check = host_check or W.is_public_host
    if not check(parts.hostname):
        raise CaptureError(_why_not_public(parts.hostname))
    fetch = fetch or W.make_fetcher(check)
    robots = urllib.robotparser.RobotFileParser()
    try:
        robots.parse(W._decode(fetch(f"{parts.scheme}://{parts.netloc.lower()}/robots.txt")).splitlines())
    except W.CrawlError as e:
        robots.parse(["User-agent: *", "Disallow: /"] if str(e) in ("HTTP 401", "HTTP 403") else [])
    except Exception:  # noqa: BLE001  an unreadable robots.txt does not forbid the page
        robots.parse([])
    if not robots.can_fetch(W.USER_AGENT, url):
        raise CaptureError(f"{url} is disallowed by robots.txt")


def next_index(assets_dir) -> int:
    folder = Path(assets_dir)
    if not folder.is_dir():
        return 1
    pattern = re.compile(rf"promo-(\d+){re.escape(L.SUFFIX)}")
    numbers = [int(m.group(1)) for p in folder.iterdir() if (m := pattern.fullmatch(p.name))]
    return max(numbers, default=0) + 1


def load_brief(project) -> dict:
    """The project's brief.json, parsed and validated; a clear CaptureError when it cannot take a capture."""
    brief_file = Path(project) / "brief.json"
    if not brief_file.is_file():
        raise CaptureError(f"{brief_file} not found: run scripts/showcase/ingest.py for this project first")
    try:
        brief = json.loads(brief_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CaptureError(f"{brief_file} is not readable JSON ({e}); re-run ingest or fix the file") from None
    try:
        I.validate_brief(brief)
    except (I.IngestError, KeyError, TypeError, AttributeError) as e:
        raise CaptureError(f"{brief_file} is not a valid brief ({e}); re-run ingest or fix the file") from None
    return brief


def _write_json_atomic(path: Path, data: dict) -> None:
    """Write beside the target and replace it, so an interrupted write never leaves a truncated file."""
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def register_in_brief(project, image, url) -> dict:
    """Add the capture to brief.json as an unresolved-rights asset (role promo-page), replacing the same path."""
    project = Path(project)
    brief = load_brief(project)
    asset, why = A.try_describe(image, "capture", url, A.rights_note("capture", url))
    if asset is None:
        raise CaptureError(f"the capture is not a usable image: {why}")
    asset = {**asset, "path": Path(image).relative_to(project).as_posix(), "role": "promo-page"}
    brief["assets"] = [a for a in brief["assets"] if a["path"] != asset["path"]] + [asset]
    brief["rights_unresolved"] = True
    I.validate_brief(brief)
    _write_json_atomic(project / "brief.json", brief)
    return asset


MAX_NAV = 12


def nav_pages(url, limit, allow_private=False, fetch=None) -> list[tuple[str, str]]:
    """(url, label) of up to `limit` pages the page's header navigation links to, in the order the header lists them.

    Same site only, and the same rules as ingest's crawl (public host, robots.txt); the page itself is not included."""
    if limit < 1:
        return []
    result = W.crawl(url, fetch=fetch, allow_private=allow_private, max_pages=1)
    if not result.pages:
        return []
    home = result.pages[0]
    labels = {W._norm(link["url"]): link["text"] for link in home.nav_links if link["text"]}
    return [(u, labels.get(W._norm(u), "")) for u in W.select_nav_links(home, limit)]


def _report(asset, result) -> None:
    layout = result["layout_data"]
    roles: dict[str, int] = {}
    for e in layout["elements"]:
        roles[e["role"]] = roles.get(e["role"], 0) + 1
    print(f"captured {asset['path']} ({asset['width']}x{asset['height']}, page {layout['page']['w']}x{layout['page']['h']} px) "
          f"and {result['layout'].name}")
    print("elements: " + (", ".join(f"{n} {role}" for role, n in sorted(roles.items())) or "none"))
    if not layout["elements"]:
        print("warning: no elements found; give each beat a focus rectangle instead of a target", file=sys.stderr)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Capture a page at 2x with an element layout for the promo style")
    ap.add_argument("url")
    ap.add_argument("--project", required=True, help="the project folder (it must already have a brief.json)")
    ap.add_argument("--hide", action="append", default=[], metavar="CSS",
                    help="CSS selector to hide before the shot (a cookie banner, a chat widget); repeatable")
    ap.add_argument("--allow-private", action="store_true", help="allow local or private addresses (your own sites only)")
    ap.add_argument("--nav", type=int, default=0, metavar="N",
                    help=f"also capture up to N pages the header navigation links to (at most {MAX_NAV}; same site, robots.txt respected)")
    ap.add_argument("--index", type=int, help="the number in the file name, 1 or more (default: the next free one); "
                                              "an index that already exists replaces that capture")
    a = ap.parse_args(argv)
    project = Path(a.project)
    try:
        if a.index is not None and a.index < 1:
            raise CaptureError("--index must be 1 or more")
        if not 0 <= a.nav <= MAX_NAV:
            raise CaptureError(f"--nav must be between 0 and {MAX_NAV}")
        if a.nav and a.index is not None:
            raise CaptureError("--nav numbers the captures itself; drop --index")
        load_brief(project)                    # fail before the browser starts, not after the files are written
        check_url(a.url, a.allow_private)
        assets = project / "assets"
        host_check = (lambda host: True) if a.allow_private else W.is_public_host
        result = capture_page(a.url, assets, a.index if a.index is not None else next_index(assets), hide=a.hide, host_check=host_check,
                              project=project)
        asset = register_in_brief(project, result["image"], a.url)
    except (CaptureError, OSError, L.LayoutError, I.IngestError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    _report(asset, result)
    if a.nav:
        host_check = (lambda host: True) if a.allow_private else W.is_public_host
        try:
            pages = nav_pages(a.url, a.nav, a.allow_private)
        except (W.CrawlError, OSError) as e:
            pages = []
            print(f"warning: could not read the header navigation: {e}", file=sys.stderr)
        if not pages:
            print("warning: no header navigation links to capture; capture the pages you want one by one", file=sys.stderr)
        for link, label in pages:
            print(f"header link: {label or '(no text)'} -> {link}")
            try:
                check_url(link, a.allow_private)
                result = capture_page(link, assets, next_index(assets), hide=a.hide, host_check=host_check, project=project)
                _report(register_in_brief(project, result["image"], link), result)
            except (CaptureError, OSError, L.LayoutError, I.IngestError) as e:
                print(f"warning: skipped {link}: {e}", file=sys.stderr)       # one bad page does not stop the others
    print("rights: the capture is registered as unresolved; confirm before a public render "
          "(skills/inspire-showcase/references/rights-and-safety.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
