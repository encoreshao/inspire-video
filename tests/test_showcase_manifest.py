import copy
import json

import pytest

from imgs import png
from showcase import manifest as M

SENTENCES = ["Make videos from any website.", "Screenshots alone do not tell the story.",
             "It reads the site and writes the beats.", "Try it on your own project."]


def project(tmp_path, n=12, shape=(900, 600)):
    p = tmp_path / "proj"
    (p / "assets").mkdir(parents=True)
    beats = []
    for i, bid in enumerate(M.beat_ids(n)):
        en = f"{SENTENCES[i % len(SENTENCES)][:-1]} number {i}."
        (p / "assets" / f"{i}.png").write_bytes(png(*shape))
        beats.append({"id": bid, "en": en, "zh": "这是一句中文。", "asset": f"assets/{i}.png",
                      "focus": {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.4}, "callout": "Look here"})
    m = {"type": "showcase", "project_id": "acme-demo", "style": "device", "theme": "light",
         "headline": "任何网站都能变成短视频", "subtitle": "Turn any site into a short video",
         "project": {"name": "Acme", "tagline": "Widgets"},
         "source": {"kind": "website", "url": "https://example.com/", "label": "example.com"},
         "beats": beats, "provenance": {"rights_confirmed": True, "source_reference": "https://example.com/"}}
    return p, m


def spread(n, total=156.0):
    """n beat lengths that differ a little and add up to total."""
    base = [12.0 - 0.5 * (i % 4) for i in range(n)]
    scale = total / sum(base)
    return tuple(round(x * scale, 3) for x in base)


def timings(m, secs=None):
    secs = secs or spread(len(m["beats"]))
    return {"engine": "say", "voice": None, "lang": "en", "total": sum(secs),
            "beats": [{"id": b["id"], "audio": f"audio/{b['id']}.wav", "audio_seconds": s - 0.4, "seconds": s}
                      for b, s in zip(m["beats"], secs)]}


def test_a_complete_manifest_validates(tmp_path):
    p, m = project(tmp_path)
    M.validate_showcase(m, p)
    M.validate_showcase(m, p, timings(m))


def test_default_beat_length_reaches_the_two_minute_minimum(tmp_path):
    p, m = project(tmp_path, 12)
    assert M.beat_seconds_list(m) == [10.0] * 12
    p2, m2 = project(tmp_path / "x", 16)
    assert M.beat_seconds_list(m2) == [7.5] * 16
    p3, m3 = project(tmp_path / "y", 40)
    assert M.beat_seconds_list(m3) == [4.0] * 40            # the floor of 4 s a beat; 40 beats may exceed the minimum
    t = timings(m)
    assert M.beat_seconds_list(m, t) == [b["seconds"] for b in t["beats"]]


def test_frame_windows_are_contiguous_and_keep_the_total():
    secs = [10.4, 11.3, 9.9, 8.4] * 3
    w = M.frame_windows(secs, 30)
    assert w[0]["start"] == 0 and all(w[i]["start"] + w[i]["frames"] == w[i + 1]["start"] for i in range(len(w) - 1))
    assert abs(sum(x["frames"] for x in w) - round(sum(secs) * 30)) <= 1
    assert all(x["frames"] >= 1 for x in M.frame_windows([0.0, 0.01], 30))


@pytest.mark.parametrize("mutate, needle", [
    (lambda m: m.update(type="speaker"), "type"),
    (lambda m: m.update(project_id="Bad Id"), "project_id"),
    (lambda m: m.update(style="kinetic"), "style"),
    (lambda m: m.update(theme="neon"), "theme"),
    (lambda m: m.update(headline=" "), "headline"),
    (lambda m: m.update(subtitle=""), "subtitle"),
    (lambda m: m["project"].update(name=""), "project.name"),
    (lambda m: m["source"].pop("label"), "source"),
    (lambda m: m.update(beats=m["beats"][:9]), "10 to 40 beats"),
    (lambda m: m["beats"].__setitem__(1, {**m["beats"][1], "id": "hook"}), "duplicate"),
    (lambda m: m["beats"][0].update(id="../evil"), "beat id"),
    (lambda m: m["beats"][0].update(en=""), "'hook'.*en"),
    (lambda m: m["beats"][0].update(zh=" "), "'hook'.*zh"),
    (lambda m: m["beats"][0].update(en="x" * 101), "100"),
    (lambda m: m["beats"][0].update(en="First sentence. Second sentence here."), "one sentence"),
    (lambda m: m["beats"][0].update(callout="c" * 41), "callout"),
    (lambda m: m["beats"][0].update(focus={"x": 0.8, "y": 0, "w": 0.5, "h": 0.5}), "focus"),
    (lambda m: m["beats"][0].update(focus={"x": 0, "y": 0, "w": 0, "h": 0.5}), "focus"),
    (lambda m: m["beats"][0].update(focus={"x": "a", "y": 0, "w": 1, "h": 1}), "focus"),
    (lambda m: m["provenance"].update(rights_confirmed=False), "rights_confirmed"),
])
def test_invalid_manifests_are_refused_with_the_problem_named(tmp_path, mutate, needle):
    p, m = project(tmp_path)
    mutate(m)
    with pytest.raises(M.ManifestError, match=needle):
        M.validate_showcase(m, p)


