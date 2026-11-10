import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from imgs import png
from promo_fixtures import ELEMENTS, promo_project
from showcase import page_layout as L
from showcase import manifest as M

ROOT = Path(__file__).resolve().parent.parent


def beat_with(m, index, **changes):
    m = copy.deepcopy(m)
    m["beats"][index].update(changes)
    return m


def beat_without(m, index, *keys):
    m = copy.deepcopy(m)
    for key in keys:
        m["beats"][index].pop(key, None)
    return m


def test_a_valid_promo_manifest_passes_and_the_style_is_known(tmp_path):
    p, m = promo_project(tmp_path)
    assert M.STYLES == ("device", "promo")
    M.validate_showcase(m, p)


@pytest.mark.parametrize("make, message", [
    (lambda m: beat_with(m, 0, shot="whip-pan"), "unknown shot"),
    (lambda m: beat_with(m, 0, callout="Look here"), "callout"),
    (lambda m: beat_with(m, 0, focus={"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.4}), "exactly one"),
    (lambda m: beat_without(m, 0, "target"), "exactly one"),
    (lambda m: beat_with(m, 0, target="heading-9"), "heading-9"),
    (lambda m: beat_with(m, 0, target=""), "target"),
    (lambda m: beat_with(m, 1, shot="hero-push"), "back to back"),
])
def test_promo_beats_are_validated(tmp_path, make, message):
    p, m = promo_project(tmp_path)
    with pytest.raises(M.ManifestError, match=message):
        M.validate_showcase(make(m), p)


def test_the_error_names_the_beat_and_lists_the_elements_that_exist(tmp_path):
    p, m = promo_project(tmp_path)
    with pytest.raises(M.ManifestError) as e:
        M.validate_showcase(beat_with(m, 2, target="nope-1"), p)
    assert "'what'" in str(e.value) and "heading-1" in str(e.value)


def test_a_target_needs_a_layout_file_beside_a_promo_capture(tmp_path):
    p, m = promo_project(tmp_path)
    (p / "assets" / "promo-1.layout.json").unlink()
    with pytest.raises(M.ManifestError, match="layout"):
        M.validate_showcase(m, p)


def test_a_target_needs_an_image_named_like_a_promo_capture(tmp_path):
    p, m = promo_project(tmp_path)
    (p / "assets" / "shot.png").write_bytes(png(1440, 900))
    with pytest.raises(M.ManifestError, match="layout"):
        M.validate_showcase(beat_with(m, 0, asset="assets/shot.png"), p)


def test_a_broken_layout_file_is_reported_with_the_beat(tmp_path):
    p, m = promo_project(tmp_path)
    (p / "assets" / "promo-1.layout.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(M.ManifestError, match="'hook'"):
        M.validate_showcase(m, p)


def test_a_user_screenshot_works_with_a_focus_rectangle_and_no_layout(tmp_path):
    p, m = promo_project(tmp_path)
    (p / "assets" / "shot.png").write_bytes(png(1440, 900))
    m = beat_with(beat_without(m, 0, "target"), 0, asset="assets/shot.png", focus={"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.4})
    M.validate_showcase(m, p)
    box, info = M.beat_target(m["beats"][0], p)
    assert box == {"x": 144, "y": 90, "w": 720, "h": 360}
    assert info == {"page": {"w": 1440, "h": 900}, "scale": 1, "layout": None}


def test_beat_target_reads_the_element_box_and_the_page_from_the_layout(tmp_path):
    p, m = promo_project(tmp_path)
    box, info = M.beat_target(m["beats"][1], p)
    assert box == {"x": 100, "y": 300, "w": 200, "h": 48}
    assert info["page"] == {"w": 1440, "h": 1500} and info["scale"] == 2 and info["layout"]["version"] == 1


def test_a_shot_limit_and_a_minimum_length_come_from_the_shot_table(tmp_path, monkeypatch):
    p, m = promo_project(tmp_path)
    limited = {**M.PROMO_SHOTS, "hero-push": {**M.PROMO_SHOTS["hero-push"], "maxPerVideo": 1}}
    monkeypatch.setattr(M, "PROMO_SHOTS", limited)
    with pytest.raises(M.ManifestError, match="at most 1"):
        M.validate_showcase(m, p)                                  # hero-push is used twice
    slow = {**M.PROMO_SHOTS, "hero-push": {**M.PROMO_SHOTS["hero-push"], "minSeconds": 20, "maxPerVideo": None}}
    monkeypatch.setattr(M, "PROMO_SHOTS", slow)
    with pytest.raises(M.ManifestError, match="at least 20"):
        M.validate_showcase(m, p)                                  # the default beat is 10 s


def test_the_device_checks_do_not_apply_to_a_promo_manifest(tmp_path):
    p, m = promo_project(tmp_path)
    assert M.crop_warnings(m, p) == []


def test_the_python_shot_table_is_the_shared_json_file_and_not_a_copy():
    table = json.loads((ROOT / "video" / "src" / "showcase" / "shots.json").read_text(encoding="utf-8"))
    assert M.PROMO_SHOTS == table
    assert "\"needsTallPage\": " not in (ROOT / "scripts" / "showcase" / "manifest.py").read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_python_shot_table_matches_the_javascript_registry():
    code = "import('./video/src/showcase/shots.mjs').then((m) => console.log(JSON.stringify(m.shotMeta())))"
    r = subprocess.run(["node", "-e", code], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == M.PROMO_SHOTS



def test_a_crash_zoom_may_be_used_once_per_video(tmp_path):
    p, m = promo_project(tmp_path)
    M.validate_showcase(beat_with(m, 1, shot="crash-zoom-punch"), p)
    twice = beat_with(beat_with(m, 1, shot="crash-zoom-punch"), 3, shot="crash-zoom-punch")
    with pytest.raises(M.ManifestError, match="at most 1"):
        M.validate_showcase(twice, p)


def test_pan_reveal_needs_a_tall_page(tmp_path):
    p, m = promo_project(tmp_path)
    M.validate_showcase(beat_with(m, 0, shot="pan-reveal"), p)       # 1500 px is tall enough: 1.5 x the 900 px capture viewport
    layout = L.build_layout(ELEMENTS, url="https://example.com/", page_w=1440, page_h=1200, image="assets/promo-1@2x.png")
    (p / "assets" / "promo-1.layout.json").write_text(json.dumps(layout), encoding="utf-8")
    (p / "assets" / "promo-1@2x.png").write_bytes(png(2880, 2400))
    with pytest.raises(M.ManifestError, match="tall"):
        M.validate_showcase(beat_with(m, 0, shot="pan-reveal"), p)
    M.validate_showcase(m, p)                                         # the other shots do not care


def statement_beat(m, index, text="Calm work, done for you."):
    m = beat_without(m, index, "asset", "target", "focus")
    return beat_with(m, index, shot="statement", statement=text)


def test_a_statement_beat_shows_text_and_needs_no_capture(tmp_path):
    p, m = promo_project(tmp_path)
    M.validate_showcase(statement_beat(m, 0), p)
    M.validate_showcase(statement_beat(statement_beat(m, 0), 3, "你专注真正的工作"), p)    # a Chinese statement is fine too


@pytest.mark.parametrize("make, message", [
    (lambda m: beat_without(statement_beat(m, 0), 0, "statement"), "statement"),
    (lambda m: statement_beat(m, 0, "x" * 29), "wide"),
    (lambda m: beat_with(statement_beat(m, 0), 0, target="heading-1"), "no capture"),
    (lambda m: beat_with(statement_beat(m, 0), 0, asset="assets/promo-1@2x.png"), "no capture"),
    (lambda m: beat_with(m, 0, statement="Only a statement beat has one."), "only"),
])
def test_statement_beats_are_validated(tmp_path, make, message):
    p, m = promo_project(tmp_path)
    with pytest.raises(M.ManifestError, match=message):
        M.validate_showcase(make(m), p)


def test_a_statement_is_limited_by_the_shot_table(tmp_path, monkeypatch):
    p, m = promo_project(tmp_path)
    twice = statement_beat(statement_beat(m, 0), 2)
    M.validate_showcase(twice, p)                                    # two are allowed
    monkeypatch.setattr(M, "PROMO_SHOTS", {**M.PROMO_SHOTS, "statement": {**M.PROMO_SHOTS["statement"], "maxPerVideo": 1}})
    with pytest.raises(M.ManifestError, match="at most 1"):
        M.validate_showcase(twice, p)


def test_a_crash_zoom_needs_a_target_the_camera_can_punch_in_on(tmp_path):
    p, m = promo_project(tmp_path)
    big = beat_with(beat_without(m, 1, "target"), 1, shot="crash-zoom-punch", focus={"x": 0.0, "y": 0.0, "w": 0.95, "h": 0.5})
    with pytest.raises(M.ManifestError, match="too large for crash-zoom-punch"):
        M.validate_showcase(big, p)
    small = beat_with(beat_without(m, 1, "target"), 1, shot="crash-zoom-punch", focus={"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.05})
    M.validate_showcase(small, p)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_python_punch_rule_agrees_with_the_javascript_camera():
    pages = [{"w": 1440, "h": 1500}, {"w": 1440, "h": 6000}, {"w": 1440, "h": 500}]
    boxes = [{"x": 0, "y": 0, "w": w, "h": h} for w in (20, 200, 600, 900, 1100, 1368, 1440) for h in (10, 80, 400, 750, 1400)]
    cases = [(pg, b, sc) for pg in pages for b in boxes for sc in (1, 2) if b["h"] <= pg["h"]]
    code = ("const cases = JSON.parse(process.argv[1]);"
            "Promise.all([import('./video/src/showcase/promo.mjs'), import('./video/src/showcase/shots.mjs')]).then(([P, S]) => {"
            "console.log(JSON.stringify(cases.map(([page, box, scale]) => {"
            "const stage = {w: 880, h: 960};"
            "const z0 = P.minZoom(page, stage);"
            "const cam = P.promoCamera({shot: S.SHOTS['crash-zoom-punch'], target: box, page, stage, scale, progress: 1, seconds: 10});"
            "return cam.zoom > z0 + 1e-9;})));});")
    import json as _json
    r = subprocess.run(["node", "-e", code, _json.dumps(cases)], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    moves = _json.loads(r.stdout)
    assert len(moves) == len(cases) and any(moves) and not all(moves)           # the grid has both kinds
    for (page, box, scale), js in zip(cases, moves):
        assert M.crash_punch_possible(box, page, scale) == js, (page, box, scale)


def test_a_layout_that_does_not_match_its_image_is_reported_with_the_beat(tmp_path):
    p, m = promo_project(tmp_path)
    M.validate_showcase(m, p)                                               # 2880x3000 is exactly 1440x1500 at 2x
    (p / "assets" / "promo-1@2x.png").write_bytes(png(2880, 2000))          # a stale image: the layout says 3000 px high
    with pytest.raises(M.ManifestError, match="'hook'.*layout.*capture the page again"):
        M.validate_showcase(m, p)


def test_a_focus_rectangle_that_rounds_to_nothing_is_rejected(tmp_path):
    p, m = promo_project(tmp_path)
    tiny = beat_with(beat_without(m, 0, "target"), 0, focus={"x": 0.1, "y": 0.1, "w": 0.0001, "h": 0.05})
    with pytest.raises(M.ManifestError, match="too small"):
        M.validate_showcase(tiny, p)


@pytest.mark.parametrize("shot", [["hero-push"], {"a": 1}, 7, ""])
def test_a_shot_of_the_wrong_type_is_a_clear_error_not_a_traceback(tmp_path, shot):
    p, m = promo_project(tmp_path)
    with pytest.raises(M.ManifestError, match="shot"):
        M.validate_showcase(beat_with(m, 0, shot=shot), p)


@pytest.mark.parametrize("text, ok", [("a" * 28, True), ("a" * 29, False), ("字" * 14, True), ("字" * 15, False), ("字" * 13 + "ab", True)])
def test_the_statement_width_limit_sits_exactly_at_28_units(tmp_path, text, ok):
    p, m = promo_project(tmp_path)
    m = statement_beat(m, 0, text)
    if ok:
        M.validate_showcase(m, p)
    else:
        with pytest.raises(M.ManifestError, match="wide"):
            M.validate_showcase(m, p)


@pytest.mark.parametrize("page_h, ok", [(1349, False), (1350, True)])
def test_pan_reveal_needs_a_page_of_at_least_1350_px(tmp_path, page_h, ok):
    p, m = promo_project(tmp_path)
    layout = L.build_layout(ELEMENTS, url="https://example.com/", page_w=1440, page_h=page_h, image="assets/promo-1@2x.png")
    (p / "assets" / "promo-1.layout.json").write_text(json.dumps(layout), encoding="utf-8")
    (p / "assets" / "promo-1@2x.png").write_bytes(png(2880, page_h * 2))
    m = beat_with(m, 0, shot="pan-reveal")
    if ok:
        M.validate_showcase(m, p)
    else:
        with pytest.raises(M.ManifestError, match="tall"):
            M.validate_showcase(m, p)


def test_a_promo_headline_must_fit_the_larger_cover_type(tmp_path):
    p, m = promo_project(tmp_path)
    m["headline"] = "任何网站都能轻松变成精彩短视频哦呀啊"        # 18 characters: two lines of nine
    M.validate_showcase(m, p)
    m["headline"] = "任何网站都能轻松变成精彩短视频哦呀啊啊"       # 19: a ten-character line passes the 880 px box
    with pytest.raises(M.ManifestError, match="headline"):
        M.validate_showcase(m, p)
