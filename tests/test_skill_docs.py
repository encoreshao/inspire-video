import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "skills" / "inspire-showcase" / "SKILL.md").read_text(encoding="utf-8")


def test_frontmatter_names_the_skill_and_says_when_to_use_it():
    m = re.match(r"^---\nname: inspire-showcase\ndescription: (.+)\n---\n", SKILL)
    assert m and "website" in m.group(1) and "repository" in m.group(1) and "screenshots" in m.group(1)


def test_every_command_in_the_skill_exists():
    commands = set(re.findall(r"python3? scripts/((?:showcase/)?[a-z_]+\.py)", SKILL))
    assert {"showcase/ingest.py", "showcase/manifest.py", "showcase/narrate.py", "showcase/voices.py",
            "render.py", "showcase/checks.py"} <= commands
    for c in commands:
        assert (ROOT / "scripts" / c).exists(), c


def test_the_rules_that_keep_videos_honest_are_stated():
    for needle in ("rights", "never invent", "one sentence", "100", "4 to 6", "focus", "--allow-unresolved-rights",
                   "separate from", "inspire-video"):
        assert needle.lower() in SKILL.lower(), needle


def test_installer_links_the_showcase_skill():
    assert "inspire-showcase" in (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
