import textwrap

import pytest

import platforms as P

GOOD = """
version: 1
profiles:
  vertical-9x16: {width: 1080, height: 1920, safe: {x: 114, top: 190, bottom: 330}, title_top: 256}
  portrait-4x5: {width: 1080, height: 1350, safe: {x: 60, top: 90, bottom: 150}, title_top: 110, compact: true}
  square-1x1: {width: 1080, height: 1080, safe: {x: 60, top: 80, bottom: 120}, title_top: 90, compact: true,
               supported: false, fallback: portrait-4x5}
platforms:
  a: {name: A, lang: zh, profile: vertical-9x16, duration: {min: 3, max: 100}, title_field: title,
      title: {min: 1, max: 10}, description_max: 100, hashtags_max: 3}
  b: {name: B, lang: zh, profile: vertical-9x16, duration: {min: 3, max: 600}, title_field: title,
      title: {max: 10}, description_max: 100, hashtags_max: 3, verified: true, file_stem: bee}
  c: {name: C, lang: en, profile: portrait-4x5, duration: {min: 3, max: 600}, title_field: title,
      title: {max: 10}, description_max: 100, hashtags_max: 3}
  d: {name: D, lang: en, profile: square-1x1, duration: {min: 3, max: 600}, title_field: title,
      title: {max: 10}, description_max: 100, hashtags_max: 3}
"""


def reg_from(tmp_path, text=GOOD):
    f = tmp_path / "platforms.yaml"
    f.write_text(textwrap.dedent(text), encoding="utf-8")
    return P.load(f)


def test_the_real_registry_loads_and_covers_the_six_platforms():
    reg = P.load()
    assert {"wechat_channels", "douyin", "rednote", "bilibili", "linkedin", "facebook"} <= set(reg.platforms)
    for pf in reg.platforms.values():
        assert pf.profile in reg.profiles
    assert reg.profile(P.DEFAULT_PROFILE).props() == {
        "id": "vertical-9x16", "width": 1080, "height": 1920, "safeX": 114, "safeTop": 190, "safeBottom": 330,
        "titleTop": 256, "compact": False}


def test_the_real_registry_keeps_the_legacy_limits_and_file_stems():
    reg = P.load()
    w, d = reg.platform("wechat_channels"), reg.platform("douyin")
    assert (w.title_field, w.title_min, w.title_max, w.description_max, w.hashtags_max, w.file_stem) == \
        ("short_title", 6, 16, 1000, 5, "wechat")
    assert (d.title_field, d.title_max, d.description_max, d.hashtags_max, d.file_stem) == ("title", 30, 1000, 5, "douyin")
    assert reg.platform("linkedin").lang == "en" and reg.platform("facebook").lang == "en"


def test_a_good_file_loads_with_defaults(tmp_path):
    reg = reg_from(tmp_path)
    a, b = reg.platform("a"), reg.platform("b")
    assert (a.title_min, a.verified, a.file_stem) == (1, False, "a")
    assert (b.title_min, b.verified, b.file_stem) == (1, True, "bee")
    assert reg.profile("portrait-4x5").props()["compact"] is True


@pytest.mark.parametrize("old, new, message", [
    ("profile: vertical-9x16, duration: {min: 3, max: 100}", "profile: nope, duration: {min: 3, max: 100}", "unknown profile 'nope'"),
    ("lang: zh, profile: vertical-9x16, duration: {min: 3, max: 100}", "lang: fr, profile: vertical-9x16, duration: {min: 3, max: 100}", "lang must be"),
    ("hashtags_max: 3}\n  b:", "}\n  b:", "missing 'hashtags_max'"),
    ("fallback: portrait-4x5}", "fallback: ghost}", "unknown profile 'ghost'"),
    ("supported: false, fallback: portrait-4x5}", "supported: false}", "needs a 'fallback'"),
])
def test_a_bad_file_is_rejected_with_a_clear_message(tmp_path, old, new, message):
    assert old in GOOD
    with pytest.raises(P.RegistryError, match=message):
        reg_from(tmp_path, GOOD.replace(old, new, 1))


