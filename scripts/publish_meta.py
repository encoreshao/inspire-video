#!/usr/bin/env python3
"""Validate and format publishing copy (title, description, hashtags) per platform.

Usage:
  python scripts/publish_meta.py <project-dir> --init [--platform id,id]   # scaffold publish.json from copy.json (draft)
  python scripts/publish_meta.py <project-dir>                             # validate publish.json, write publish.md,
                                                                           # publish_<platform>.txt files and project.json

publish.json (platform ids and their limits live in config/platforms.yaml):
{
  "platforms": {
    "wechat_channels": {"title": "...", "description": "...", "hashtags": ["拖延症", "..."]},
    "linkedin":        {"title": "...", "description": "...", "hashtags": ["Growth", "..."]}
  },
  "credit": "内容来源：...",          # appended to Chinese platforms' descriptions; required when a Chinese platform is listed
  "credit_en": "Source: ...",         # required when an English platform (lang: en) is listed
  "notes": ["optional reminders for the publisher"]
}
Hashtags are written without '#'. The old shape (top-level "wechat_channels" with "short_title" and "douyin") still loads.
"""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

import platforms

ROOT = Path(__file__).resolve().parent.parent
LEGACY_IDS = ("wechat_channels", "douyin")
LABELS = {"zh": ("标题", "描述", "字"), "en": ("Title", "Description", "chars")}


def tags_line(tags: list[str]) -> str:
    return " ".join(f"#{t}" for t in tags)


def body(desc: str, credit: str, tags: list[str]) -> str:
    return f"{desc}\n\n{credit}\n\n{tags_line(tags)}"


def credit_for(p: dict, pf: platforms.Platform) -> str:
    return (p.get("credit_en", "") if pf.lang == "en" else p.get("credit", "")).strip()


def normalize(p: dict) -> dict:
    """publish.json in the platform-keyed shape; the old top-level wechat_channels / douyin blocks are converted."""
    if "platforms" in p:
        return p
    out = {k: v for k, v in p.items() if k not in LEGACY_IDS}
    out["platforms"] = {}
    for pid in LEGACY_IDS:
        block = p.get(pid)
        if block:
            title = block.get("short_title" if pid == "wechat_channels" else "title", "")
            out["platforms"][pid] = {"title": title, "description": block.get("description", ""),
                                     "hashtags": block.get("hashtags", [])}
    return out


def bad_title_chars(title: str, allowed: str) -> list[str]:
    """Characters in `title` that are neither letters, digits, CJK nor one of the `allowed` marks."""
    return list(dict.fromkeys(c for c in title if not (c.isalnum() or c in allowed)))


def clean_title(title: str, allowed: str) -> str:
    """A title with every comma-like mark turned into a space and every other disallowed mark dropped."""
    out = "".join(" " if c in ",，、;；" else c for c in title)
    out = "".join(c for c in out if c.isalnum() or c in allowed)
    return " ".join(out.split())


