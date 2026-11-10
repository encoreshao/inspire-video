import pytest

from promo_fixtures import promo_project
from showcase import manifest as M
from showcase import render_showcase as R


def with_statement(tmp_path, **extra):
    p, m = promo_project(tmp_path)
    first = {"id": m["beats"][0]["id"], "shot": "statement", "statement": "Capital meets innovation.", "en": "An AI platform.",
             "zh": "一个 AI 平台。", **extra}
    m = {**m, "beats": [first] + m["beats"][1:]}
    return p, m


def test_a_statement_may_carry_a_backdrop_and_up_to_three_facts(tmp_path):
    p, m = with_statement(tmp_path, backdrop="assets/promo-1@2x.png", facts=["Free plan", "Web app · Chrome · MCP"])
    M.validate_showcase(m, p)


@pytest.mark.parametrize("extra,needle", [
    ({"backdrop": "assets/missing.png"}, "backdrop"),
    ({"backdrop": "/etc/passwd"}, "backdrop"),
    ({"backdrop": "../x.png"}, "backdrop"),
    ({"backdrop": 5}, "backdrop"),
    ({"facts": "Free plan"}, "facts"),
    ({"facts": []}, "facts"),
    ({"facts": ["a", "b", "c", "d"]}, "facts"),
    ({"facts": ["ok", ""]}, "facts"),
    ({"facts": ["x" * 29]}, "facts"),
    ({"facts": [5]}, "facts"),
])
def test_bad_backdrop_and_facts_are_clear_errors(tmp_path, extra, needle):
    p, m = with_statement(tmp_path, **extra)
    with pytest.raises(M.ManifestError, match=needle):
        M.validate_showcase(m, p)


@pytest.mark.parametrize("key,value", [("backdrop", "assets/promo-1@2x.png"), ("facts", ["Free plan"])])
def test_a_camera_beat_may_not_carry_them(tmp_path, key, value):
    p, m = promo_project(tmp_path)
    m = {**m, "beats": [{**m["beats"][0], key: value}] + m["beats"][1:]}
    with pytest.raises(M.ManifestError, match="only for the statement"):
        M.validate_showcase(m, p)


def test_the_props_carry_the_staged_backdrop_and_the_facts(tmp_path):
    p, m = with_statement(tmp_path, backdrop="assets/promo-1@2x.png", facts=["Free plan"])
    public = tmp_path / "pub"
    staged = R.stage(p, public, m, None)
    entry = R.build_props(m, p, None, staged)["beats"][0]
    assert entry["shot"] == "statement" and entry["facts"] == ["Free plan"]
    assert entry["backdrop"] == staged[m["beats"][0]["id"]]["backdrop"] and (public / entry["backdrop"]).is_file()
    assert entry["backdropSize"] == {"w": 2880, "h": 3000}


def test_a_plain_statement_has_neither_key(tmp_path):
    p, m = with_statement(tmp_path)
    entry = R.build_props(m, p, None, R.stage(p, tmp_path / "pub", m, None))["beats"][0]
    assert "backdrop" not in entry and "facts" not in entry