@pytest.mark.parametrize("asset", ["../outside.png", "/etc/passwd", "assets/missing.png", "assets", ""])
def test_assets_must_be_real_images_inside_the_project(tmp_path, asset):
    p, m = project(tmp_path)
    (tmp_path / "outside.png").write_bytes(png(900, 600))
    m["beats"][0]["asset"] = asset
    with pytest.raises(M.ManifestError, match="asset"):
        M.validate_showcase(m, p)


def test_a_symlink_out_of_the_project_and_a_fake_image_are_refused(tmp_path):
    p, m = project(tmp_path)
    (tmp_path / "secret.png").write_bytes(png(900, 600))
    (p / "assets" / "link.png").symlink_to(tmp_path / "secret.png")
    m["beats"][0]["asset"] = "assets/link.png"
    with pytest.raises(M.ManifestError, match="asset"):
        M.validate_showcase(m, p)
    (p / "assets" / "fake.png").write_bytes(b"not an image")
    m["beats"][0]["asset"] = "assets/fake.png"
    with pytest.raises(M.ManifestError, match="asset"):
        M.validate_showcase(m, p)


def test_timings_must_match_the_beats_and_the_length_rule(tmp_path):
    p, m = project(tmp_path)
    t = timings(m)
    t["beats"][0]["id"] = "other"
    with pytest.raises(M.ManifestError, match="timings"):
        M.validate_showcase(m, p, t)
    t = timings(m)
    t["beats"] = t["beats"][:-1]
    with pytest.raises(M.ManifestError, match="timings"):
        M.validate_showcase(m, p, t)
    with pytest.raises(M.ManifestError, match="minimum"):
        M.validate_showcase(m, p, timings(m, (9.0,) * 12))
    with pytest.raises(M.ManifestError, match="maximum"):
        M.validate_showcase(m, p, timings(m, (26.0,) * 12))


def test_a_voice_without_timings_asks_to_narrate_first(tmp_path):
    p, m = project(tmp_path)
    m["voice"] = "encore"
    with pytest.raises(M.ManifestError, match="narrate"):
        M.validate_showcase(m, p)
    M.validate_showcase(m, p, narrated(m, voice="encore"))


def brief(n_assets=3):
    return {"version": 1, "source": {"kind": "website", "url": "https://example.com/", "host": "example.com", "repo_path": ""},
            "assets": [{"path": f"assets/{i}.png", "width": 900, "height": 600} for i in range(n_assets)],
            "facts": [{"id": "f1", "claim": "The site is titled \"Acme\"", "source": "https://example.com/"}]}


def test_scaffold_cycles_assets_and_leaves_the_text_to_fill_in(tmp_path):
    m = M.scaffold_manifest(brief(3), "acme-demo", 12)
    assert m["type"] == "showcase" and m["project_id"] == "acme-demo" and len(m["beats"]) == 12
    assert [b["asset"] for b in m["beats"]] == [f"assets/{i % 3}.png" for i in range(12)]
    assert all(b["en"] == "" and b["zh"] == "" for b in m["beats"]) and m["headline"] == ""
    assert m["source"] == {"kind": "website", "url": "https://example.com/", "label": "example.com"}
    assert m["provenance"]["rights_confirmed"] is False
    with pytest.raises(M.ManifestError):
        M.scaffold_manifest(brief(0), "acme-demo", 12)


