from showcase import manifest as M


def timings(rows):
    return {"beats": [{"id": i, "audio_seconds": a, "seconds": s} for i, a, s in rows]}


def test_a_beat_held_far_longer_than_its_speech_is_flagged():
    w = M.pacing_warnings({}, timings([("a", 6.0, 6.4), ("b", 3.0, 7.5)]))
    assert len(w) == 1 and "'b'" in w[0] and "7.5" in w[0] and "silence" in w[0]


def test_natural_gaps_are_not_flagged():
    assert M.pacing_warnings({}, timings([("a", 5.0, 5.4), ("b", 4.2, 6.1)])) == []     # up to 2 s of silence is a natural pause


def test_without_narration_there_is_nothing_to_say():
    assert M.pacing_warnings({}, None) == [] and M.pacing_warnings({}, {"beats": []}) == []


def test_a_row_without_an_audio_length_is_skipped():
    assert M.pacing_warnings({}, {"beats": [{"id": "a", "seconds": 9.0}]}) == []
