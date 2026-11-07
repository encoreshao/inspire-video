import json
import sys
from pathlib import Path

import pytest

import platforms
import publish_meta

LEGACY = {
    "wechat_channels": {"short_title": "先行动再自信吧", "description": "先开始，信心随后到来。", "hashtags": ["自信", "行动"]},
    "douyin": {"title": "先行动，再自信", "description": "行动先于信心。", "hashtags": ["自信"]},
    "credit": "内容来源：测试。",
}
NEW = {
    "platforms": {
        "douyin": {"title": "先行动，再自信", "description": "行动先于信心。", "hashtags": ["自信"]},
        "linkedin": {"title": "Act first, feel confident", "description": "Confidence follows action.",
                     "hashtags": ["Confidence", "Growth"]},
    },
    "credit": "内容来源：测试。",
    "credit_en": "Source: test. Subtitles are my own translation.",
}


@pytest.fixture
def run(tmp_path, monkeypatch, capsys):
    """Run publish_meta.main() on a throwaway project; returns (exit code, output dir, captured stderr)."""
    monkeypatch.setattr(publish_meta, "ROOT", tmp_path)
    proj = tmp_path / "output/projects/demo"
    proj.mkdir(parents=True)
    (proj / "video_manifest.json").write_text(json.dumps({
        "project_id": "demo", "copy": {"headline_zh": "先行动，再自信"},
        "provenance": {"review_status": "approved", "source_reference": "https://example.com/v"}}))
    out = tmp_path / "output/final/demo"

    def go(publish, *flags, files=()):
        (proj / "publish.json").write_text(json.dumps(publish, ensure_ascii=False))
        out.mkdir(parents=True, exist_ok=True)
        for name in files:
            (out / name).write_bytes(b"x")
        monkeypatch.setattr(sys, "argv", ["publish_meta.py", str(proj), *flags])
        rc = publish_meta.main()
        return rc, out, capsys.readouterr().err

    go.proj = proj
    return go


def test_a_legacy_publish_json_writes_the_same_files_as_before(run):
    rc, out, _ = run(LEGACY)
    assert rc == 0
    assert (out / "publish_wechat.txt").read_text() == "先行动再自信吧\n\n先开始，信心随后到来。\n\n内容来源：测试。\n\n#自信 #行动\n"
    assert (out / "publish_douyin.txt").read_text() == "先行动，再自信\n\n行动先于信心。\n\n内容来源：测试。\n\n#自信\n"
    project = json.loads((out / "project.json").read_text())
    project.pop("created_at")
    assert project == {
        "schema": 1, "slug": "demo", "title": "先行动，再自信", "source_url": "https://example.com/v",
        "video": "demo.mp4", "cover": None,
        "publish": {
            "wechat": {"title": "先行动再自信吧", "caption": "先开始，信心随后到来。\n\n内容来源：测试。", "hashtags": ["自信", "行动"]},
            "douyin": {"title": "先行动，再自信", "caption": "行动先于信心。\n\n内容来源：测试。", "hashtags": ["自信"]}}}
    md = (out / "publish.md").read_text()
    assert "微信视频号" in md and "抖音" in md and "先行动再自信吧" in md


def test_a_legacy_file_with_only_one_platform_works(run):
    only_douyin = {"douyin": LEGACY["douyin"], "credit": LEGACY["credit"]}
    rc, out, err = run(only_douyin)
    assert rc == 0, err
    assert (out / "publish_douyin.txt").exists() and not (out / "publish_wechat.txt").exists()
    assert list(json.loads((out / "project.json").read_text())["publish"]) == ["douyin"]


def test_english_platforms_use_the_english_credit_and_list_their_video(run):
    rc, out, err = run(NEW, files=["demo-portrait-4x5.mp4"])
    assert rc == 0, err
    assert (out / "publish_linkedin.txt").read_text() == (
        "Act first, feel confident\n\nConfidence follows action.\n\n"
        "Source: test. Subtitles are my own translation.\n\n#Confidence #Growth\n")
    assert "内容来源：测试。" in (out / "publish_douyin.txt").read_text()
    project = json.loads((out / "project.json").read_text())
    assert project["publish"]["linkedin"]["caption"].endswith("Source: test. Subtitles are my own translation.")
    assert project["videos"] == {"portrait-4x5": "demo-portrait-4x5.mp4"}
    assert project["covers"] == {}
    assert "## LinkedIn" in (out / "publish.md").read_text()


def test_an_english_platform_without_credit_en_is_rejected(run):
    bad = {**NEW}
    bad.pop("credit_en")
    rc, _, err = run(bad)
    assert rc == 1 and "linkedin" in err and "credit_en" in err


def test_an_unknown_platform_id_lists_the_known_ones(run):
    rc, _, err = run({"platforms": {"tiktok": {"title": "t", "description": "d", "hashtags": []}}, "credit": "c"})
    assert rc == 1 and "unknown platform 'tiktok'" in err and "douyin" in err and "linkedin" in err


def test_an_empty_platform_list_is_rejected(run):
    rc, _, err = run({"platforms": {}, "credit": "c"})
    assert rc == 1 and "platforms is empty" in err


