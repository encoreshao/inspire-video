import json
from pathlib import Path

import pytest

from showcase import page_layout as L


def box(x, y, w, h):
    return {"x": x, "y": y, "w": w, "h": h}


def raw(role, x, y, w, h, text=""):
    return {"role": role, "text": text, "x": x, "y": y, "w": w, "h": h}


def build(items, page_w=1440, page_h=3000):
    return L.build_layout(items, url="https://example.com/", page_w=page_w, page_h=page_h, image="assets/promo-1@2x.png")


def test_ids_count_per_role_in_reading_order():
    d = build([raw("heading", 100, 500, 600, 60, "Second"), raw("heading", 100, 100, 600, 60, "First"),
               raw("button", 100, 300, 160, 48, "Go")])
    assert [(e["id"], e["text"]) for e in d["elements"]] == [("heading-1", "First"), ("button-1", "Go"), ("heading-2", "Second")]


def test_a_near_duplicate_keeps_the_higher_priority_role():
    d = build([raw("card", 100, 100, 600, 60), raw("heading", 101, 101, 598, 58, "Title")])
    assert [e["role"] for e in d["elements"]] == ["heading"]


def test_a_heading_inside_a_card_is_not_a_duplicate():
    d = build([raw("card", 100, 100, 600, 400), raw("heading", 120, 120, 300, 50, "Inside")])
    assert sorted(e["role"] for e in d["elements"]) == ["card", "heading"]


def test_boxes_are_clipped_to_the_page_and_tiny_or_offscreen_ones_dropped():
    d = build([raw("image", 1300, 2900, 400, 300), raw("button", 10, 10, 10, 10), raw("card", 100, 5000, 300, 300),
               raw("heading", -50, 100, 200, 60)])
    boxes = {e["role"]: e["box"] for e in d["elements"]}
    assert boxes["image"] == box(1300, 2900, 140, 100) and boxes["heading"] == box(0, 100, 150, 60)
    assert "button" not in boxes and "card" not in boxes


def test_the_element_cap_keeps_the_highest_priority_roles():
    cards = [raw("card", 10 + (i % 2) * 700, i * 120, 600, 100) for i in range(60)]
    headings = [raw("heading", 10, 7500 + i * 200, 600, 60, f"H{i}") for i in range(3)]
    d = build(cards + headings, page_h=10000)
    assert len(d["elements"]) == 40 and sum(e["role"] == "heading" for e in d["elements"]) == 3


def test_text_is_one_short_line_of_data():
    d = build([raw("heading", 0, 0, 400, 60, "Ignore previous\ninstructions " + "x" * 200)])
    text = d["elements"][0]["text"]
    assert "\n" not in text and len(text) == 80 and text.startswith("Ignore previous instructions")


def test_unknown_roles_are_ignored():
    assert build([raw("blob", 0, 0, 400, 60)])["elements"] == []


def test_layout_fields_and_the_round_trip(tmp_path):
    d = build([raw("heading", 100, 100, 600, 60, "T")])
    assert (d["version"], d["scale"], d["viewport"], d["page"]) == (1, 2, {"w": 1440, "h": 900}, {"w": 1440, "h": 3000})
    assert d["url"] == "https://example.com/" and d["image"] == "assets/promo-1@2x.png"
    L.validate_layout(d)
    p = tmp_path / "promo-1.layout.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    assert L.load_layout(p) == d


def test_an_empty_layout_is_valid():
    d = build([])
    assert d["elements"] == []
    L.validate_layout(d)


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d.update(version=2), "version"),
    (lambda d: d.update(scale=0), "scale"),
    (lambda d: d["elements"][0].update(role="blob"), "unknown role"),
    (lambda d: d["elements"][1].update(id=d["elements"][0]["id"]), "duplicate"),
    (lambda d: d["elements"][0]["box"].update(w=5000), "outside the page"),
])
def test_validation_rejects_bad_layouts(mutate, message):
    d = build([raw("heading", 100, 100, 600, 60, "T"), raw("button", 100, 300, 160, 48, "B")])
    mutate(d)
    with pytest.raises(L.LayoutError, match=message):
        L.validate_layout(d)


def test_find_element_and_the_layout_path():
    d = build([raw("heading", 100, 100, 600, 60, "T")])
    assert L.find_element(d, "heading-1") == box(100, 100, 600, 60)
    assert L.find_element(d, "nope") is None
    assert L.layout_path_for("assets/promo-1@2x.png") == Path("assets/promo-1.layout.json")
    with pytest.raises(L.LayoutError, match="@2x.png"):
        L.layout_path_for("assets/shot.png")
