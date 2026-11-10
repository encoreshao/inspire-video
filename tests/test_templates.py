import json
from collections import Counter

import pytest
import yaml

from showcase import templates as T


def good(**over):
    base = {"id": "demo", "name": "Demo", "description": "A demo recipe.", "style": "promo",
            "shots": [{"id": "hero-push", "weight": 3}, {"id": "spotlight-focus", "weight": 3},
                      {"id": "crash-zoom-punch", "weight": 1, "max": 1}, {"id": "statement", "weight": 1}]}
    base.update(over)
    return base


def test_a_good_template_is_normalised():
    t = T.validate_template(good(theme="ink", opening="statement"), "demo")
    assert t["id"] == "demo" and t["theme"] == "ink" and t["opening"] == "statement" and t["closing"] is None
    assert t["transition"] == "dissolve" and t["name_zh"] is None and t["pacing"] is None
    assert t["shots"][0] == {"id": "hero-push", "weight": 3, "max": None}


@pytest.mark.parametrize("over,needle", [
    ({"id": "other"}, "file name"),
    ({"id": "Demo"}, "id"),
    ({"style": "device"}, "style"),
    ({"theme": "neon"}, "theme"),
    ({"name": ""}, "name"),
    ({"extra": 1}, "extra"),
    ({"shots": []}, "shots"),
    ({"shots": [{"id": "hero-push", "weight": 1}, {"id": "hero-push", "weight": 1}, {"id": "spotlight-focus", "weight": 1}]}, "twice"),
    ({"shots": [{"id": "nope", "weight": 1}, {"id": "hero-push", "weight": 1}, {"id": "spotlight-focus", "weight": 1}]}, "nope"),
    ({"shots": [{"id": "hero-push", "weight": 0}, {"id": "spotlight-focus", "weight": 1}, {"id": "statement", "weight": 1}]}, "weight"),
    ({"shots": [{"id": "hero-push", "weight": 1.5}, {"id": "spotlight-focus", "weight": 1}, {"id": "statement", "weight": 1}]}, "weight"),
    ({"shots": [{"id": "hero-push", "weight": 1}, {"id": "spotlight-focus", "weight": 1}, {"id": "statement", "weight": 1, "max": 3}]}, "max"),
    ({"shots": [{"id": "hero-push", "weight": 1, "max": 0}, {"id": "spotlight-focus", "weight": 1}, {"id": "statement", "weight": 1}]}, "max"),
    ({"shots": [{"id": "hero-push", "weight": 1}, {"id": "statement", "weight": 1}, {"id": "crash-zoom-punch", "weight": 1}]}, "unlimited"),
    ({"shots": [{"id": "hero-push", "weight": 1}, {"id": "spotlight-focus", "weight": 1}]}, "three"),
    ({"opening": "pan-reveal"}, "opening"),
    ({"opening": "crash-zoom-punch", "closing": "crash-zoom-punch"}, "closing"),
    ({"transition": "wipe"}, "transition"),
    ({"pacing": {"beat_seconds": [12, 8]}}, "beat_seconds"),
    ({"pacing": {"beat_seconds": [2, 8]}}, "beat_seconds"),
])
def test_a_bad_template_is_rejected_with_a_clear_message(over, needle):
    with pytest.raises(T.TemplateError, match=needle):
        T.validate_template(good(**over), "demo")


def test_a_template_that_is_not_a_mapping_is_rejected():
    with pytest.raises(T.TemplateError, match="mapping"):
        T.validate_template(["x"], "demo")


def write(directory, name, data):
    (directory / f"{name}.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")


def test_load_templates_sorts_by_id_and_names_the_broken_file(tmp_path):
    write(tmp_path, "zeta", good(id="zeta"))
    write(tmp_path, "alpha", good(id="alpha"))
    assert list(T.load_templates(tmp_path)) == ["alpha", "zeta"]
    write(tmp_path, "broken", good(id="broken", style="device"))
    with pytest.raises(T.TemplateError, match="broken.yaml"):
        T.load_templates(tmp_path)


def test_a_missing_or_empty_directory_is_an_empty_catalogue(tmp_path):
    assert T.load_templates(tmp_path / "nope") == {} and T.catalogue(tmp_path) == []


def test_yaml_that_executes_nothing_and_a_bad_file_is_a_template_error(tmp_path):
    (tmp_path / "evil.yaml").write_text("id: !!python/object/apply:os.system ['true']\n", encoding="utf-8")
    with pytest.raises(T.TemplateError, match="evil.yaml"):
        T.load_templates(tmp_path)


@pytest.mark.parametrize("bad", ["../etc/passwd", "CINEMATIC", "", None, 3, "nope"])
def test_an_unknown_or_hostile_id_lists_the_valid_ones(tmp_path, bad):
    write(tmp_path, "alpha", good(id="alpha"))
    with pytest.raises(T.TemplateError, match="alpha"):
        T.get_template(bad, tmp_path)


@pytest.mark.parametrize("n", [10, 16, 25, 40])
def test_suggested_shots_respect_the_limits_and_never_repeat_back_to_back(n):
    t = T.validate_template(good(opening="statement", closing="statement"), "demo")
    seq = T.suggest_shots(t, n)
    assert len(seq) == n and seq[0] == "statement" and seq[-1] == "statement"
    assert all(a != b for a, b in zip(seq, seq[1:]))
    counts = Counter(seq)
    assert counts["crash-zoom-punch"] <= 1 and counts["statement"] <= 2