def test_a_fallback_that_is_itself_unsupported_is_rejected(tmp_path):
    text = GOOD.replace("fallback: portrait-4x5}", "fallback: square-1x1}", 1)
    with pytest.raises(P.RegistryError, match="not supported either"):
        reg_from(tmp_path, text)


def test_unknown_ids_list_the_known_ones(tmp_path):
    reg = reg_from(tmp_path)
    with pytest.raises(P.RegistryError, match=r"unknown platform 'tiktok'; known: a, b, c, d"):
        reg.platform("tiktok")
    with pytest.raises(P.RegistryError, match="unknown profile 'x'"):
        reg.profile("x")


def test_output_names_keep_the_vertical_files_unchanged():
    assert P.video_name("slug", "vertical-9x16") == "slug.mp4"
    assert P.video_name("slug", "portrait-4x5") == "slug-portrait-4x5.mp4"
    assert P.cover_name("vertical-9x16") == "cover.png"
    assert P.cover_name("portrait-4x5") == "cover-portrait-4x5.png"


def test_platforms_on_one_profile_render_once(tmp_path):
    reg = reg_from(tmp_path)
    profiles, warnings = P.plan_renders(reg, ["a", "b"])
    assert [p.id for p in profiles] == ["vertical-9x16"] and warnings == []
    profiles, _ = P.plan_renders(reg, ["a", "c", "b"])
    assert [p.id for p in profiles] == ["vertical-9x16", "portrait-4x5"]


def test_an_unsupported_profile_falls_back_with_a_warning(tmp_path):
    reg = reg_from(tmp_path)
    profiles, warnings = P.plan_renders(reg, ["d", "c"])
    assert [p.id for p in profiles] == ["portrait-4x5"]
    assert len(warnings) == 1 and "square-1x1" in warnings[0] and "portrait-4x5" in warnings[0]


def test_an_explicit_profile_overrides_the_platforms_and_nothing_means_vertical(tmp_path):
    reg = reg_from(tmp_path)
    assert [p.id for p in P.plan_renders(reg, ["a"], "portrait-4x5")[0]] == ["portrait-4x5"]
    assert [p.id for p in P.plan_renders(reg)[0]] == ["vertical-9x16"]
    with pytest.raises(P.RegistryError):
        P.plan_renders(reg, ["nope"])


def test_the_duration_check_names_the_platform_that_fails(tmp_path):
    reg = reg_from(tmp_path)
    assert P.check_duration(reg, ["a", "b"], 60) == []
    errs = P.check_duration(reg, ["a", "b"], 120)
    assert len(errs) == 1 and errs[0].startswith("a:") and "100" in errs[0]


def test_a_duplicate_platform_id_is_rejected(tmp_path):
    copied = GOOD + """  a: {name: A2, lang: zh, profile: vertical-9x16, duration: {min: 3, max: 9}, title_field: title,
      title: {max: 10}, description_max: 100, hashtags_max: 3, file_stem: a2}
"""
    with pytest.raises(P.RegistryError, match="duplicate key 'a'"):
        reg_from(tmp_path, copied)


def test_a_duplicate_profile_id_is_rejected(tmp_path):
    dup = GOOD.replace("platforms:\n", "  portrait-4x5: {width: 1, height: 1, safe: {x: 1, top: 1, bottom: 1}, title_top: 1}\nplatforms:\n", 1)
    with pytest.raises(P.RegistryError, match="duplicate key 'portrait-4x5'"):
        reg_from(tmp_path, dup)


def test_two_platforms_may_not_share_a_file_stem(tmp_path):
    clash = GOOD.replace("hashtags_max: 3, verified: true, file_stem: bee}", "hashtags_max: 3, file_stem: a}", 1)
    assert clash != GOOD
    with pytest.raises(P.RegistryError, match="platforms a and b share file_stem 'a'"):
        reg_from(tmp_path, clash)