def test_cli_scaffold_never_overwrites_and_validate_reports(tmp_path, capsys):
    p = tmp_path / "proj"
    p.mkdir()
    (p / "brief.json").write_text(json.dumps(brief(2)))
    assert M.main(["scaffold", str(p), "--beats", "12"]) == 0
    first = (p / "video_manifest.json").read_text()
    assert M.main(["scaffold", str(p)]) == 1 and "already exists" in capsys.readouterr().err
    assert (p / "video_manifest.json").read_text() == first
    assert M.main(["validate", str(p)]) == 1 and "error:" in capsys.readouterr().err


def narrated(m, secs=None, lang="en", voice=None):
    import hashlib
    t = timings(m, secs)
    t["lang"], t["voice"] = lang, voice
    for row, b in zip(t["beats"], m["beats"]):
        row["text_sha"] = hashlib.sha256(b[lang].strip().encode()).hexdigest()
    return t


@pytest.mark.parametrize("callout, ok", [("Look here", True), ("中" * 11, True), ("中" * 12, False), ("c" * 22, True), ("c" * 23, False)])
def test_callout_width_is_limited_in_width_units(tmp_path, callout, ok):
    p, m = project(tmp_path)
    m["beats"][0]["callout"] = callout
    if ok:
        M.validate_showcase(m, p)
    else:
        with pytest.raises(M.ManifestError, match="callout"):
            M.validate_showcase(m, p)


@pytest.mark.parametrize("mutate, needle", [
    (lambda m: m.update(headline="长" * 21), "headline"),
    (lambda m: m.update(subtitle="word " * 40), "subtitle"),
    (lambda m: m["project"].update(name="N" * 30, name_zh="极致小工具工作室工作室"), "project name"),
    (lambda m: m["project"].update(tagline="t" * 70), "tagline"),
    (lambda m: m["project"].update(tagline_zh="长" * 32), "tagline_zh"),
    (lambda m: m["source"].update(label="x" * 70), "source.label"),
    (lambda m: m["beats"][0].update(zh="长" * 46), "'hook'.*zh"),
])
def test_text_that_would_overflow_the_layout_is_refused_before_rendering(tmp_path, mutate, needle):
    p, m = project(tmp_path)
    mutate(m)
    with pytest.raises(M.ManifestError, match=needle):
        M.validate_showcase(m, p)


def test_stale_narration_is_refused(tmp_path):
    p, m = project(tmp_path)
    M.validate_showcase(m, p, narrated(m))
    t = narrated(m)
    m["beats"][1]["en"] = "A different sentence now."
    with pytest.raises(M.ManifestError, match="'problem'.*out of date"):
        M.validate_showcase(m, p, t)


def test_the_manifest_voice_must_match_the_narration(tmp_path):
    p, m = project(tmp_path)
    m["voice"] = "me"
    with pytest.raises(M.ManifestError, match="voice"):
        M.validate_showcase(m, p, narrated(m, voice=None))
    M.validate_showcase(m, p, narrated(m, voice="me"))
    del m["voice"]
    with pytest.raises(M.ManifestError, match="voice"):
        M.validate_showcase(m, p, narrated(m, voice="me"))


def test_scaffold_label_for_a_local_folder_is_the_folder_name_not_the_path():
    b = brief(3)
    b["source"] = {"kind": "local", "url": "/Users/me/code/my-app", "host": "", "repo_path": ""}
    m = M.scaffold_manifest(b, "x", 12)
    assert m["source"]["label"] == "my-app" and "/Users" not in json.dumps(m["source"]["label"])


def test_scaffold_ids_always_end_with_a_call_to_action():
    for n in (10, 16, 40):
        ids = [b["id"] for b in M.scaffold_manifest(brief(3), "x", n)["beats"]]
        assert ids == M.beat_ids(n) and ids[0] == "hook" and ids[-1] == "cta"


@pytest.mark.parametrize("n", range(10, 41))
def test_beat_ids_are_a_hook_numbered_details_proof_and_a_call_to_action(n):
    ids = M.beat_ids(n)
    assert len(ids) == n and len(set(ids)) == n
    assert ids[:3] == ["hook", "problem", "what"] and ids[-2:] == ["proof", "cta"]
    assert ids[3:-2] == [f"detail-{i:02d}" for i in range(1, n - 4)]
    assert all(M.BEAT_ID.match(i) for i in ids)


