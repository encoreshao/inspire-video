"""Screenshots of web pages with a headless Chrome/Chromium (no extra dependencies)."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
CHROME_NAMES = ("google-chrome", "chromium", "chromium-browser", "chrome")
SIZES = (("desktop", 1440, 900), ("phone", 390, 844))
TIMEOUT = 60


class CaptureError(RuntimeError):
    pass


def find_chrome(exists=os.path.exists, which=shutil.which):
    for p in CHROME_PATHS:
        if exists(p):
            return p
    for name in CHROME_NAMES:
        found = which(name)
        if found:
            return found
    return None


def capture_command(chrome, url, out, width, height, profile) -> list[str]:
    return [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", f"--user-data-dir={profile}", f"--window-size={width},{height}",
            "--virtual-time-budget=8000", f"--screenshot={out}", url]


def capture_pages(urls, out_dir, chrome=None, run=subprocess.run, sizes=SIZES, prefix="capture"):
    chrome = chrome or find_chrome()
    if not chrome:
        raise CaptureError("no Chrome or Chromium found for page screenshots: install one, or pass your own --screenshots")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    captures, failures = [], []
    for i, url in enumerate(urls, 1):
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            failures.append({"url": url, "reason": "only http(s) pages can be captured"})
            continue
        for kind, width, height in sizes:
            out = out_dir / f"{prefix}-{i:02d}-{kind}.png"
            out.unlink(missing_ok=True)
            with tempfile.TemporaryDirectory() as profile:
                try:
                    run(capture_command(chrome, url, out, width, height, profile), check=True,
                        capture_output=True, text=True, timeout=TIMEOUT)
                except subprocess.CalledProcessError as e:
                    tail = (e.stderr or "").strip().splitlines()[-1:] or [str(e)]
                    failures.append({"url": url, "reason": f"browser failed: {tail[0]}"})
                    break
                except subprocess.TimeoutExpired:
                    failures.append({"url": url, "reason": f"browser timed out after {TIMEOUT} s"})
                    break
            if not out.exists() or out.stat().st_size == 0:
                failures.append({"url": url, "reason": "the browser produced no screenshot"})
                break
            captures.append({"path": str(out), "url": url, "kind": kind})
    return captures, failures