def validate(p: dict, reg: platforms.Registry) -> list[str]:
    errs = []
    listed = p.get("platforms") or {}
    if any(pid in reg.platforms and reg.platforms[pid].lang == "zh" for pid in listed) and not p.get("credit", "").strip():
        errs.append("credit is required for Chinese platforms (source, speaker, and that subtitles are your own translation)")
    if not listed:
        errs.append(f"platforms is empty; list at least one of: {', '.join(reg.platforms)}")
        return errs
    english_credit_flagged = False
    for pid, blk in listed.items():
        try:
            pf = reg.platform(pid)
        except platforms.RegistryError as e:
            errs.append(str(e))
            continue
        if pf.lang == "en" and not p.get("credit_en", "").strip() and not english_credit_flagged:
            errs.append(f"{pid}: credit_en is required for English platforms (source, speaker, own-translation note)")
            english_credit_flagged = True
        title = blk.get("title", "")
        if not pf.title_min <= len(title) <= pf.title_max:
            errs.append(f"{pid}: {pf.title_field} is {len(title)} chars; allowed {pf.title_min}-{pf.title_max}")
        if pf.title_punct is not None and (bad := bad_title_chars(title, pf.title_punct)):
            errs.append(f"{pid}: {pf.title_field} has symbols the platform rejects: {' '.join(bad)} "
                        "(allowed: 《》 quotes : + ? % ℃; use a space for a comma)")
        desc, tags = blk.get("description", ""), blk.get("hashtags", [])
        if not desc:
            errs.append(f"{pid}: description is empty")
        full = body(desc, credit_for(p, pf), tags)
        if len(full) > pf.description_max:
            errs.append(f"{pid}: description + credit + hashtags is {len(full)} chars; max {pf.description_max}")
        if len(tags) > pf.hashtags_max:
            errs.append(f"{pid}: {len(tags)} hashtags; max {pf.hashtags_max}")
        for t in tags:
            if not t or any(c in t for c in " #\n"):
                errs.append(f"{pid}: hashtag '{t}' must be non-empty with no spaces or '#'")
    return errs


def write_project_json(out_dir: Path, m: dict, p: dict, reg: platforms.Registry) -> Path:
    """Machine-readable manifest of a finished project (schema 1), read by the LoopX Creator page."""
    slug = m["project_id"]
    prev = {}
    try:
        prev = json.loads((out_dir / "project.json").read_text())
    except (OSError, ValueError):
        pass
    cover = out_dir / "cover.png"
    publish, rendered = {}, []
    for pid, blk in p["platforms"].items():
        pf = reg.platform(pid)
        publish[pf.file_stem] = {"title": blk["title"], "caption": f"{blk['description']}\n\n{credit_for(p, pf)}",
                                 "hashtags": blk.get("hashtags", [])}
        profile = reg.resolve(pf.profile)[0].id
        if profile not in rendered:
            rendered.append(profile)
    manifest = {
        "schema": 1,
        "slug": slug,
        "title": (m.get("copy") or {}).get("headline_zh") or slug,
        "source_url": (m.get("provenance") or {}).get("source_reference") or None,
        "created_at": prev.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "video": f"{slug}.mp4",
        "cover": "cover.png" if cover.exists() else None,
        **({"cover_3x4": "cover-3x4.png"} if (out_dir / "cover-3x4.png").exists() else {}),
        "publish": publish,
    }
    if any(pid != platforms.DEFAULT_PROFILE for pid in rendered):   # additive keys, only when another format is in play
        manifest["videos"] = {pid: platforms.video_name(slug, pid) for pid in rendered
                              if (out_dir / platforms.video_name(slug, pid)).exists()}
        manifest["covers"] = {pid: platforms.cover_name(pid) for pid in rendered
                              if (out_dir / platforms.cover_name(pid)).exists()}
    out = out_dir / "project.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return out


def init(proj: Path, ids: list[str]) -> None:
    out = proj / "publish.json"
    if out.exists():
        sys.exit(f"{out} exists; edit it or delete it first")
    reg = platforms.load()
    for pid in ids:
        reg.platform(pid)               # fail on an unknown id before reading or writing anything
    cp = json.loads((proj / "copy.json").read_text())
    who = cp.get("speaker_name", "")
    credit = (f"内容来源：{cp.get('source_name', '')}"
              + (f"《{cp['talk_title']}》" if cp.get("talk_title") else "")
              + (f"，演讲者 {who}" if who else "") + (f"，{cp['year']}" if cp.get("year") else "")
              + "。中英字幕为自制翻译，版权归原作者所有。")
    parts = [f"Source: {cp.get('source_name', '')}"]
    if cp.get("talk_title"):
        parts.append(f"“{cp['talk_title']}”")
    if who:
        parts.append(f"speaker {who}")
    if cp.get("year"):
        parts.append(str(cp["year"]))
    credit_en = ", ".join(parts) + ". Chinese and English subtitles are my own translation; all rights belong to the original author."
    drafts = {}
    for pid in ids:
        pf = reg.platform(pid)
        if pf.lang == "en":
            drafts[pid] = {"title": (cp.get("subtitle_en") or "")[:pf.title_max], "description": cp.get("quote_en", ""), "hashtags": []}
        else:
            head = cp.get("headline_zh") or ""
            head = clean_title(head, pf.title_punct) if pf.title_punct is not None else head
            drafts[pid] = {"title": head[:pf.title_max], "description": cp.get("quote_zh", ""), "hashtags": []}
    data = {"platforms": drafts, "credit": credit}
    if any(reg.platform(pid).lang == "en" for pid in ids):
        data["credit_en"] = credit_en
    data["notes"] = ["DRAFT scaffold: rewrite the titles, descriptions and hashtags before publishing."]
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Wrote draft {out}")


