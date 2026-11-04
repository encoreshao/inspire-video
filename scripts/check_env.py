#!/usr/bin/env python3
"""Check local prerequisites without exposing environment secrets."""
import importlib.util
import re
import shutil
import subprocess
import sys


def js_runtime():
    """YouTube URLs need a JavaScript runtime that yt-dlp supports: Deno, Bun, or Node >= 20.19."""
    for rt in ("deno", "bun"):
        if shutil.which(rt):
            return rt
    if shutil.which("node"):
        v = re.match(r"v(\d+)\.(\d+)", subprocess.run(["node", "--version"], capture_output=True, text=True).stdout)
        if v and (int(v[1]), int(v[2])) >= (20, 19):
            return "node"
    return None


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    checks = {
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
    }
    print(f"yt-dlp (needed only for URLs): {shutil.which('yt-dlp') or 'NOT FOUND - pip install yt-dlp'}")
    rt = js_runtime()
    print(f"js runtime (YouTube URLs only): {rt or 'NOT FOUND - install Deno or Bun (or Node 20.19+) to download from YouTube'}")
    print(f"python:yt_dlp_ejs (YouTube URLs only): {'OK' if importlib.util.find_spec('yt_dlp_ejs') else 'NOT INSTALLED - pip install \"yt-dlp[default]\"'}")
    failed = False
    for name, path in checks.items():
        status = path or "NOT FOUND"
        print(f"{name}: {status}")
        failed |= path is None

    for module in ("yaml", "pydantic", "faster_whisper", "jsonschema"):
        found = importlib.util.find_spec(module) is not None
        print(f"python:{module}: {'OK' if found else 'NOT INSTALLED'}")

    if failed:
        print("\nInstall missing system tools, then run this check again.")
        return 1
    print("\nSystem tools found.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
