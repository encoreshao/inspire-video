import pytest
from PIL import Image

from showcase import brand as B


def save(tmp_path, name, size, fill, blocks=()):
    im = Image.new("RGB", size, fill)
    for box, colour in blocks:
        im.paste(colour, box)
    p = tmp_path / name
    im.save(p)
    return p


def hue_close(hex_colour, rgb, tol=40):
    got = tuple(int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return all(abs(a - b) <= tol for a, b in zip(got, rgb))


def test_the_accent_is_the_dominant_saturated_colour_not_the_white_page(tmp_path):
    p = save(tmp_path, "a.png", (400, 1600), "#ffffff", [((20, 40, 380, 200), (124, 58, 237)), ((20, 300, 60, 330), (230, 60, 40))])
    assert hue_close(B.dominant_accent(p), (124, 58, 237))


def test_the_larger_coloured_area_wins(tmp_path):
    p = save(tmp_path, "b.png", (400, 400), "#f4f4f4", [((0, 0, 400, 100), (30, 90, 220)), ((0, 200, 400, 240), (220, 40, 40))])
    assert hue_close(B.dominant_accent(p), (30, 90, 220))


@pytest.mark.parametrize("fill", ["#ffffff", "#808080", "#101010"])
def test_a_page_with_no_colour_has_no_accent(tmp_path, fill):
    assert B.dominant_accent(save(tmp_path, "c.png", (200, 200), fill)) is None


def test_a_missing_or_broken_image_has_no_accent(tmp_path):
    assert B.dominant_accent(tmp_path / "nope.png") is None
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    assert B.dominant_accent(bad) is None


def test_the_first_image_with_an_accent_is_used(tmp_path):
    grey = save(tmp_path, "g.png", (100, 100), "#999999")
    blue = save(tmp_path, "u.png", (100, 100), "#ffffff", [((0, 0, 100, 60), (20, 80, 200))])
    assert hue_close(B.first_accent([grey, blue]), (20, 80, 200))
    assert B.first_accent([grey]) is None and B.first_accent([]) is None


def test_a_small_accent_on_a_mostly_white_page_still_counts(tmp_path):
    # thin purple headline words and one small button: about 0.12% of the page, the way a clean marketing page looks
    p = save(tmp_path, "d.png", (1440, 6000), "#fafafa", [((100, 300, 220, 330), (124, 58, 237)), ((100, 2000, 220, 2030), (124, 58, 237)),
                                                           ((100, 4000, 220, 4030), (124, 58, 237))])
    assert hue_close(B.dominant_accent(p), (124, 58, 237))


def test_a_handful_of_stray_coloured_pixels_is_not_an_accent(tmp_path):
    p = save(tmp_path, "e.png", (1440, 6000), "#fafafa", [((10, 10, 14, 14), (230, 60, 40))])
    assert B.dominant_accent(p) is None
