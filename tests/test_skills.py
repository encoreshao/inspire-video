import os
import subprocess
from pathlib import Path

import pytest

import check_skills as C

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIRS = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
GOOD_DESC = "This skill should be used when the user asks to build a demo widget from a spec."


def make_skill(tmp_path, name="demo", desc=GOOD_DESC, body="# Demo\n\nRun `python3 scripts/demo.py`.\n", refs=None,
               frontmatter=True, scripts=("demo.py",)):
    repo = tmp_path / "repo"
    d = repo / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    (repo / "scripts").mkdir(exist_ok=True)
    for s in scripts:
        (repo / "scripts" / s).write_text("")
    for fname, text in (refs or {}).items():
        (d / "references").mkdir(exist_ok=True)
        (d / "references" / fname).write_text(text)
    head = f"---\nname: {name}\ndescription: {desc}\n---\n\n" if frontmatter else ""
    (d / "SKILL.md").write_text(head + body)
    return repo, d


# ---- the repo's own skills -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda p: p.name)
def test_every_skill_in_the_repo_passes_the_checks(skill_dir):
    assert C.check_skill(skill_dir, ROOT) == []


def test_the_whole_repo_passes_the_checks_and_has_both_skills():
    assert C.check_all(ROOT) == []
    assert {"inspire-video", "inspire-showcase"} <= {p.name for p in SKILL_DIRS}


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda p: p.name)
def test_skills_stay_lean(skill_dir):
    # Detail belongs in references/: keep the workflow file small enough to load whenever the skill triggers.
    meta, body = C.split_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    assert len(body.split()) <= 2500, f"{skill_dir.name}: {len(body.split())} words; move detail into references/"
    assert len(meta["description"]) <= 600


def test_the_conventions_are_documented_for_future_skills():
    doc = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")
    for needle in ("This skill should be used when", "scripts/check_skills.py", "references/", "skills/<name>/SKILL.md"):
        assert needle in doc, needle


def test_the_root_pointer_keeps_old_installs_working():
    shim = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert len(shim.split()) <= 150 and "skills/inspire-video/SKILL.md" in shim


# ---- the validator itself --------------------------------------------------------------------------------------------

def test_a_good_skill_passes(tmp_path):
    repo, d = make_skill(tmp_path, refs={"guide.md": "# Guide\n"}, body="# Demo\n\nRead `references/guide.md`. Run `python3 scripts/demo.py`.\n")
    assert C.check_skill(d, repo) == []


@pytest.mark.parametrize("kwargs, needle", [
    ({"frontmatter": False}, "frontmatter"),
    ({"desc": "Builds demo widgets."}, "This skill should be used when"),
    ({"desc": "This skill should be used when " + "x" * 1100}, "1024"),
    ({"body": "# Demo\n\nYou should run `python3 scripts/demo.py`.\n"}, "second person"),
    ({"body": "# Demo\n\nRead `references/missing.md`.\n"}, "references/missing.md"),
    ({"body": "# Demo\n\nRun `python3 scripts/nope.py`.\n"}, "scripts/nope.py"),
    ({"body": "# Demo\n\n" + "word " * 5001}, "5000"),
])
def test_bad_skills_are_reported(tmp_path, kwargs, needle):
    repo, d = make_skill(tmp_path, **kwargs)
    problems = C.check_skill(d, repo)
    assert any(needle in p for p in problems), problems


def test_the_name_must_match_the_folder(tmp_path):
    repo, d = make_skill(tmp_path, name="demo")
    (d / "SKILL.md").write_text((d / "SKILL.md").read_text().replace("name: demo", "name: other"))
    assert any("name" in p and "folder" in p for p in C.check_skill(d, repo))


def test_an_unlisted_reference_file_is_an_orphan(tmp_path):
    repo, d = make_skill(tmp_path, refs={"unused.md": "# x\n"})
    assert any("unused.md" in p and "not mentioned" in p for p in C.check_skill(d, repo))