def section(pf: platforms.Platform, blk: dict, full: str, slug: str, reg: platforms.Registry) -> str:
    title_label, desc_label, unit = LABELS[pf.lang]
    if pf.title_field == "short_title":
        title_label = "短标题"
    profile_id = reg.resolve(pf.profile)[0].id
    files = (f"Video: `output/final/{slug}/{platforms.video_name(slug, profile_id)}`  ·  "
             f"Cover: `output/final/{slug}/{platforms.cover_name(profile_id)}`")
    return (f"## {pf.name}\n\n{files}\n\n**{title_label}** ({len(blk['title'])} {unit})\n\n```\n{blk['title']}\n```\n\n"
            f"**{desc_label}** ({len(full)} {unit})\n\n```\n{full}\n```\n\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--platform", default=",".join(LEGACY_IDS), help="with --init: comma-separated platform ids to draft")
    a = ap.parse_args()
    proj = Path(a.project_dir).resolve()
    if a.init:
        try:
            init(proj, [x.strip() for x in a.platform.split(",") if x.strip()])
        except platforms.RegistryError as e:
            print(e, file=sys.stderr)
            return 1
        return 0
    reg = platforms.load()
    p = normalize(json.loads((proj / "publish.json").read_text()))
    errs = validate(p, reg)
    if errs:
        print("publish.json problems:\n- " + "\n- ".join(errs), file=sys.stderr)
        return 1

    m = json.loads((proj / "video_manifest.json").read_text())
    out_dir = ROOT / "output/final" / m["project_id"]  # one folder per project: video, cover, publishing copy
    out_dir.mkdir(parents=True, exist_ok=True)
    status = m["provenance"].get("review_status", "pending")
    warn = ""
    if status != "approved":
        warn = (f"> **NOT CLEARED FOR PUBLICATION** (review_status = `{status}`). "
                f"See `review.md` and `provenance.edit_notes` before posting.\n\n")
    sections, written, unverified = "", [], []
    for pid, blk in p["platforms"].items():
        pf = reg.platform(pid)
        full = body(blk["description"], credit_for(p, pf), blk.get("hashtags", []))
        name = f"publish_{pf.file_stem}.txt"
        (out_dir / name).write_text(f"{blk['title']}\n\n{full}\n")
        written.append(name)
        sections += section(pf, blk, full, m["project_id"], reg)
        if not pf.verified:
            unverified.append(pf.name)
    notes = "".join(f"- {n}\n" for n in p.get("notes", []))
    (out_dir / "publish.md").write_text(
        f"# Publishing copy: {m['project_id']}\n\n{warn}"
        f"{sections}"
        + (f"## Notes\n\n{notes}\n" if notes else "")
        + (f"Limits come from `config/platforms.yaml` and are unverified for: {', '.join(unverified)}. "
           f"Check each platform's publish page.\n" if unverified else ""))
    print(f"Wrote {out_dir/'publish.md'}, {', '.join(written)}")
    print(f"Wrote {write_project_json(out_dir, m, p, reg)}")
    if warn:
        print(f"WARNING: review_status is '{status}': not cleared for publication", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
