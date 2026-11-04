#!/usr/bin/env python3
"""Download a video URL once, with a rights confirmation and a shared cache.

Usage: python scripts/fetch.py <url> [--yes-rights] [--force]

Cache: <skill-root>/output/cache/<extractor>-<id>/{source.mp4,source_metadata.json}
A video already in the cache is never downloaded again (unless --force).
Prints the cached source path on the last stdout line.
"""
import argparse, json, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "output" / "cache"
FORMAT = "bv*[height<=1080]+ba/b[height<=1080]/b"


def die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def probe(url: str) -> dict:
    r = subprocess.run(["yt-dlp", "--dump-single-json", "--no-playlist", "--no-download", url],
                       capture_output=True, text=True)
    if r.returncode != 0:
        die("could not read video metadata (private, removed, login/geo-restricted, or "
            f"unsupported). Provide a local file instead.\n{r.stderr.strip()[-400:]}")
    return json.loads(r.stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--yes-rights", action="store_true",
                    help="confirm you own the video or are licensed/permitted to reuse it")
    ap.add_argument("--force", action="store_true", help="re-download even if cached")
    a = ap.parse_args()

    if not shutil.which("yt-dlp"):
        die("yt-dlp not found. Install: pip install yt-dlp (or brew install yt-dlp)")

    info = probe(a.url)
    if info.get("is_live") or info.get("live_status") in ("is_live", "is_upcoming"):
        die("live/upcoming streams are not supported")
    if info.get("availability") not in (None, "public", "unlisted"):
        die(f"video availability is '{info.get('availability')}'; not downloading")

    key = f"{info['extractor_key'].lower()}-{info['id']}"
    dest = CACHE / key
    src, meta = dest / "source.mp4", dest / "source_metadata.json"

    if src.exists() and meta.exists() and not a.force:
        print(f"Cached, skipping download: {key}", file=sys.stderr)
        print(src)
        return 0

    print(f"Title:   {info.get('title')}\nChannel: {info.get('channel') or info.get('uploader')}\n"
          f"License: {info.get('license') or 'not stated (standard platform terms)'}\n"
          f"Length:  {info.get('duration')}s", file=sys.stderr)
    if not a.yes_rights:
        if not sys.stdin.isatty():
            die("rights not confirmed; re-run with --yes-rights after confirming you may reuse this video")
        if input("Do you own this video or have permission to reuse it? [y/N] ").strip().lower() != "y":
            die("rights not confirmed; aborting", 2)

    CACHE.mkdir(parents=True, exist_ok=True)
    lock = CACHE / f".{key}.lock"
    try:
        lock.mkdir()  # atomic: prevents two concurrent downloads of the same video
    except FileExistsError:
        if time.time() - lock.stat().st_mtime < 3600:
            die(f"another download of {key} is in progress")
        shutil.rmtree(lock)
        lock.mkdir()
    tmp = CACHE / f".{key}.part"
    try:
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir()
        r = subprocess.run(["yt-dlp", "--no-playlist", "-f", FORMAT, "--merge-output-format", "mp4",
                            "-o", str(tmp / "source.%(ext)s"), a.url])
        if r.returncode != 0 or not (tmp / "source.mp4").exists():
            die("download failed; nothing cached")
        record = {k: info.get(k) for k in ("id", "extractor_key", "title", "channel", "uploader",
                  "upload_date", "license", "duration", "webpage_url", "description")}
        record.update(source_url=a.url, rights_confirmed=True,
                      downloaded_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        (tmp / "source_metadata.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
        if dest.exists():
            shutil.rmtree(dest)
        tmp.rename(dest)  # publish only when complete
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(lock, ignore_errors=True)
    print(src)
    return 0


if __name__ == "__main__":
    sys.exit(main())
