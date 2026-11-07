import re
from pathlib import Path

import platforms

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "inspire-video"
DOCS = {p.name: p.read_text(encoding="utf-8") for p in [SKILL_DIR / "SKILL.md", *sorted((SKILL_DIR / "references").glob("*.md"))]}
ALL = "\n".join(DOCS.values())
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_every_platform_is_named_in_the_publishing_guide():
    for pid in platforms.load().platforms:
        assert f"`{pid}`" in DOCS["publishing.md"], pid


def test_every_profile_is_named_in_the_rendering_guide():
    for pid in platforms.load().profiles:
        assert f"`{pid}`" in DOCS["rendering-guide.md"], pid


def test_the_docs_describe_the_flags_render_py_accepts():
    for flag in ("--platform", "--profile"):
        assert flag in DOCS["rendering-guide.md"]
        assert flag in (ROOT / "scripts/render.py").read_text(encoding="utf-8")


def test_the_old_limits_file_is_gone_everywhere():
    assert not (ROOT / "config/publish.yaml").exists()
    for name, text in {**DOCS, "README.md": README, "README.zh-CN.md": (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")}.items():
        assert "config/publish.yaml" not in text, name


def test_the_safe_area_numbers_in_the_docs_match_the_registry():
    reg = platforms.load()
    v, p = reg.profile("vertical-9x16"), reg.profile("portrait-4x5")
    style = DOCS["visual-style.md"]
    assert f"{v.safe_x} px" in style and f"{v.safe_bottom} px" in style
    assert f"{p.safe_x} px" in style and f"{p.safe_bottom} px" in style
    assert re.search(rf"{p.width}\s*x\s*{p.height}", style)
