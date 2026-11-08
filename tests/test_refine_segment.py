import json

import pytest

import refine_segment as R

# Ten 10-second sentences back to back (0-100 s), then a 30 s silence, then three more (130-160 s).
CUES = [R.Cue(i * 10.0, i * 10.0 + 9.5, f"Sentence {i}.") for i in range(10)] + \
       [R.Cue(130.0 + i * 10.0, 139.5 + i * 10.0, f"Late {i}.") for i in range(3)]


def refine(start, end, cues=CUES, **kw):
    return R.refine(start, end, cues, **kw)


def test_boundaries_snap_to_the_nearest_cue_edges():
    r = refine(10.8, 60.2)           # 10.8 is near the start of cue 1 (10.0); 60.2 near the end of cue 5 (59.5)
    assert (r.start, r.end) == (10.0, 59.5)
    assert any("snapped start" in a for a in r.actions) and any("snapped end" in a for a in r.actions)


def test_an_already_aligned_range_is_left_alone():
    r = refine(10.0, 59.5)
    assert (r.start, r.end, r.actions) == (10.0, 59.5, [])


def test_a_range_far_from_any_edge_moves_to_the_cue_that_contains_it():
    r = R.refine(14.0, 80.0, [R.Cue(0, 30, "A."), R.Cue(30, 100, "B.")], snap_window=2.0)
    assert r.start == 0 and r.end == 100


def test_a_short_range_is_extended_forward_to_the_minimum():
    r = refine(0.0, 20.0)
    assert r.end >= 40.0 and r.duration >= 40.0 and any("extended end" in a for a in r.actions)


def test_extension_does_not_cross_a_long_silence():
    # 100-130 is silent: a range ending at 99.5 cannot grow forward, so it grows backward instead.
    r = refine(70.0, 99.5)
    assert r.end == 99.5 and r.start <= 59.5 and r.duration >= 40.0


def test_a_range_that_cannot_reach_the_minimum_is_an_error():
    with pytest.raises(R.RefineError, match="40"):
        R.refine(0.0, 5.0, [R.Cue(0.0, 9.5, "Only.")])


def test_a_long_range_is_trimmed_back_to_the_maximum_on_a_cue_edge():
    cues = [R.Cue(i * 10.0, i * 10.0 + 9.5, f"S{i}.") for i in range(20)]
    r = R.refine(0.0, 199.5, cues)
    assert r.duration <= 150.0 and r.end in {c.end for c in cues} and any("trimmed end" in a for a in r.actions)


def test_a_single_cue_longer_than_the_maximum_is_an_error():
    with pytest.raises(R.RefineError, match="150"):
        R.refine(0.0, 200.0, [R.Cue(0.0, 200.0, "Very long.")])


def test_a_range_ending_mid_sentence_is_warned_about():
    cues = [R.Cue(0, 30, "A full sentence."), R.Cue(30, 60, "and then it goes on")]
    r = R.refine(0.0, 60.0, cues)
    assert any("sentence" in w for w in r.warnings)
    assert refine(0.0, 49.5).warnings == []


def test_bad_input_is_rejected():
    with pytest.raises(R.RefineError, match="end"):
        refine(50.0, 10.0)
    with pytest.raises(R.RefineError, match="no cues"):
        R.refine(0.0, 50.0, [])


def test_load_cues_reads_the_transcript_and_skips_broken_segments(tmp_path):
    (tmp_path / "transcript.json").write_text(json.dumps({"segments": [
        {"start": 5, "end": 8, "text": " Hello. "}, {"start": 1, "end": 4, "text": "First."},
        {"start": "x", "end": 9, "text": "bad"}, {"start": 9, "end": 9, "text": "empty"}]}))
    cues = R.load_cues(tmp_path / "transcript.json")
    assert [(c.start, c.text) for c in cues] == [(1.0, "First."), (5.0, "Hello.")]


def test_cli_prints_a_report_and_can_write_it(tmp_path, capsys):
    (tmp_path / "transcript.json").write_text(json.dumps({"segments": [
        {"start": i * 10.0, "end": i * 10.0 + 9.5, "text": f"S{i}."} for i in range(10)]}))
    assert R.main([str(tmp_path), "--start", "10.8", "--end", "60.2", "--write"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["start"] == 10.0 and out["end"] == 59.5 and out["duration"] == 49.5
    assert json.loads((tmp_path / "segment_report.json").read_text())["end"] == 59.5
    assert R.main([str(tmp_path), "--start", "50", "--end", "10"]) == 1
    assert R.main([str(tmp_path / "nope"), "--start", "0", "--end", "50"]) == 1
