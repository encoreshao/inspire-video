import json

import pytest

from promo_fixtures import promo_project
from showcase import manifest as M
from showcase import templates as T
from test_showcase_manifest import brief


def test_a_known_template_passes_and_none_changes_nothing(tmp_path):
    p, m = promo_project(tmp_path)
    M.validate_showcase(m, p)
    M.validate_showcase({**m, "template": "minimal"}, p)


@pytest.mark.parametrize("bad", ["../etc/passwd", "CINEMATIC", "", None, 3, "nope"])
def test_an_unknown_template_id_is_a_clear_error_listing_the_valid_ids(tmp_path, bad):
    p, m = promo_project(tmp_path)
    with pytest.raises(M.ManifestError, match="cinematic"):
        M.validate_showcase({**m, "template": bad}, p)


def test_the_manifest_style_must_match_the_template(tmp_path):
    p, m = promo_project(tmp_path)
    with pytest.raises(M.ManifestError, match="style"):
        M.validate_showcase({**m, "template": "cinematic", "style": "device"}, p)


def test_a_template_max_is_enforced(tmp_path, monkeypatch):
    p, m = promo_project(tmp_path)
    m = {**m, "template": "minimal"}
    tight = {**T.get_template("minimal"), "shots": [
        {"id": "hero-push", "weight": 1, "max": 3}, {"id": "spotlight-focus", "weight": 1, "max": None},
        {"id": "statement", "weight": 1, "max": 1}]}
    monkeypatch.setattr(T, "get_template", lambda tid, directory=T.TEMPLATE_DIR: tight)
    with pytest.raises(M.ManifestError, match="hero-push.*at most 3"):
        M.validate_showcase(m, p)


def test_a_shot_outside_the_palette_is_a_warning_not_an_error(tmp_path):
    p, m = promo_project(tmp_path)
    m = {**m, "template": "minimal", "beats": [dict(b) for b in m["beats"]]}
    m["beats"][2] = {**m["beats"][2], "shot": "crash-zoom-punch", "target": "button-1"}
    M.validate_showcase(m, p)
    warnings = M.template_warnings(m)
    assert len(warnings) == 1 and "crash-zoom-punch" in warnings[0] and "minimal" in warnings[0]
    assert M.template_warnings({k: v for k, v in m.items() if k != "template"}) == []


@pytest.mark.parametrize("n", [10, 16, 40])
def test_scaffold_with_a_template_sets_style_theme_and_a_shot_per_beat(n):
    m = M.scaffold_manifest(brief(3), "acme", n, template="cinematic")
    t = T.get_template("cinematic")
    assert m["template"] == "cinematic" and m["style"] == "promo" and m["theme"] == "ink" and len(m["beats"]) == n
    shots = [b["shot"] for b in m["beats"]]
    assert shots == T.suggest_shots(t, n) and shots[0] == "statement" and shots[-1] == "statement"
    for b in m["beats"]:
        if b["shot"] == "statement":
            assert b["statement"] == "" and "asset" not in b and "focus" not in b
        else:
            assert "asset" in b and b["focus"] == {"x": 0, "y": 0, "w": 1, "h": 1}


def test_scaffold_without_a_template_is_unchanged():
    m = M.scaffold_manifest(brief(3), "acme", 12)
    assert "template" not in m and m["style"] == "device" and all("shot" not in b for b in m["beats"])


def test_scaffold_with_a_template_that_sets_no_theme_leaves_theme_out():
    assert "theme" not in M.scaffold_manifest(brief(3), "acme", 12, template="minimal")


def test_scaffold_with_an_unknown_template_is_a_manifest_error():
    with pytest.raises(M.ManifestError, match="cinematic"):
        M.scaffold_manifest(brief(3), "acme", 12, template="nope")


def test_cli_scaffold_template_flag_and_unknown_template(tmp_path, capsys):
    p = tmp_path / "proj"
    p.mkdir()
    (p / "brief.json").write_text(json.dumps(brief(2)))
    assert M.main(["scaffold", str(p), "--beats", "12", "--template", "calm"]) == 0
    assert json.loads((p / "video_manifest.json").read_text())["template"] == "calm"
    q = tmp_path / "other"
    q.mkdir()
    (q / "brief.json").write_text(json.dumps(brief(2)))
    assert M.main(["scaffold", str(q), "--template", "nope"]) == 1
    assert "error:" in capsys.readouterr().err
