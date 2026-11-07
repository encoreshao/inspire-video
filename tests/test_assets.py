import pytest

from imgs import gif, jpeg, png, webp
from showcase import assets as A


@pytest.mark.parametrize("name, data, size", [
    ("a.png", png(1440, 900), (1440, 900)),
    ("a.jpg", jpeg(390, 844), (390, 844)),
    ("a.gif", gif(640, 480), (640, 480)),
    ("a.webp", webp(1280, 720), (1280, 720)),
])
def test_image_size_per_format(tmp_path, name, data, size):
    p = tmp_path / name
    p.write_bytes(data)
    assert A.image_size(p) == size


@pytest.mark.parametrize("data", [b"", b"just some text", b"\x89PNG\r\n\x1a\n", png(0, 0)])
def test_fake_or_broken_images_are_rejected(tmp_path, data):
    p = tmp_path / "x.png"
    p.write_bytes(data)
    with pytest.raises(A.AssetError, match="x.png"):
        A.image_size(p)


def test_natural_order():
    names = ["10.png", "2.png", "01-home.png", "1.png"]
    assert sorted(names, key=A.natural_key) == ["01-home.png", "1.png", "2.png", "10.png"]


def test_rights_notes():
    assert A.rights_note("user") == "provided by the user"
    assert "https://x.io" in A.rights_note("capture", "https://x.io") and "confirm" in A.rights_note("capture", "https://x.io")
    assert "license: MIT" in A.rights_note("repo", "https://github.com/a/b", "MIT")
    assert "license: unknown" in A.rights_note("repo", "https://github.com/a/b")


def test_try_describe_accepts_a_good_image_and_names_the_reason_otherwise(tmp_path):
    ok = tmp_path / "ok.png"
    ok.write_bytes(png(800, 600))
    asset, why = A.try_describe(ok, "user", str(ok), A.rights_note("user"))
    assert why is None and asset["origin"] == "user" and (asset["width"], asset["height"]) == (800, 600)
    assert asset["rights_resolved"] is True and len(asset["sha256"]) == 64
    tiny = tmp_path / "tiny.png"
    tiny.write_bytes(png(100, 900))
    assert A.try_describe(tiny, "repo", "r", "x") == (None, "too small (100x900): the short side must be at least 320 px")
    txt = tmp_path / "notes.txt"
    txt.write_text("hi")
    assert A.try_describe(txt, "repo", "r", "x")[1].startswith("not an image file")
    asset, _ = A.try_describe(ok, "capture", "https://x.io", "r")
    assert asset["rights_resolved"] is False


def test_collect_user_shots_orders_naturally_and_rejects_with_reasons(tmp_path):
    d = tmp_path / "shots"
    d.mkdir()
    (d / "10-end.png").write_bytes(png(900, 900))
    (d / "2-editor.png").write_bytes(png(900, 901))
    (d / "1-home.jpg").write_bytes(jpeg(900, 900))
    (d / "dup.png").write_bytes(png(900, 901))          # same bytes as 2-editor.png
    (d / "tiny.png").write_bytes(png(50, 50))
    (d / "fake.png").write_bytes(b"not an image")
    (d / "notes.txt").write_text("x")
    (d / ".DS_Store").write_bytes(b"x")
    assets, rejected = A.collect_user_shots(d)
    assert [a["path"].rsplit("/", 1)[1] for a in assets] == ["1-home.jpg", "2-editor.png", "10-end.png"]
    reasons = {r["path"].rsplit("/", 1)[1]: r["reason"] for r in rejected}
    assert set(reasons) == {"dup.png", "tiny.png", "fake.png", "notes.txt"}
    assert "duplicate of 2-editor.png" in reasons["dup.png"] and "too small" in reasons["tiny.png"]


def test_missing_screenshots_folder_is_an_error(tmp_path):
    with pytest.raises(A.AssetError, match="does not exist"):
        A.collect_user_shots(tmp_path / "nope")


def test_dedupe_and_rank(tmp_path):
    def a(origin, sha):
        return {"origin": origin, "sha256": sha, "path": f"{origin}-{sha}"}
    items = [a("repo", "1"), a("user", "2"), a("capture", "3"), a("repo", "2"), a("user", "4")]
    kept, dropped = A.dedupe(items)
    assert [x["path"] for x in kept] == ["repo-1", "user-2", "capture-3", "user-4"]
    assert dropped == [{"path": "repo-2", "reason": "duplicate of user-2"}]
    assert [x["origin"] for x in A.rank_assets(kept)] == ["user", "user", "capture", "repo"]
