"""Read a repository folder (local, or a shallow clone of a GitHub/GitLab repo) into plain facts."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from showcase.assets import IMAGE_EXTS
from showcase.sources import Source

SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", "venv", ".venv", "__pycache__", ".next",
             ".idea", ".cache", "vendor"}
README_NAMES = ("README.md", "readme.md", "README.MD", "README.rst", "README.txt", "README")
LANG_BY_EXT = {".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
               ".rb": "Ruby", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".swift": "Swift",
               ".php": "PHP", ".c": "C", ".cpp": "C++", ".cs": "C#", ".sh": "Shell", ".html": "HTML",
               ".css": "CSS", ".vue": "Vue", ".dart": "Dart"}
LICENSES = (("mit license", "MIT"), ("apache license", "Apache-2.0"), ("gnu general public", "GPL"),
            ("gnu lesser general", "LGPL"), ("mozilla public", "MPL-2.0"), ("bsd", "BSD"), ("unlicense", "Unlicense"))
SHOT_WORDS = re.compile(r"(screenshot|screen[-_ ]?shot|demo|preview|hero|banner|mockup)", re.I)
SHOT_DIRS = {"screenshots", "screenshot", "images", "img", "assets", "docs", "media", "public"}
MAX_README, MAX_TREE, MAX_DOCS, MAX_IMAGES, MAX_FILES = 8000, 200, 30, 20, 5000
README_IMG = re.compile(r"""!\[[^\]]*\]\(\s*<?([^)\s>]+)|<img[^>]+src=["']([^"']+)["']""", re.I)


class RepoError(ValueError):
    pass


def _inside(root: Path, p: Path) -> bool:
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def _walk(root: Path) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if p.is_symlink() or not _inside(root, p):
                continue
            out.append(p.relative_to(root).as_posix())
            if len(out) >= MAX_FILES:
                return out
    return out


def _read_text(root: Path, rel: str, limit: int) -> str | None:
    p = root / rel
    if not p.is_file() or not _inside(root, p):
        return None
    return p.read_text(encoding="utf-8", errors="replace")[:limit]


def _readme(root: Path):
    for name in README_NAMES:
        text = _read_text(root, name, MAX_README)
        if text is not None:
            return {"path": name, "text": text}
    return None


def _readme_images(text: str, root: Path) -> list[str]:
    found = []
    for m in README_IMG.finditer(text):
        ref = (m.group(1) or m.group(2) or "").split("?")[0].split("#")[0]
        if not ref or re.match(r"^[a-z][a-z0-9+.-]*:", ref, re.I) or ref.startswith("//"):
            continue
        p = root / ref
        if p.suffix.lower() in IMAGE_EXTS and p.is_file() and _inside(root, p) and not p.is_symlink():
            rel = p.resolve().relative_to(root.resolve()).as_posix()
            if rel not in found:
                found.append(rel)
    return found


def _manifests(root: Path) -> dict:
    out = {}
    text = _read_text(root, "package.json", 200_000)
    if text:
        try:
            d = json.loads(text)
            out["package.json"] = {"name": d.get("name", ""), "description": d.get("description", ""),
                                   "version": d.get("version", ""), "scripts": sorted(d.get("scripts", {}))[:15],
                                   "dependencies": sorted(d.get("dependencies", {}))[:15]}
        except (ValueError, AttributeError):
            pass
    text = _read_text(root, "pyproject.toml", 200_000)
    if text:
        try:
            proj = tomllib.loads(text).get("project", {})
            out["pyproject.toml"] = {"name": proj.get("name", ""), "description": proj.get("description", ""),
                                     "version": proj.get("version", "")}
        except tomllib.TOMLDecodeError:
            pass
    text = _read_text(root, "Cargo.toml", 200_000)
    if text:
        try:
            pkg = tomllib.loads(text).get("package", {})
            out["Cargo.toml"] = {"name": pkg.get("name", ""), "description": pkg.get("description", ""),
                                 "version": pkg.get("version", "")}
        except tomllib.TOMLDecodeError:
            pass
    text = _read_text(root, "go.mod", 20_000)
    if text and (m := re.search(r"^module\s+(\S+)", text, re.M)):
        out["go.mod"] = {"name": m.group(1)}
    return out


def _license(root: Path, files: list[str]) -> str:
    for rel in files:
        if re.match(r"^(licen[sc]e|copying)(\.\w+)?$", rel, re.I):
            text = (_read_text(root, rel, 2000) or "").lower()
            for needle, name in LICENSES:
                if needle in text:
                    return name
            return "other"
    return "unknown"


def _languages(files: list[str]) -> list[dict]:
    counts = Counter(LANG_BY_EXT[Path(f).suffix.lower()] for f in files if Path(f).suffix.lower() in LANG_BY_EXT)
    return [{"language": k, "files": v} for k, v in counts.most_common(5)]


def _image_candidates(root: Path, files: list[str], readme_text: str) -> list[str]:
    picked = _readme_images(readme_text, root)
    for rel in files:
        parts = Path(rel).parts
        if Path(rel).suffix.lower() not in IMAGE_EXTS or rel in picked:
            continue
        if SHOT_WORDS.search(Path(rel).name) or (len(parts) > 1 and parts[0].lower() in SHOT_DIRS):
            picked.append(rel)
    return picked[:MAX_IMAGES]


def read_repo(root) -> dict:
    root = Path(root)
    files = _walk(root)
    readme = _readme(root)
    return {"name": root.resolve().name, "readme": readme, "tree": files[:MAX_TREE], "manifests": _manifests(root),
            "docs": [f for f in files if f.startswith("docs/") and f.endswith((".md", ".rst"))][:MAX_DOCS],
            "license": _license(root, files), "languages": _languages(files),
            "image_candidates": _image_candidates(root, files, readme["text"] if readme else "")}


def clone_repo(source: Source, cache_dir, run=subprocess.run) -> Path:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9._-]", "_", f"{source.host}-{source.repo_path.replace('/', '__')}")
    dest = cache_dir / slug
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        if (dest / ".git").exists():
            try:
                run(["git", "-C", str(dest), "pull", "--ff-only", "--depth", "1"], check=True,
                    capture_output=True, text=True, timeout=120, env=env)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass                                     # keep using the existing clone
        else:
            run(["git", "clone", "--depth", "1", "--", source.url, str(dest)], check=True,
                capture_output=True, text=True, timeout=300, env=env)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        detail = (getattr(e, "stderr", "") or str(e)).strip().splitlines()[-1:] or [""]
        raise RepoError(f"could not clone {source.url}: {detail[0]}; for a private repository check your git "
                        "credentials (gh auth status / glab auth status)") from None
    return dest


def fetch_metadata(source: Source, run=subprocess.run):
    try:
        if source.kind == "github":
            fields = "description,stargazerCount,repositoryTopics,licenseInfo,latestRelease,homepageUrl,primaryLanguage"
            r = run(["gh", "repo", "view", source.repo_path, "--json", fields], check=True,
                    capture_output=True, text=True, timeout=30)
            d = json.loads(r.stdout)
            topics = [t.get("name") or (t.get("topic") or {}).get("name") for t in d.get("repositoryTopics") or []]
            lic = d.get("licenseInfo") or {}
            return {"description": d.get("description") or "", "stars": d.get("stargazerCount"),
                    "topics": [t for t in topics if t], "license": lic.get("spdxId") or lic.get("name") or "",
                    "latest_release": (d.get("latestRelease") or {}).get("tagName", ""),
                    "homepage": d.get("homepageUrl") or "",
                    "primary_language": (d.get("primaryLanguage") or {}).get("name", "")}, None
        if source.kind == "gitlab":
            r = run(["glab", "api", "--hostname", source.host, f"projects/{quote(source.repo_path, safe='')}"],
                    check=True, capture_output=True, text=True, timeout=30)
            d = json.loads(r.stdout)
            return {"description": d.get("description") or "", "stars": d.get("star_count"),
                    "topics": d.get("topics") or d.get("tag_list") or [], "homepage": d.get("web_url") or ""}, None
        return {}, None
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as e:
        why = (getattr(e, "stderr", "") or str(e)).strip().splitlines()[-1:] or [type(e).__name__]
        return {}, f"repository metadata unavailable ({why[0]}); stars, topics and releases are missing"