def test_suggestions_follow_the_weights_and_are_deterministic():
    t = T.validate_template(good(), "demo")
    assert T.suggest_shots(t, 20) == T.suggest_shots(t, 20)
    counts = Counter(T.suggest_shots(t, 40))
    assert counts["hero-push"] >= 10 and counts["spotlight-focus"] >= 10


def test_the_shipped_templates_are_valid_and_the_default_exists():
    loaded = T.load_templates()
    assert T.DEFAULT_TEMPLATE in loaded and len(loaded) >= 3
    for t in loaded.values():
        for n in (10, 16, 40):
            seq = T.suggest_shots(t, n)
            assert all(a != b for a, b in zip(seq, seq[1:])) and len(seq) == n


def test_the_catalogue_is_plain_json_data(tmp_path):
    write(tmp_path, "alpha", good(id="alpha", name_zh="甲"))
    (tmp_path / "covers").mkdir()
    (tmp_path / "covers" / "alpha.png").write_bytes(b"x")
    [row] = T.catalogue(tmp_path)
    assert row["id"] == "alpha" and row["name_zh"] == "甲" and row["cover"] == "templates/covers/alpha.png"
    assert [s["id"] for s in row["shots"]][:2] == ["hero-push", "spotlight-focus"]
    json.dumps(row)


def test_cli_list_json_prints_only_json_on_stdout(capsys):
    assert T.main(["list", "--json"]) == 0
    out = capsys.readouterr()
    assert {r["id"] for r in json.loads(out.out)} >= {T.DEFAULT_TEMPLATE}


def test_cli_show_validate_and_unknown_id(capsys):
    assert T.main(["show", T.DEFAULT_TEMPLATE, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == T.DEFAULT_TEMPLATE
    assert T.main(["validate"]) == 0 and "valid" in capsys.readouterr().out
    assert T.main(["show", "nope"]) == 1 and "error:" in capsys.readouterr().err


def test_a_closing_on_an_unlimited_shot_needs_a_third_unlimited_shot():
    # With only two unlimited shots and the rest used up, the closing could not be placed for some video lengths.
    shots = [{"id": "hero-push", "weight": 3}, {"id": "spotlight-focus", "weight": 8},
             {"id": "crash-zoom-punch", "weight": 6, "max": 1}]
    with pytest.raises(T.TemplateError, match="closing"):
        T.validate_template(good(shots=shots, closing="hero-push"), "demo")
    with pytest.raises(T.TemplateError, match="opening"):
        T.validate_template(good(shots=shots, opening="spotlight-focus"), "demo")


def test_every_valid_random_template_can_always_be_scaffolded():
    import random
    rng = random.Random(7)
    ids = list(T.PROMO_SHOTS)
    tried = 0
    for _ in range(600):
        picked = rng.sample(ids, rng.randint(3, len(ids)))
        shots = [{"id": s, "weight": rng.randint(1, 9), **({"max": rng.randint(1, 2)} if rng.random() < 0.4 else {})} for s in picked]
        try:
            t = T.validate_template(good(shots=shots, opening=rng.choice([None, *picked]), closing=rng.choice([None, *picked])), "demo")
        except T.TemplateError:
            continue
        tried += 1
        for n in range(10, 41):
            seq = T.suggest_shots(t, n)
            assert len(seq) == n and all(a != b for a, b in zip(seq, seq[1:])), (shots, t["opening"], t["closing"], n)
    assert tried > 20


@pytest.mark.parametrize("text", ["id: demo\nname: D\ndescription: d\nstyle: promo\nshots: [{id: [hero-push], weight: 1}]\n",
                                  "id: demo\nname: D\ndescription: d\nstyle: promo\nopening: [hero-push]\nshots: []\n",
                                  "1: x\nfoo: y\n"])
def test_a_malformed_template_file_is_an_error_that_names_the_file_not_a_traceback(tmp_path, text):
    (tmp_path / "demo.yaml").write_text(text, encoding="utf-8")
    with pytest.raises(T.TemplateError, match="demo.yaml"):
        T.load_templates(tmp_path)


def test_a_template_file_that_is_not_utf8_names_the_file(tmp_path):
    (tmp_path / "demo.yaml").write_bytes(b"id: \xff\xfe\n")
    with pytest.raises(T.TemplateError, match="demo.yaml"):
        T.load_templates(tmp_path)


def test_the_transition_names_are_the_javascript_ones():
    import shutil
    import subprocess
    from pathlib import Path
    if shutil.which("node") is None:
        pytest.skip("node is not installed")
    root = Path(__file__).resolve().parent.parent
    code = "import('./video/src/showcase/transitions.mjs').then((m) => console.log(JSON.stringify(m.TRANSITIONS)))"
    r = subprocess.run(["node", "-e", code], cwd=root, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert tuple(json.loads(r.stdout)) == T.TRANSITIONS


def test_the_shipped_recipes_use_the_named_transitions_where_they_fit():
    loaded = T.load_templates()
    assert loaded["punchy"]["transition"] == "flash-cut" and loaded["tour"]["transition"] == "whip-pan"
    assert loaded["cinematic"]["transition"] == "dissolve" and loaded["calm"]["transition"] == "dissolve"
    assert T.validate_template(good(transition="whip-pan"), "demo")["transition"] == "whip-pan"
