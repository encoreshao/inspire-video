import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
READMES = [ROOT / "README.md", ROOT / "README.zh-CN.md"]
PATH = re.compile(r"`((?:scripts|skills|schemas|config|video/src|tests|docs)/[\w./<>-]+\.(?:py|sh|md|json|yaml|mjs|tsx|ts))`")
FENCE = re.compile(r"```.*?```", re.S)


def headings(path):
    text = FENCE.sub("", path.read_text(encoding="utf-8"))
    return [l for l in text.splitlines() if l.startswith("#")]


@pytest.mark.parametrize("readme", READMES, ids=lambda p: p.name)
def test_every_repo_path_the_readme_mentions_exists(readme):
    missing = [t for t in PATH.findall(readme.read_text(encoding="utf-8")) if "<" not in t and not (ROOT / t).exists()]
    assert missing == []


def test_both_languages_have_the_same_structure():
    en, zh = (headings(p) for p in READMES)
    assert len(en) == len(zh) and [h.count("#") for h in en] == [h.count("#") for h in zh]


@pytest.mark.parametrize("readme", READMES, ids=lambda p: p.name)
def test_every_skill_is_documented(readme):
    text = readme.read_text(encoding="utf-8")
    for d in sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir()):
        assert f"`{d.name}`" in text, f"{readme.name} does not mention the {d.name} skill"
    assert "scripts/check_skills.py" in text and "skills/README.md" in text


@pytest.mark.parametrize("readme", READMES, ids=lambda p: p.name)
def test_the_old_reference_paths_are_gone(readme):
    text = readme.read_text(encoding="utf-8")
    assert "`references/" not in text.replace("`skills/inspire-video/references/", "").replace("`skills/inspire-showcase/references/", "")
