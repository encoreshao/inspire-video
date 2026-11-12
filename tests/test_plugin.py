"""The repo is also a Claude Code plugin marketplace: /plugin marketplace add encoreshao/inspire-video."""
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
MARKET = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))


def test_the_marketplace_lists_this_repo_as_its_one_plugin():
    assert MARKET["name"] == PLUGIN["name"] == "inspire-video"
    assert [(p["name"], p["source"]) for p in MARKET["plugins"]] == [("inspire-video", "./")]


def test_no_version_is_pinned_so_every_commit_is_an_update():
    # With a version in the manifest, /plugin update does nothing until someone bumps it; without one the commit is used.
    assert "version" not in PLUGIN and all("version" not in p for p in MARKET["plugins"])


def test_the_skills_do_not_assume_one_install_folder():
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        assert "scripts/prepare.sh" in text and "two levels above" in text, skill.parent.name


def test_both_readmes_show_the_plugin_install():
    for name in ("README.md", "README.zh-CN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "/plugin marketplace add encoreshao/inspire-video" in text, name
        assert "/plugin install inspire-video@inspire-video" in text and "CLAUDE_CONFIG_DIR" in text, name


def copy_engine(dest):
    (dest / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "prepare.sh", dest / "scripts" / "prepare.sh")
    return dest


def prepare(engine, home, **extra):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR", "INSPIRE_VIDEO_HOME")}
    return subprocess.run(["bash", str(engine / "scripts" / "prepare.sh"), "--no-deps"],
                          env={**env, "HOME": str(home), **extra}, capture_output=True, text=True, timeout=60)


def test_a_plugin_copy_keeps_outputs_and_voices_in_the_data_folder(tmp_path):
    engine = copy_engine(tmp_path / ".claude-loopx" / "plugins" / "cache" / "inspire-video" / "inspire-video" / "abc123")
    (engine / "output" / "final").mkdir(parents=True)
    (engine / "output" / "final" / ".gitkeep").write_text("")
    data = tmp_path / ".inspire-video"
    (data / "output" / "final" / "old").mkdir(parents=True)
    (data / "output" / "final" / "old" / "old.mp4").write_text("kept")
    r = prepare(engine, tmp_path)
    assert r.returncode == 0, r.stderr
    for name in ("output", "voices"):
        assert (engine / name).is_symlink() and (engine / name).resolve() == (data / name).resolve()
    assert (engine / "output" / "final" / "old" / "old.mp4").read_text() == "kept"
    assert (data / "output" / "projects").is_dir() and str(data.resolve()) in r.stdout
    assert prepare(engine, tmp_path).returncode == 0                      # running it again changes nothing

    newer = copy_engine(engine.parent / "def456")                         # a plugin update is a new folder
    (engine / "output" / "final" / "made.mp4").write_text("video")
    assert prepare(newer, tmp_path).returncode == 0
    assert (newer / "output" / "final" / "made.mp4").read_text() == "video"


def test_files_already_written_into_a_plugin_copy_are_moved_not_lost(tmp_path):
    engine = copy_engine(tmp_path / "plugins" / "cache" / "m" / "p" / "v1")
    (engine / "output" / "projects" / "talk").mkdir(parents=True)
    (engine / "output" / "projects" / "talk" / "props.json").write_text("{}")
    assert prepare(engine, tmp_path).returncode == 0
    assert (tmp_path / ".inspire-video" / "output" / "projects" / "talk" / "props.json").read_text() == "{}"


def test_a_clone_keeps_its_own_output_folder(tmp_path):
    engine = copy_engine(tmp_path / "clone")
    r = prepare(engine, tmp_path)
    assert r.returncode == 0 and not (engine / "output").is_symlink() and (engine / "output" / "final").is_dir()
    assert not (tmp_path / ".inspire-video").exists()


def test_the_data_folder_can_be_moved(tmp_path):
    engine = copy_engine(tmp_path / "plugins" / "cache" / "m" / "p" / "v1")
    assert prepare(engine, tmp_path, INSPIRE_VIDEO_HOME=str(tmp_path / "elsewhere")).returncode == 0
    assert (engine / "output").resolve() == (tmp_path / "elsewhere" / "output").resolve()
