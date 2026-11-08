# Skills

Every agent skill of this repo lives in its own folder here. The shared engine (`scripts/`, `video/`, `config/`, `schemas/`) stays at the repo root, so several skills can reuse one renderer, one set of themes and one set of tools.

| Skill | Use it to | Look |
|---|---|---|
| `inspire-video` | Turn a podcast, interview or speech (URL or file) into a bilingual short video with the speaker's footage. | Editorial: a light paper layout with a headline block, a framed video, a caption card and a speaker card. |
| `inspire-showcase` | Turn a website, repository or screenshots into a bilingual showcase short video with local voice narration. | Two styles: `promo` (cinematic: a dark frame and a camera flying over the real page) for a live website, and `device` (editorial, like `inspire-video`) for repositories and screenshots. |

## Layout

```text
skills/<name>/SKILL.md          required: the workflow (frontmatter + imperative steps)
skills/<name>/references/*.md   optional: detail loaded only when a step needs it
skills/<name>/assets/           optional: files used in the output (templates, images), not loaded into context
scripts/                        shared, executable code (never copied into a skill)
schemas/                        machine-read schemas
```

## Conventions

- `name` in the frontmatter equals the folder name (lowercase letters, digits and hyphens).
- `description` is third person, starts with "This skill should be used when", says what the user asks for, and stays under 1024 characters. It is the only text loaded before the skill triggers, so it decides when the skill is used.
- Write the body as imperative steps ("Run", "Write", "Ask"), never second person. Keep it under 2,500 words (hard limit 5,000); put the full rules, field lists and long checklists in `references/`.
- Mention every reference file in `SKILL.md` and say when to read it. A file that is never mentioned is never loaded.
- Say that commands run from the repo root and use `scripts/...` paths, so one script serves every skill.
- Keep rights, honesty and safety rules in `SKILL.md` itself (a short list), with the details in a reference.

## Add a skill

1. Create `skills/<name>/SKILL.md` with the frontmatter above, and `references/` files for detail.
2. Put any new code in `scripts/` (with tests in `tests/`), not in the skill folder.
3. Run `python3 scripts/check_skills.py` and `python3 -m pytest tests -q`. The checks cover every folder under `skills/` automatically: frontmatter, third-person description, second person, size, links and unmentioned reference files.
4. Run `bash scripts/install.sh`. It links every folder under `skills/` into `~/.claude/skills` and `~/.agents/skills`, so the installer needs no change. `bash scripts/uninstall.sh` removes those links.

## Migration note

Earlier installs linked the repository root as the `inspire-video` skill. The root `SKILL.md` is now a short pointer so those installs keep working; running `bash scripts/install.sh` once replaces the old link with the per-skill links.
