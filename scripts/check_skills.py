#!/usr/bin/env python3
"""Check that every skill under skills/ follows the repo's skill conventions (see skills/README.md).

  python scripts/check_skills.py [repo-root]

Checks per skill: SKILL.md frontmatter (name equals the folder name, a third-person description that starts with
"This skill should be used when"), no second person in the body, a body under 5000 words, every `references/...`
mention resolves inside the skill, every `scripts/...` or `schemas/...` mention resolves in the repo, and no reference
file is left unmentioned. Also checks the optional root SKILL.md pointer.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
DESC_START = "This skill should be used when"
MAX_DESC = 1024
MAX_WORDS = 5000
MAX_POINTER_WORDS = 150
SECOND_PERSON = re.compile(r"\b(you|your|yours|yourself)\b", re.I)
REF_TOKEN = re.compile(r"(?<![\w/.-])(references/[\w./-]+\.\w+)")
REPO_TOKEN = re.compile(r"(?<![\w/.-])((?:scripts|schemas)/[\w./-]+\.(?:py|sh|json))")
POINTER_TOKEN = re.compile(r"skills/([\w-]+)/SKILL\.md")
CODE_SPAN = re.compile(r"`[^`\n]*`|\"[^\"\n]*\"")      # code and quoted text (a quotation is not an instruction)


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    meta = {}
    for line in text[4:end].splitlines():
        if ":" in line and line.strip():
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, text[end + 5:]


def check_skill(skill_dir, repo_root) -> list[str]:
    skill_dir, repo_root = Path(skill_dir), Path(repo_root)
    label = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{label}: missing SKILL.md"]
    text = skill_md.read_text(encoding="utf-8")
    try:
        meta, body = split_frontmatter(text)
    except ValueError as e:
        return [f"{label}: SKILL.md has no valid frontmatter ({e}); it must start with --- name and description ---"]
    problems: list[str] = []
    name, desc = meta.get("name", ""), meta.get("description", "")
    if not NAME_RE.fullmatch(name):
        problems.append(f"{label}: name {name!r} must be lowercase letters, digits and hyphens (at most 64 characters)")
    elif name != skill_dir.name:
        problems.append(f"{label}: name {name!r} must equal the folder name {skill_dir.name!r}")
    if not desc.startswith(DESC_START):
        problems.append(f"{label}: the description must be third person and start with \"{DESC_START}\" (it decides when the skill triggers)")
    if len(desc) > MAX_DESC:
        problems.append(f"{label}: the description is {len(desc)} characters; the limit is {MAX_DESC}")
    if "<" in desc or ">" in desc:
        problems.append(f"{label}: the description must not contain angle brackets")
    words = len(body.split())
    if words > MAX_WORDS:
        problems.append(f"{label}: the body is {words} words; the limit is {MAX_WORDS}: move detail into references/")
    for n, line in enumerate(body.splitlines(), 1):
        if SECOND_PERSON.search(CODE_SPAN.sub("", line)):
            problems.append(f"{label}: SKILL.md line {n} uses second person; write imperative instructions")
            break

    docs = [skill_md, *sorted((skill_dir / "references").glob("*.md"))]
    for doc in docs:
        content = doc.read_text(encoding="utf-8")
        for token in sorted(set(REF_TOKEN.findall(content))):
            if not (skill_dir / token).is_file():
                problems.append(f"{label}: {doc.name} mentions {token}, which does not exist in the skill")
        for token in sorted(set(REPO_TOKEN.findall(content))):
            if not (repo_root / token).is_file():
                problems.append(f"{label}: {doc.name} mentions {token}, which does not exist in the repo")
    for ref in sorted((skill_dir / "references").glob("*")):
        if ref.is_file() and f"references/{ref.name}" not in body:
            problems.append(f"{label}: references/{ref.name} is not mentioned in SKILL.md, so it will never be loaded")
    return problems


def check_all(repo_root) -> list[str]:
    repo_root = Path(repo_root)
    skills = repo_root / "skills"
    if not skills.is_dir():
        return ["there is no skills/ folder"]
    problems: list[str] = []
    for d in sorted(p for p in skills.iterdir() if p.is_dir()):
        problems += check_skill(d, repo_root)
    pointer = repo_root / "SKILL.md"
    if pointer.exists():
        text = pointer.read_text(encoding="utf-8")
        named = POINTER_TOKEN.findall(text)
        if len(text.split()) > MAX_POINTER_WORDS:
            problems.append(f"root SKILL.md is a pointer and must stay under {MAX_POINTER_WORDS} words")
        if not named or not all((skills / n / "SKILL.md").is_file() for n in named):
            problems.append("root SKILL.md pointer must name an existing skills/<name>/SKILL.md")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check the skills in a repository against the skill conventions")
    ap.add_argument("repo", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    a = ap.parse_args(argv)
    problems = check_all(a.repo)
    for p in problems:
        print(f"PROBLEM: {p}")
    if not problems:
        count = len([d for d in (Path(a.repo) / "skills").iterdir() if d.is_dir()])
        print(f"all skills passed ({count})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
