#!/usr/bin/env python3
"""Check local prerequisites without exposing environment secrets."""
import importlib.util
import shutil
import sys

def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    checks = {
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
    }
    print(f"yt-dlp (needed only for URLs): {shutil.which('yt-dlp') or 'NOT FOUND - pip install yt-dlp'}")
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