def test_the_scaffold_defaults_to_sixteen_beats_and_clamps_to_the_allowed_range():
    assert len(M.scaffold_manifest(brief(3), "x")["beats"]) == 16
    assert len(M.scaffold_manifest(brief(3), "x", 3)["beats"]) == M.MIN_BEATS == 10
    assert len(M.scaffold_manifest(brief(3), "x", 99)["beats"]) == M.MAX_BEATS == 40


def test_the_cli_scaffold_writes_sixteen_beats_by_default(tmp_path):
    (tmp_path / "brief.json").write_text(json.dumps(brief(2)))
    assert M.main(["scaffold", str(tmp_path)]) == 0
    assert len(json.loads((tmp_path / "video_manifest.json").read_text())["beats"]) == 16


@pytest.mark.parametrize("n", [10, 40])
def test_the_smallest_and_largest_manifests_validate(tmp_path, n):
    p, m = project(tmp_path, n)
    M.validate_showcase(m, p)
    M.validate_showcase(m, p, timings(m, spread(n, 150.0 if n == 10 else 290.0)))


@pytest.mark.parametrize("n", [9, 41])
def test_one_beat_too_few_or_too_many_is_refused_naming_the_range(tmp_path, n):
    p, m = project(tmp_path, 12)
    beats = m["beats"][:n] if n < 12 else m["beats"] + [{**copy.deepcopy(m["beats"][1]), "id": f"extra-{i}"} for i in range(n - 12)]
    m["beats"] = beats
    with pytest.raises(M.ManifestError, match="10 to 40 beats"):
        M.validate_showcase(m, p)


def test_cli_scaffold_gives_non_ascii_folder_names_distinct_ids(tmp_path):
    ids = []
    for name in ("项目甲", "项目乙"):
        d = tmp_path / name
        d.mkdir()
        (d / "brief.json").write_text(json.dumps(brief(2)))
        assert M.main(["scaffold", str(d)]) == 0
        ids.append(json.loads((d / "video_manifest.json").read_text())["project_id"])
    assert all(i.startswith("showcase-") for i in ids) and ids[0] != ids[1]


def test_odd_image_shapes_get_a_crop_warning(tmp_path):
    p, m = project(tmp_path, shape=(900, 600))
    assert M.crop_warnings(m, p) == []
    p2, m2 = project(tmp_path / "sq", shape=(1000, 1000))
    w = M.crop_warnings(m2, p2)
    assert len(w) == 12 and "cropped" in w[0] and "'hook'" in w[0]


def test_the_device_scaffold_ignores_promo_page_captures():
    base = {"source": {"kind": "website", "url": "https://example.com/", "host": "example.com", "repo_path": ""}}
    brief = {**base, "assets": [{"path": "assets/promo-1@2x.png", "role": "promo-page"},
                                {"path": "assets/capture-a-01-desktop.png"}]}
    beats = M.scaffold_manifest(brief, "demo", 12)["beats"]
    assert {b["asset"] for b in beats} == {"assets/capture-a-01-desktop.png"}
    only_promo = {**base, "assets": [{"path": "assets/promo-1@2x.png", "role": "promo-page"}]}
    with pytest.raises(M.ManifestError, match="no assets"):
        M.scaffold_manifest(only_promo, "demo", 12)


@pytest.mark.parametrize("topic, ok", [
    ("Services", True), ("Our services", True), ("Our services · 服务", True), ("服务", True), ("About us.", True), ("R&D", True),
    ("Q4 results", True), ("A", True), ("", False), (" Services", False), ("Services ", False), ("-Services", False),
    ("Services-", False), ("Our\nservices", False), ("Services 🚀", False), ("<b>Services</b>", False), ("服" * 15, False),
    ("S" * 29, False), ("S" * 28, True), (7, False), (None, False),
])
def test_topic_labels_follow_the_rule_the_renderer_uses(topic, ok):
    assert M.topic_valid(topic) is ok


def test_a_beat_may_carry_a_valid_topic_and_a_bad_one_is_refused_naming_the_beat(tmp_path):
    p, m = project(tmp_path, 12)
    for b in m["beats"]:
        b["topic"] = "Services"
    M.validate_showcase(m, p)
    m["beats"][3]["topic"] = "<b>x</b>"
    with pytest.raises(M.ManifestError, match=r"beat 'detail-01'.*topic"):
        M.validate_showcase(m, p)
