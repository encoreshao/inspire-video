#!/usr/bin/env python3
"""Get a source video into the shared cache once, after a rights confirmation.

Usage:
  python scripts/fetch.py <url> [--yes-rights] [--force]
  python scripts/fetch.py <url> --cookies-from-browser chrome     # opt-in: use YOUR signed-in browser session
  python scripts/fetch.py <url> --cookies cookies.json            # opt-in: cookies exported from your browser
                                                                    (Netscape cookies.txt, or a JSON list from an extension)
  python scripts/fetch.py --file ./video.mp4 [--source-url URL]   # import a file you downloaded yourself

Cache: <skill-root>/output/cache/<key>/{source.<ext>,source_metadata.json}
  key = <site>-<video id> for URLs, local-<content hash> for files.
A video already in the cache is never fetched or copied again (unless --force).
The last stdout line is the cached source path.

--cookies and --cookies-from-browser are OFF by default. It makes yt-dlp read your browser's YouTube login to get past
a "confirm you're not a bot" check. That can violate the platform's terms and may get the account flagged;
use it only with your own account, at your own risk. Cookies are never stored or logged by this script.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(os.environ.get("INSPIRE_VIDEO_CACHE", ROOT / "output" / "cache"))
FORMAT = "bv*[height<=720]+ba/b[height<=720]/b"  # clips are scaled to 720p, so no need for more
BROWSERS = ["chrome", "firefox", "safari", "edge", "brave", "chromium", "opera", "vivaldi"]


def die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def confirm_rights(a) -> None:
    if a.yes_rights:
        return
    if not sys.stdin.isatty():
        die("rights not confirmed; re-run with --yes-rights after confirming you may reuse this video")
    if input("Do you own this video or have permission to reuse it? [y/N] ").strip().lower() != "y":
        die("rights not confirmed; aborting", 2)


def cached_source(dest: Path):
    if not (dest / "source_metadata.json").exists():
        return None
    for p in sorted(dest.glob("source.*")):
        if p.suffix != ".json":
            return p
    return None


COOKIE_DOMAINS = ("youtube.com", "google.com", "googlevideo.com", "ytimg.com")


def json_cookies_to_netscape(path: Path) -> str:
    """Convert a browser-extension JSON cookie export to Netscape format.
    Only cookies for YouTube/Google domains are kept; values are never printed."""
    data = json.loads(path.read_text())
    items = data if isinstance(data, list) else data.get("cookies", [])
    lines = ["# Netscape HTTP Cookie File"]
    kept = 0
    for c in items:
        dom = (c.get("domain") or "").strip()
        if not any(dom.lstrip(".").endswith(d) for d in COOKIE_DOMAINS):
            continue
        exp = c.get("expirationDate", c.get("expires", 0)) or 0
        if c.get("session"):
            exp = 0
        prefix = "#HttpOnly_" if c.get("httpOnly") else ""
        include_sub = "TRUE" if dom.startswith(".") or not c.get("hostOnly", False) else "FALSE"
        lines.append("\t".join([prefix + dom, include_sub, c.get("path") or "/",
                                 "TRUE" if c.get("secure") else "FALSE", str(int(float(exp))),
                                 c["name"], c.get("value", "")]))
        kept += 1
    if not kept:
        die(f"no YouTube/Google cookies found in {path.name}")
    print(f"Using {kept} cookies from {path.name} (YouTube/Google domains only).", file=sys.stderr)
    return "\n".join(lines) + "\n"


_TMP_COOKIES = []


def js_args() -> list:
    """YouTube now needs a JavaScript runtime (plus the yt-dlp-ejs package) to solve its player script.
    Enable the first one found; yt-dlp only enables deno by default."""
    for rt in ("deno", "bun", "node"):  # node < 20.19 is reported as unsupported by yt-dlp
        if shutil.which(rt):
            return ["--js-runtimes", rt]
    return []


def cookie_args(a) -> list:
    """Extra yt-dlp arguments for the opt-in cookie options (none by default)."""
    if a.cookies:
        src = Path(a.cookies).expanduser()
        if not src.is_file():
            die(f"cookies file not found: {src}")
        text = src.read_text()
        if text.lstrip().startswith(("[", "{")):
            text = json_cookies_to_netscape(src)
        # yt-dlp may rewrite its cookie file, so give it a private temp copy that is deleted afterwards
        fd, tmp = tempfile.mkstemp(prefix="inspire-cookies-", suffix=".txt")
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        _TMP_COOKIES.append(tmp)
        return ["--cookies", tmp]
    return ["--cookies-from-browser", a.cookies_from_browser] if a.cookies_from_browser else []


def cleanup_cookies() -> None:
    for t in _TMP_COOKIES:
        try:
            os.remove(t)
        except OSError:
            pass


def probe(url: str, a) -> dict:
    r = subprocess.run(["yt-dlp", *js_args(), *cookie_args(a), "--dump-single-json", "--no-playlist", "--no-download", url],
                       capture_output=True, text=True)
    if r.returncode != 0:
        hint = ""
        if "not a bot" in r.stderr or "Sign in" in r.stderr:
            hint = ("\nYouTube wants a signed-in session. Either download the video yourself and import it with "
                    "--file, or (at your own risk) re-run with --cookies <file> or --cookies-from-browser <browser>.")
        die("could not read video metadata (private, removed, login/geo-restricted, or unsupported)."
            f"{hint}\n{r.stderr.strip()[-300:]}")
    return json.loads(r.stdout)


def publish(tmp: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    tmp.rename(dest)  # publish only when complete


def import_file(a) -> int:
    f = Path(a.file).expanduser().resolve()
    if not f.is_file():
        die(f"file not found: {f}")
    h = hashlib.sha256()
    with f.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    key = f"local-{h.hexdigest()[:12]}"
    dest = CACHE / key
    got = cached_source(dest)
    if got and not a.force:
        print(f"Cached, skipping copy: {key}", file=sys.stderr)
        print(got)
        return 0
    print(f"File: {f.name} ({f.stat().st_size / 1e6:.1f} MB)", file=sys.stderr)
    confirm_rights(a)
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = CACHE / f".{key}.part"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    try:
        shutil.copy2(f, tmp / f"source{f.suffix.lower() or '.mp4'}")
        (tmp / "source_metadata.json").write_text(json.dumps({
            "id": key, "extractor_key": "Local", "title": a.title or f.stem, "original_filename": f.name,
            "webpage_url": a.source_url, "source_url": a.source_url, "rights_confirmed": True,
            "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }, ensure_ascii=False, indent=2))
        publish(tmp, dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(cached_source(dest))
    return 0


def download_url(a) -> int:
    if not shutil.which("yt-dlp"):
        die("yt-dlp not found. Install: pip install yt-dlp (or brew install yt-dlp)")
    if a.cookies:
        print("NOTE: using cookies you exported (opt-in). This may violate the platform's terms and can get the "
              "account flagged. Delete the cookie file when you are done.", file=sys.stderr)
    if a.cookies_from_browser:
        print(f"NOTE: using your '{a.cookies_from_browser}' browser session (opt-in). This may violate the "
              "platform's terms and can get the account flagged. Cookies are not stored by this script.",
              file=sys.stderr)
    info = probe(a.url, a)
    if info.get("is_live") or info.get("live_status") in ("is_live", "is_upcoming"):
        die("live/upcoming streams are not supported")
    if info.get("availability") not in (None, "public", "unlisted"):
        die(f"video availability is '{info.get('availability')}'; not downloading")

    key = f"{info['extractor_key'].lower()}-{info['id']}"
    dest = CACHE / key
    got = cached_source(dest)
    if got and not a.force:
        print(f"Cached, skipping download: {key}", file=sys.stderr)
        print(got)
        return 0

    print(f"Title:   {info.get('title')}\nChannel: {info.get('channel') or info.get('uploader')}\n"
          f"License: {info.get('license') or 'not stated (standard platform terms)'}\n"
          f"Length:  {info.get('duration')}s", file=sys.stderr)
    confirm_rights(a)

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
        r = subprocess.run(["yt-dlp", *js_args(), *cookie_args(a), "--no-playlist", "-f", FORMAT, "--merge-output-format", "mp4",
                            "-o", str(tmp / "source.%(ext)s"), a.url])
        if r.returncode != 0 or not (tmp / "source.mp4").exists():
            die("download failed; nothing cached")
        record = {k: info.get(k) for k in ("id", "extractor_key", "title", "channel", "uploader",
                  "upload_date", "license", "duration", "webpage_url", "description")}
        record.update(source_url=a.url, rights_confirmed=True,
                      downloaded_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        (tmp / "source_metadata.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
        publish(tmp, dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(lock, ignore_errors=True)
    print(cached_source(dest))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?", help="video URL (omit when using --file)")
    ap.add_argument("--file", help="import a video file you downloaded yourself")
    ap.add_argument("--source-url", help="with --file: where the file came from (kept for attribution)")
    ap.add_argument("--title", help="with --file: title to record")
    ap.add_argument("--cookies-from-browser", choices=BROWSERS, metavar="BROWSER",
                    help="opt-in: let yt-dlp use your signed-in browser session (%s)" % ", ".join(BROWSERS))
    ap.add_argument("--cookies", metavar="FILE",
                    help="opt-in: cookies exported from your browser (Netscape .txt or JSON list); never committed")
    ap.add_argument("--yes-rights", action="store_true",
                    help="confirm you own the video or are licensed/permitted to reuse it")
    ap.add_argument("--force", action="store_true", help="re-fetch even if cached")
    a = ap.parse_args()
    if bool(a.url) == bool(a.file):
        ap.error("give either a URL or --file")
    try:
        return import_file(a) if a.file else download_url(a)
    finally:
        cleanup_cookies()


if __name__ == "__main__":
    sys.exit(main())