def test_references_inside_reference_files_are_checked_too(tmp_path):
    repo, d = make_skill(tmp_path, refs={"guide.md": "See `references/ghost.md` and `scripts/ghost.py`.\n"},
                         body="# Demo\n\nRead `references/guide.md`.\n")
    problems = C.check_skill(d, repo)
    assert any("ghost.md" in p for p in problems) and any("ghost.py" in p for p in problems)


def test_a_folder_without_skill_md_is_reported_by_check_all(tmp_path):
    repo, _ = make_skill(tmp_path)
    (repo / "skills" / "empty").mkdir()
    assert any("empty" in p and "SKILL.md" in p for p in C.check_all(repo))


def test_a_root_pointer_must_point_at_a_real_skill(tmp_path):
    repo, _ = make_skill(tmp_path)
    (repo / "SKILL.md").write_text("---\nname: demo\ndescription: " + GOOD_DESC + "\n---\nSee skills/ghost/SKILL.md.\n")
    assert any("pointer" in p for p in C.check_all(repo))
    (repo / "SKILL.md").write_text("---\nname: demo\ndescription: " + GOOD_DESC + "\n---\nSee skills/demo/SKILL.md.\n")
    assert C.check_all(repo) == []


def test_cli_exit_codes(tmp_path, capsys):
    assert C.main([str(ROOT)]) == 0 and "all skills passed" in capsys.readouterr().out
    repo, d = make_skill(tmp_path, desc="Builds widgets.")
    assert C.main([str(repo)]) == 1 and "This skill should be used when" in capsys.readouterr().out


# ---- the installer links every skill ---------------------------------------------------------------------------------

def install(home, *args):
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run(["bash", "scripts/install.sh", "claude", "--no-deps", *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=120)


def test_the_installer_links_every_skill_folder(tmp_path):
    install(tmp_path)
    target = tmp_path / ".claude" / "skills"
    for d in SKILL_DIRS:
        link = target / d.name
        assert link.is_symlink() and link.resolve() == d.resolve(), d.name
    install(tmp_path)                                                   # idempotent
    assert all((target / d.name).is_symlink() for d in SKILL_DIRS)


def test_the_installer_replaces_an_old_root_link(tmp_path):
    target = tmp_path / ".claude" / "skills"
    target.mkdir(parents=True)
    (target / "inspire-video").symlink_to(ROOT)                         # the previous layout linked the repo root
    install(tmp_path)
    assert (target / "inspire-video").resolve() == (ROOT / "skills" / "inspire-video").resolve()


def test_the_installer_never_replaces_a_real_folder(tmp_path):
    target = tmp_path / ".claude" / "skills" / "inspire-showcase"
    target.mkdir(parents=True)
    (target / "mine.txt").write_text("keep")
    r = install(tmp_path)
    assert r.returncode != 0 and "Refusing" in r.stderr and (target / "mine.txt").read_text() == "keep"


def test_second_person_inside_quoted_text_is_not_an_instruction(tmp_path):
    repo, d = make_skill(tmp_path, body='# Demo\n\nIf the site says "confirm you are not a bot", ask for a file. Run `python3 scripts/demo.py`.\n')
    assert C.check_skill(d, repo) == []


def test_uninstall_removes_only_links_into_this_clone(tmp_path):
    install(tmp_path)
    skills = tmp_path / ".claude" / "skills"
    (skills / "old-root-link").symlink_to(ROOT)                          # the previous layout
    other = tmp_path / "elsewhere"
    other.mkdir()
    (skills / "someone-elses").symlink_to(other)                          # must survive
    (skills / "plain-folder").mkdir()                                     # must survive
    env = {**os.environ, "HOME": str(tmp_path)}
    r = subprocess.run(["bash", "scripts/uninstall.sh"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0
    assert [p.name for p in sorted(skills.iterdir())] == ["plain-folder", "someone-elses"]


def test_the_content_extraction_reference_has_a_rubric_for_each_content_type_and_credits_its_source():
    text = (ROOT / "skills" / "inspire-video" / "references" / "content-extraction.md").read_text(encoding="utf-8")
    for row in ("Speech or talk", "Interview or conversation", "Opinion or commentary", "Experience or how-to",
                "Business or finance", "Entertainment or banter"):
        assert f"| {row} |" in text, row
    assert "autoclip" in text
