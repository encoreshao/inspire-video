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


def test_the_reference_states_every_limit_the_registry_has():
    for shot, meta in M.PROMO_SHOTS.items():
        limit = meta["maxPerVideo"]
        if limit is not None:
            assert (f"at most {limit}" in STYLE) or (limit == 1 and "once per video" in STYLE), shot
        if meta["minSeconds"] != 4:
            assert f"`{shot}` {meta['minSeconds']} s" in STYLE or f"{meta['minSeconds']} s" in STYLE, shot
    assert "Chinese or English" in STYLE or "either language" in STYLE                 # which language a statement may use
    assert "finished statement" in STYLE                                              # what a statement-first cover shows


def test_the_notice_names_every_promo_shot():
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    for shot in M.PROMO_SHOTS:
        assert shot in notice, shot


def test_the_promo_reference_describes_its_own_look():
    for needle in ("## Look", "ink", "880", "pips", "left-aligned", "no headline block"):
        assert needle in STYLE, needle


def test_the_skills_readme_tells_the_two_styles_apart():
    text = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")
    assert "editorial" in text and "cinematic" in text


def test_the_skill_and_the_promo_reference_document_templates():
    from showcase import templates as T
    assert "templates.py list" in SKILL and "--template" in SKILL
    assert "templates/<id>.yaml" in STYLE and "shots.json" in STYLE
    for tid in T.load_templates():
        assert f"`{tid}`" in STYLE, tid


def test_the_skill_shows_the_template_previews_when_the_user_chooses():
    assert "--json" in SKILL and "cover" in SKILL and "preview" in SKILL and "templates.py preview" in SKILL
    assert "ask" in SKILL.lower()


def test_every_shipped_template_has_a_cover_and_a_sample_clip():
    from showcase import templates as T
    for row in T.catalogue():
        assert row["cover"] and row["preview"], f"{row['id']}: run `python3 scripts/showcase/templates.py preview {row['id']}`"
        assert (ROOT / row["cover"]).stat().st_size > 1000 and (ROOT / row["preview"]).stat().st_size > 10000