def test_limits_come_from_the_registry():
    reg = platforms.load()
    ok = {"title": "先行动再自信吧", "description": "描述", "hashtags": ["自信"]}

    def errs(platform, **change):
        p = {"platforms": {platform: {**ok, **change}}, "credit": "来源", "credit_en": "Source"}
        return publish_meta.validate(p, reg)

    assert errs("wechat_channels") == []
    assert any("short_title" in e and "6-16" in e for e in errs("wechat_channels", title="短"))
    assert any("title" in e and "30" in e for e in errs("douyin", title="长" * 31))
    assert any("hashtags" in e for e in errs("douyin", hashtags=["a"] * 6))
    assert any("'#bad'" in e or "bad tag" in e for e in errs("douyin", hashtags=["bad tag"]))
    assert any("description" in e and "1000" in e for e in errs("douyin", description="长" * 1000))
    assert any("description is empty" in e for e in errs("douyin", description=""))
    assert errs("rednote", hashtags=["a"] * 10) == []
    assert any("hashtags" in e for e in errs("rednote", hashtags=["a"] * 11))


def test_init_drafts_each_requested_platform_and_never_overwrites(run, monkeypatch, capsys):
    proj = run.proj
    (proj / "copy.json").write_text(json.dumps({
        "headline_zh": "先行动，再自信，让信心随行动而来", "subtitle_en": "Act First, Then Feel Confident",
        "quote_zh": "那份不安全感就会减轻一点。", "quote_en": "It removes a little bit of the insecurity.",
        "speaker_name": "Ada", "source_name": "TED", "talk_title": "On Doing", "year": 2020}, ensure_ascii=False))
    monkey_argv = ["publish_meta.py", str(proj), "--init", "--platform", "wechat_channels,linkedin"]
    monkeypatch.setattr(sys, "argv", monkey_argv)
    assert publish_meta.main() == 0
    draft = json.loads((proj / "publish.json").read_text())
    assert list(draft["platforms"]) == ["wechat_channels", "linkedin"]
    assert len(draft["platforms"]["wechat_channels"]["title"]) <= 16
    assert draft["platforms"]["linkedin"]["title"] == "Act First, Then Feel Confident"
    assert draft["platforms"]["linkedin"]["description"] == "It removes a little bit of the insecurity."
    assert "TED" in draft["credit"] and "TED" in draft["credit_en"] and "Ada" in draft["credit_en"]
    with pytest.raises(SystemExit):
        publish_meta.main()          # publish.json exists now


def test_a_block_without_hashtags_still_publishes(run):
    block = {"title": "先行动，再自信", "description": "行动先于信心。"}
    rc, out, err = run({"platforms": {"douyin": block}, "credit": "内容来源：测试。"})
    assert rc == 0, err
    assert (out / "publish_douyin.txt").read_text() == "先行动，再自信\n\n行动先于信心。\n\n内容来源：测试。\n\n\n"
    assert json.loads((out / "project.json").read_text())["publish"]["douyin"]["hashtags"] == []


def test_init_with_an_unknown_platform_exits_1_and_writes_nothing(run):
    proj = run.proj
    (proj / "copy.json").write_text(json.dumps({"headline_zh": "x"}))
    rc, _, err = run_init(run, "tiktok")
    assert rc == 1 and "unknown platform 'tiktok'" in err and "douyin" in err
    assert not (proj / "publish.json").exists()


def run_init(run, ids):
    return run_init_impl(run.proj, ids)


def run_init_impl(proj, ids):
    import io, contextlib
    old = sys.argv
    sys.argv = ["publish_meta.py", str(proj), "--init", "--platform", ids]
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            rc = publish_meta.main()
    finally:
        sys.argv = old
    return rc, None, err.getvalue()


def test_publish_md_warns_for_the_unverified_platforms(run):
    rc, out, err = run(NEW)
    assert rc == 0, err
    md = (out / "publish.md").read_text()
    assert "unverified for:" in md
    reg = platforms.load()
    sentence = md.split("unverified for:")[1]
    assert reg.platform("douyin").name in sentence and reg.platform("linkedin").name in sentence


def _registry_with_verified(tmp_path, monkeypatch, verified_ids):
    import yaml
    raw = yaml.safe_load(platforms.DEFAULT_PATH.read_text(encoding="utf-8"))
    for pid, blk in raw["platforms"].items():
        blk["verified"] = pid in verified_ids
    path = tmp_path / "platforms.yaml"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    monkeypatch.setattr(platforms, "DEFAULT_PATH", path)


def test_a_verified_platform_is_left_out_of_the_warning(run, tmp_path, monkeypatch):
    _registry_with_verified(tmp_path, monkeypatch, {"douyin"})
    rc, out, err = run(NEW)
    assert rc == 0, err
    sentence = (out / "publish.md").read_text().split("unverified for:")[1]
    reg = platforms.load()
    assert reg.platform("linkedin").name in sentence and reg.platform("douyin").name not in sentence


def test_no_warning_when_every_listed_platform_is_verified(run, tmp_path, monkeypatch):
    _registry_with_verified(tmp_path, monkeypatch, {"douyin", "linkedin"})
    rc, out, err = run(NEW)
    assert rc == 0, err
    assert "unverified" not in (out / "publish.md").read_text()


def test_publish_md_names_each_platforms_own_video_and_cover(run):
    rc, out, err = run(NEW)
    assert rc == 0, err
    md = (out / "publish.md").read_text()
    douyin, linkedin = md.split("## 抖音")[1].split("## LinkedIn")
    assert "output/final/demo/demo.mp4" in douyin and "output/final/demo/cover.png" in douyin
    assert "demo-portrait-4x5" not in douyin
    assert "output/final/demo/demo-portrait-4x5.mp4" in linkedin and "output/final/demo/cover-portrait-4x5.png" in linkedin
    assert md.index("## 抖音") == md.index("Video:") - len("## 抖音\n\n")   # no header line before the first section
