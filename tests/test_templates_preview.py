import json

import pytest

from showcase import manifest as M
from showcase import templates as T


def sample(tid, tmp_path):
    p = tmp_path / "proj"
    T.build_sample_project(T.get_template(tid), p)
    return p, json.loads((p / "video_manifest.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("tid", sorted(T.load_templates()))
def test_the_sample_project_of_every_template_validates_and_uses_its_palette(tmp_path, tid):
    t = T.get_template(tid)
    p, m = sample(tid, tmp_path)
    M.validate_showcase(m, p)
    shots = [b["shot"] for b in m["beats"]]
    assert set(shots) == {s["id"] for s in t["shots"]}
    assert all(a != b for a, b in zip(shots, shots[1:]))
    if t["opening"]:
        assert shots[0] == t["opening"]
    if t["closing"]:
        assert shots[-1] == t["closing"]
    assert m["template"] == tid and m["style"] == "promo" and m["sample"] is True and m["project_id"] == f"preview-{tid}"
    assert sum(m["sample_seconds"]) < 60 and len(m["sample_seconds"]) == len(m["beats"])
    assert M.template_warnings(m) == []


def test_sample_mode_only_relaxes_the_beat_count_and_the_total_length(tmp_path):
    p, m = sample("cinematic", tmp_path)
    plain = {k: v for k, v in m.items() if k not in ("sample", "sample_seconds")}
    with pytest.raises(M.ManifestError, match="beats"):
        M.validate_showcase(plain, p)
    short = {**m, "sample_seconds": [1.0] * len(m["beats"])}
    with pytest.raises(M.ManifestError, match="needs at least"):
        M.validate_showcase(short, p)
    with pytest.raises(M.ManifestError, match="sample_seconds"):
        M.validate_showcase({**m, "sample_seconds": [5.0]}, p)
    with pytest.raises(M.ManifestError, match="rights"):
        M.validate_showcase({**m, "provenance": {"rights_confirmed": False, "source_reference": "x"}}, p)


def test_sample_seconds_set_the_beat_lengths_only_in_sample_mode(tmp_path):
    p, m = sample("minimal", tmp_path)
    assert M.beat_seconds_list(m) == [float(x) for x in m["sample_seconds"]]
    plain = {k: v for k, v in m.items() if k not in ("sample",)}
    assert M.beat_seconds_list(plain) != [float(x) for x in m["sample_seconds"]]


def test_preview_of_an_unknown_template_is_a_clear_error(capsys):
    assert T.main(["preview", "nope"]) == 1 and "error:" in capsys.readouterr().err


def test_the_catalogue_lists_a_preview_clip_when_one_exists(tmp_path):
    import yaml
    (tmp_path / "alpha.yaml").write_text(yaml.safe_dump({"id": "alpha", "name": "A", "description": "d", "style": "promo", "shots": [
        {"id": "hero-push", "weight": 1}, {"id": "spotlight-focus", "weight": 1}, {"id": "statement", "weight": 1}]}), encoding="utf-8")
    assert T.catalogue(tmp_path)[0]["preview"] is None
    (tmp_path / "covers").mkdir()
    (tmp_path / "covers" / "alpha.mp4").write_bytes(b"x")
    assert T.catalogue(tmp_path)[0]["preview"] == "templates/covers/alpha.mp4"
