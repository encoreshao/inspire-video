import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "inspire-showcase"
SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
ALL = SKILL + "".join(f.read_text(encoding="utf-8") for f in sorted((SKILL_DIR / "references").glob("*.md")))


def test_the_description_names_what_the_skill_is_for():
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
        assert needle.lower() in ALL.lower(), needle


def test_the_input_limits_in_the_reference_match_the_validator():
    from showcase import manifest as M
    ref = (SKILL_DIR / "references" / "beat-writing.md").read_text(encoding="utf-8")
    assert f"at most {M.CALLOUT_UNITS} width units" in ref and f"at most {M.MAX_ZH} characters" in ref


def test_the_review_references_are_loaded_credited_and_licensed():
    for name in ("aesthetic-rules.md", "final-review.md"):
        assert f"references/{name}" in SKILL
        head = (SKILL_DIR / "references" / name).read_text(encoding="utf-8")[:600]
        assert "video-shotcraft" in head and "Apache License 2.0" in head
    assert "video-shotcraft" in (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "Apache License" in (ROOT / "LICENSES" / "Apache-2.0.txt").read_text(encoding="utf-8")
    assert "checks.py <video> --sheet" in SKILL
