#!/usr/bin/env python3
"""Validate and format publishing copy (title, description, tags) for WeChat Channels and Douyin.

Usage:
  python scripts/publish_meta.py <project-dir> --init    # scaffold publish.json from copy.json (draft)
  python scripts/publish_meta.py <project-dir>           # validate publish.json, write publish.md + .txt files

publish.json:
{
  "wechat_channels": {"short_title": "...", "description": "...", "hashtags": ["拖延症", "..."]},
  "douyin":          {"title": "...",       "description": "...", "hashtags": ["拖延症", "..."]},
  "credit": "内容来源：...",
  "notes": ["optional reminders for the publisher"]
}
Hashtags are written without '#'. The credit line is appended to every description.
"""
import argparse, json, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def limits() -> dict:
    return yaml.safe_load((ROOT / "config/publish.yaml").read_text())


def tags_line(tags: list[str]) -> str:
    return " ".join(f"#{t}" for t in tags)


def body(desc: str, credit: str, tags: list[str]) -> str:
    return f"{desc}\n\n{credit}\n\n{tags_line(tags)}"


def validate(p: dict, lim: dict) -> list[str]:
    errs = []
    w, d = p.get("wechat_channels", {}), p.get("douyin", {})
    credit = p.get("credit", "").strip()
    if not credit:
        errs.append("credit is required (source, speaker, and that subtitles are your own translation)")
    lw, ld = lim["wechat_channels"], lim["douyin"]
    st = w.get("short_title", "")
    if not lw["short_title_min"] <= len(st) <= lw["short_title_max"]:
        errs.append(f"wechat short_title is {len(st)} chars; allowed {lw['short_title_min']}-{lw['short_title_max']}")
    if len(d.get("title", "")) > ld["title_max"] or not d.get("title"):
        errs.append(f"douyin title is {len(d.get('title', ''))} chars; allowed 1-{ld['title_max']}")
    for name, blk, lm, dk in (("wechat", w, lw, "description"), ("douyin", d, ld, "description")):
        tags = blk.get("hashtags", [])
        full = body(blk.get(dk, ""), credit, tags)
        if not blk.get(dk):
            errs.append(f"{name} description is empty")
        if len(full) > lm["description_max"]:
            errs.append(f"{name} description + credit + hashtags is {len(full)} chars; max {lm['description_max']}")
        if len(tags) > lm["hashtags_max"]:
            errs.append(f"{name} has {len(tags)} hashtags; max {lm['hashtags_max']}")
        for t in tags:
            if not t or any(c in t for c in " #\n"):
                errs.append(f"{name} hashtag '{t}' must be non-empty with no spaces or '#'")
    return errs


def init(proj: Path) -> None:
    out = proj / "publish.json"
    if out.exists():
        sys.exit(f"{out} exists; edit it or delete it first")
    cp = json.loads((proj / "copy.json").read_text())
    who = cp.get("speaker_name", "")
    credit = (f"内容来源：{cp.get('source_name', '')}"
              + (f"《{cp['talk_title']}》" if cp.get("talk_title") else "")
              + (f"，演讲者 {who}" if who else "") + (f"，{cp['year']}" if cp.get("year") else "")
              + "。中英字幕为自制翻译，版权归原作者所有。")
    head = cp.get("headline_zh", "")
    out.write_text(json.dumps({
        "wechat_channels": {"short_title": head[:16], "description": cp.get("quote_zh", ""), "hashtags": []},
        "douyin": {"title": head[:30], "description": cp.get("quote_zh", ""), "hashtags": []},
        "credit": credit,
        "notes": ["DRAFT scaffold: rewrite the titles, descriptions and hashtags before publishing."],
    }, ensure_ascii=False, indent=2))
    print(f"Wrote draft {out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--init", action="store_true")
    a = ap.parse_args()
    proj = Path(a.project_dir).resolve()
    if a.init:
        init(proj)
        return 0
    p = json.loads((proj / "publish.json").read_text())
    errs = validate(p, limits())
    if errs:
        print("publish.json problems:\n- " + "\n- ".join(errs), file=sys.stderr)
        return 1

    m = json.loads((proj / "video_manifest.json").read_text())
    status = m["provenance"].get("review_status", "pending")
    warn = ""
    if status != "approved":
        warn = (f"> **NOT CLEARED FOR PUBLICATION** (review_status = `{status}`). "
                f"See `review.md` and `provenance.edit_notes` before posting.\n\n")
    credit, w, d = p["credit"].strip(), p["wechat_channels"], p["douyin"]
    wx = body(w["description"], credit, w["hashtags"])
    dy = body(d["description"], credit, d["hashtags"])
    (proj / "publish_wechat.txt").write_text(f"{w['short_title']}\n\n{wx}\n")
    (proj / "publish_douyin.txt").write_text(f"{d['title']}\n\n{dy}\n")
    notes = "".join(f"- {n}\n" for n in p.get("notes", []))
    (proj / "publish.md").write_text(
        f"# Publishing copy: {m['project_id']}\n\n{warn}"
        f"Video: `output/final/{m['project_id']}.mp4`  ·  Cover: `output/final/{m['project_id']}-cover.png`\n\n"
        f"## 微信视频号 (WeChat Channels)\n\n**短标题** ({len(w['short_title'])} 字)\n\n```\n{w['short_title']}\n```\n\n"
        f"**描述** ({len(wx)} 字)\n\n```\n{wx}\n```\n\n"
        f"## 抖音 (Douyin)\n\n**标题** ({len(d['title'])} 字)\n\n```\n{d['title']}\n```\n\n"
        f"**作品描述** ({len(dy)} 字)\n\n```\n{dy}\n```\n\n"
        + (f"## Notes\n\n{notes}\n" if notes else "")
        + "Limits come from `config/publish.yaml` and are unverified; check them in each platform's publish page.\n")
    print(f"Wrote {proj/'publish.md'}, publish_wechat.txt, publish_douyin.txt")
    if warn:
        print(f"WARNING: review_status is '{status}': not cleared for publication", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
