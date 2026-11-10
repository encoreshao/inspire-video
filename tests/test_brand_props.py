import pytest
from PIL import Image

from promo_fixtures import promo_project
from showcase import manifest as M
from showcase import render_showcase as R


@pytest.mark.parametrize("bad", ["purple", "#fff", "7c3aed", "#7c3aeZ", 5, ""])
def test_a_brand_colour_must_be_a_six_digit_hex(tmp_path, bad):
    p, m = promo_project(tmp_path)
    with pytest.raises(M.ManifestError, match="brand_color"):
        M.validate_showcase({**m, "brand_color": bad}, p)


def test_a_valid_brand_colour_passes(tmp_path):
    p, m = promo_project(tmp_path)
    M.validate_showcase({**m, "brand_color": "#7C3AED"}, p)


def props(p, m, sandbox_public):
    return R.build_props(m, p, None, R.stage(p, sandbox_public, m, None))


def test_the_brand_comes_from_the_manifest_first(tmp_path):
    p, m = promo_project(tmp_path)
    assert props(p, {**m, "brand_color": "#112233"}, tmp_path / "pub")["brand"] == "#112233"


def test_the_brand_is_read_from_the_captures_when_the_manifest_has_none(tmp_path):
    p, m = promo_project(tmp_path)
    cap = Image.new("RGB", (2880, 3000), "#ffffff")
    cap.paste((124, 58, 237), (200, 200, 2000, 900))
    cap.save(p / "assets" / "promo-1@2x.png")
    brand = props(p, m, tmp_path / "pub")["brand"]
    got = tuple(int(brand[i:i + 2], 16) for i in (1, 3, 5))
    assert all(abs(a - b) <= 40 for a, b in zip(got, (124, 58, 237)))


def test_a_colourless_site_has_no_brand_key(tmp_path):
    p, m = promo_project(tmp_path)
    assert "brand" not in props(p, m, tmp_path / "pub")
