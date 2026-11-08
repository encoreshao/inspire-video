from pathlib import Path

from showcase import manifest as M

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "inspire-showcase"
SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
STYLE = (SKILL_DIR / "references" / "promo-style.md").read_text(encoding="utf-8")
REVIEW = (SKILL_DIR / "references" / "final-review.md").read_text(encoding="utf-8")


def test_the_promo_reference_documents_every_shot_in_the_registry():
    for shot in M.PROMO_SHOTS:
        assert f"`{shot}`" in STYLE, shot


def test_the_promo_reference_gives_the_rules_the_validator_enforces():
    for needle in ("callout", "target", "focus", "statement", "back to back", "tall page", "once", "capture_page.py",
                   "storyboard", "--hide"):
        assert needle in STYLE, needle
    assert str(M.STATEMENT_UNITS) in STYLE and str(M.TALL_PAGE_PX) in STYLE


def test_the_credits_are_exact_about_what_was_and_was_not_borrowed():
    assert "video-shotcraft" in STYLE and "Apache-2.0" in STYLE
    for card in ("spotlight-hero-card", "crash-zoom-punch", "steep-tilt-glide"):
        assert card in STYLE, card
    assert "complete action arc" not in STYLE and "single hero target" in STYLE      # the arc of that card was not borrowed
    assert "pull-back" in STYLE and "second punch" in STYLE                         # what the crash card does that the shot does not
    assert "tilt-glide" in STYLE and "not included" in STYLE.lower()          # the shot that was left out, and why
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "spotlight-hero-card" in notice and "crash-zoom-punch" in notice and "no code" in notice.lower()


def test_the_skill_loads_the_promo_reference_and_describes_the_flow():
    assert "references/promo-style.md" in SKILL
    for needle in ("capture_page.py", "storyboard", '"style": "promo"'):
        assert needle in SKILL, needle


def test_both_readmes_describe_the_promo_style():
    for name in ("README.md", "README.zh-CN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "promo" in text and "hero-push" in text and "crash-zoom-punch" in text, name


def test_the_final_review_checks_the_promo_shots():
    assert "promo" in REVIEW.lower() and "S1" in REVIEW and "S6" in REVIEW
