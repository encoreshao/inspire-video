#!/usr/bin/env python3
"""Turn a website, a GitHub/GitLab repository or a local folder (plus optional screenshots) into brief.json.

  python scripts/showcase/ingest.py SOURCE [--project DIR] [--screenshots DIR] [--capture | --no-capture]
                                    [--gitlab-host HOST ...] [--allow-private]

The brief holds deterministic facts with their sources, the page and README text for the beat writer, the
ranked assets (copied into <project>/assets/) with rights notes, and what is unknown.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from showcase import assets as A  # noqa: E402
from showcase import capture as C  # noqa: E402
from showcase import repo_reader as R  # noqa: E402
from showcase import webcrawl as W  # noqa: E402
from showcase.sources import classify_source  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MAX_SELECTED = 12
BRIEF_KEYS = ("version", "source", "created", "facts", "texts", "assets", "candidates", "rejected_assets",
              "skipped", "unknowns", "rights_unresolved", "hints")
ASSET_KEYS = ("path", "origin", "source", "width", "height", "sha256", "rights", "rights_resolved")


class IngestError(ValueError):
    pass


@dataclass
class Deps:
    fetch: object = None                       # webcrawl fetcher; None means the real network
    host_check: object = W.is_public_host
    run: object = subprocess.run
    chrome: object = None                      # Chrome path override


class _Facts:
    def __init__(self):
        self.items = []

    def add(self, claim, source):
        claim = (claim or "").strip()
        if claim:
            self.items.append({"id": f"f{len(self.items) + 1}", "claim": claim, "source": source})


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "project"


def validate_brief(brief: dict) -> None:
    missing = [k for k in BRIEF_KEYS if k not in brief]
    if missing:
        raise IngestError(f"brief is missing {', '.join(missing)}")
    if brief["version"] != 1:
        raise IngestError(f"unsupported brief version {brief['version']!r}")
    for f in brief["facts"]:
        if not all(isinstance(f.get(k), str) and f.get(k) for k in ("id", "claim", "source")):
            raise IngestError(f"invalid fact {f!r}: id, claim and source are required")
    for a in brief["assets"] + brief["candidates"]:
        if any(k not in a for k in ASSET_KEYS):
            raise IngestError(f"invalid asset {a.get('path')!r}: needs {', '.join(ASSET_KEYS)}")


def _website(src, deps, allow_private, facts, texts, skipped, unknowns, have_user_shots):
    result = W.crawl(src.url, fetch=deps.fetch, host_check=deps.host_check, allow_private=allow_private)
    skipped.extend(result.skipped)
    if not result.pages:
        why = "; ".join(f"{s['url']}: {s['reason']}" for s in result.skipped) or "no page could be read"
        if not have_user_shots:
            raise IngestError(f"could not read any page of {src.url} ({why}); provide your own images with "
                              "--screenshots and run again")
        unknowns.append(f"website text unavailable ({why})")
        return []
    home = result.pages[0]
    facts.add(f"The site is titled \"{home.title}\"" if home.title else "", home.url)
    facts.add(f"The site describes itself as: {home.description}" if home.description else "", home.url)
    labels = [l["text"] for l in home.nav_links if l["text"]]
    facts.add(f"The navigation lists: {', '.join(dict.fromkeys(labels))}" if labels else "", home.url)
    for page in result.pages:
        if page.headings:
            facts.add(f"Page \"{page.title or page.url}\" has the headings: {'; '.join(page.headings[:4])}", page.url)
        texts.append({"source": page.url, "kind": "page", "text": page.text})
    return result.pages


def _repo(src, deps, cache_dir, facts, texts, unknowns):
    root = Path(src.url) if src.kind == "local" else R.clone_repo(
        src, cache_dir or ROOT / "output" / "cache" / "repos", run=deps.run)
    info = R.read_repo(root)
    meta, note = ({}, None) if src.kind == "local" else R.fetch_metadata(src, run=deps.run)
    if note:
        unknowns.append(note)
    where = src.url if src.kind != "local" else "local repository"
    manifest = next(iter(info["manifests"].values()), {})
    name = src.repo_path or manifest.get("name") or info["name"]
    description = meta.get("description") or manifest.get("description")
    facts.add(f"The project is called {name}", where)
    facts.add(f"Description: {description}" if description else "", where)
    if meta.get("stars") is not None:
        facts.add(f"It has {meta['stars']} stars", where)
    if meta.get("topics"):
        facts.add(f"Topics: {', '.join(meta['topics'])}", where)
    license_name = meta.get("license") or info["license"]
    if license_name and license_name != "unknown":
        facts.add(f"License: {license_name}", where)
    if meta.get("latest_release"):
        facts.add(f"Latest release: {meta['latest_release']}", where)
    if meta.get("homepage"):
        facts.add(f"Homepage: {meta['homepage']}", where)
    if info["languages"]:
        facts.add("Main languages: " + ", ".join(f"{l['language']} ({l['files']} files)" for l in info["languages"][:3]), where)
    if info["readme"]:
        texts.append({"source": info["readme"]["path"], "kind": "readme", "text": info["readme"]["text"]})
    return root, info, license_name


def ingest(source_arg, project, screenshots=None, capture=None, gitlab_hosts=(), allow_private=False,
           deps=None, cache_dir=None) -> dict:
    deps = deps or Deps()
    src = classify_source(source_arg, gitlab_hosts)
    project = Path(project)
    assets_dir = project / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    facts, texts, skipped, unknowns, rejected = _Facts(), [], [], [], []

    user_assets = []
    if screenshots:
        user_assets, bad = A.collect_user_shots(screenshots)
        rejected.extend(bad)

    found = []                                                   # capture or repo assets
    if src.kind == "website":
        pages = _website(src, deps, allow_private, facts, texts, skipped, unknowns, bool(user_assets))
        if pages and (capture if capture is not None else not user_assets):
            urls = [p.url for p in pages[:4]]
            caps, fails = C.capture_pages(urls[:1], assets_dir, chrome=deps.chrome, run=deps.run, prefix="capture-a")
            more, fails2 = C.capture_pages(urls[1:], assets_dir, chrome=deps.chrome, run=deps.run,
                                           sizes=C.SIZES[:1], prefix="capture-b")
            skipped.extend(fails + fails2)
            for c in caps + more:
                asset, why = A.try_describe(c["path"], "capture", c["url"], A.rights_note("capture", c["url"]))
                if asset:
                    found.append(asset)
                else:
                    rejected.append({"path": c["path"], "reason": why})
    else:
        root, info, license_name = _repo(src, deps, cache_dir, facts, texts, unknowns)
        where = src.url if src.kind != "local" else "local repository"
        for rel in info["image_candidates"]:
            asset, why = A.try_describe(root / rel, "repo", f"{where}:{rel}", A.rights_note("repo", where, license_name))
            if asset:
                found.append(asset)
            else:
                rejected.append({"path": rel, "reason": why})

    found, dupes = A.dedupe(found)
    rejected.extend(dupes)
    if user_assets:
        selected, candidates = user_assets, found
    else:
        selected, candidates = A.rank_assets(found)[:MAX_SELECTED], []
    if not selected:
        if src.kind == "website":
            raise IngestError(f"no usable images for {src.url}: page capture produced none; provide your own "
                              "images with --screenshots and run again")
        unknowns.append("no product screenshots found in the repository or provided; the terminal style "
                        "fits better than the device walkthrough")

    final = []
    for i, a in enumerate(selected, 1):
        src_path = Path(a["path"])
        if src_path.parent.resolve() == assets_dir.resolve():
            dest = src_path
        else:
            dest = assets_dir / f"{i:02d}-{a['origin']}-{re.sub(r'[^A-Za-z0-9._-]', '_', src_path.name)}"
            shutil.copyfile(src_path, dest)
        final.append({**a, "path": dest.relative_to(project).as_posix()})
    keep = {a["path"] for a in final}
    for stray in assets_dir.iterdir():                           # capture files that were not selected
        if stray.is_file() and stray.relative_to(project).as_posix() not in keep:
            stray.unlink()

    brief = {"version": 1,
             "source": {"kind": src.kind, "url": src.url, "host": src.host, "repo_path": src.repo_path},
             "created": date.today().isoformat(), "facts": facts.items, "texts": texts, "assets": final,
             "candidates": candidates, "rejected_assets": rejected, "skipped": skipped, "unknowns": unknowns,
             "rights_unresolved": any(not a["rights_resolved"] for a in final),
             "hints": {"suggested_style": "device" if final else "terminal"}}
    validate_brief(brief)
    (project / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")
    return brief


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build a showcase brief from a website, repository or local folder")
    ap.add_argument("source", help="website URL, GitHub/GitLab repository URL, or a local repository folder")
    ap.add_argument("--project", help="project folder (default: output/projects/<slug>)")
    ap.add_argument("--screenshots", help="folder of your own screenshots (ordered by filename)")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--capture", dest="capture", action="store_true", default=None, help="always capture the site's pages")
    grp.add_argument("--no-capture", dest="capture", action="store_false", help="never capture the site's pages")
    ap.add_argument("--gitlab-host", action="append", default=[], help="a self-hosted GitLab host (repeatable)")
    ap.add_argument("--allow-private", action="store_true", help="allow crawling localhost and private addresses")
    a = ap.parse_args(argv)
    try:
        src = classify_source(a.source, a.gitlab_host)
        project = Path(a.project) if a.project else ROOT / "output" / "projects" / _slug(
            src.repo_path.split("/")[-1] or src.host or Path(src.url).name)
        brief = ingest(a.source, project, a.screenshots, a.capture, a.gitlab_host, a.allow_private, deps=Deps())
    except (ValueError, RuntimeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    unresolved = sum(1 for x in brief["assets"] if not x["rights_resolved"])
    print(f"brief written: {len(brief['facts'])} facts, {len(brief['assets'])} assets ({unresolved} with unresolved "
          f"rights), suggested style {brief['hints']['suggested_style']} -> {project / 'brief.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
