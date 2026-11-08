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


def test_the_promo_capture_command_is_documented_and_its_dependency_is_optional():
    assert "scripts/showcase/capture_page.py" in SKILL and "Playwright" in SKILL
    assert (ROOT / "scripts" / "showcase" / "capture_page.py").exists()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'promo = ["playwright' in pyproject
    import ast
    for module in ("capture_page", "page_layout"):
        tree = ast.parse((ROOT / "scripts" / "showcase" / f"{module}.py").read_text(encoding="utf-8"))
        top_level = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        assert not any("playwright" in ast.dump(n) for n in top_level), f"{module} imports playwright at load"


def _description(skill: str) -> str:
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return re.search(r"^description: (.+)$", text, re.M).group(1)


def test_each_skill_description_says_what_the_other_skill_is_for():
    video, showcase = _description("inspire-video"), _description("inspire-showcase")
    assert "inspire-showcase" in video and "inspire-video" in showcase          # a "not for" clause pointing at the other skill
    assert "product" in video.lower() and ("talk" in showcase.lower() or "interview" in showcase.lower())
    assert len(video) < 1024 and len(showcase) < 1024
    assert video.startswith("This skill should be used when") and showcase.startswith("This skill should be used when")


def test_the_showcase_skill_says_how_to_choose_between_its_two_styles():
    assert "## Choose the style" in SKILL
    section = SKILL.split("## Choose the style")[1].split("\n## ")[0]
    assert "promo" in section and "device" in section and "website" in section
    assert "editorial" in SKILL                                                  # the device style shares the speaker layout, and says so
