import pytest

from showcase import timing


def test_wav_seconds(tmp_path, make_wav):
    assert timing.wav_seconds(make_wav(tmp_path / "a.wav", seconds=5.0)) == 5.0
    assert timing.wav_seconds(make_wav(tmp_path / "b.wav", seconds=2.5, rate=24000)) == 2.5


def test_beat_seconds_adds_the_pad():
    assert timing.beat_seconds(3.0) == 3.4
    assert timing.PAD == 0.4


def test_check_total_accepts_the_allowed_range():
    assert timing.check_total([60.0, 65.4]) == 125.4
    assert timing.check_total([timing.MIN_TOTAL]) == timing.MIN_TOTAL
    assert timing.check_total([timing.MAX_TOTAL]) == timing.MAX_TOTAL


def test_the_allowed_range_is_two_to_five_minutes():
    assert (timing.MIN_TOTAL, timing.MAX_TOTAL) == (120.0, 300.0)


def test_just_outside_the_range_is_refused():
    with pytest.raises(timing.LengthError, match="longer"):
        timing.check_total([timing.MIN_TOTAL - 0.1])
    with pytest.raises(timing.LengthError, match="shorten"):
        timing.check_total([timing.MAX_TOTAL + 0.1])


def test_too_long_asks_to_shorten():
    with pytest.raises(timing.LengthError, match="shorten"):
        timing.check_total([160.0, 160.0])


def test_too_short_asks_to_lengthen():
    with pytest.raises(timing.LengthError, match="longer"):
        timing.check_total([50.0, 50.0])


def test_no_beats_is_an_error():
    with pytest.raises(timing.LengthError, match="no beats"):
        timing.check_total([])


def test_limits_can_be_overridden():
    assert timing.check_total([1.0, 2.0], lo=1.0, hi=5.0) == 3.0


def test_cache_key_is_stable_and_sensitive_to_every_field():
    base = ("你好 hello", "zh", "voice1", "cosyvoice", 1.0, "v1")
    k = timing.cache_key(*base)
    assert k == timing.cache_key(*base)
    assert len(k) == 64
    for i, other in enumerate(["你好 hello!", "en", "voice2", "kokoro", 1.1, "v2"]):
        changed = list(base)
        changed[i] = other
        assert timing.cache_key(*changed) != k, f"field {i} not part of the key"


def test_a_pause_is_between_four_tenths_and_a_second_and_grows_with_the_line():
    short, long_ = timing.pause_after(2.5), timing.pause_after(7.0)
    assert short == timing.PAUSE_MIN == 0.4 and long_ == 0.7
    mid = [timing.pause_after(a) for a in (3.0, 4.0, 5.0, 6.0, 6.5)]
    assert mid == sorted(mid) and all(0.4 <= p <= 0.7 for p in mid)        # monotonic, and inside the no-topic-change range


def test_a_change_of_topic_adds_a_longer_pause_capped_at_one_second():
    assert timing.pause_after(2.5, topic_change=True) == 0.7
    assert timing.pause_after(4.5, topic_change=True) == pytest.approx(timing.pause_after(4.5) + 0.3)
    assert timing.pause_after(7.0, topic_change=True) == timing.PAUSE_MAX == 1.0
    assert timing.pause_after(30.0, topic_change=True) == 1.0


def test_beat_seconds_takes_the_pause_it_is_given():
    assert timing.beat_seconds(3.0, 0.9) == 3.9
    assert timing.beat_seconds(3.0) == 3.4          # the old fixed pad is the default


def test_a_topic_break_follows_the_rule_the_transitions_use():
    # the topics differ when either beat names one; otherwise the capture differs (a title card has no capture)
    assert timing.topic_break({"topic": "A"}, {"topic": "B"}) and not timing.topic_break({"topic": "A"}, {"topic": "A"})
    assert timing.topic_break({"topic": "A"}, {}) and timing.topic_break({}, {"topic": "A"})
    assert timing.topic_break({"asset": "x.png"}, {"asset": "y.png"}) and not timing.topic_break({"asset": "x.png"}, {"asset": "x.png"})
    assert timing.topic_break({"shot": "statement"}, {"asset": "y.png"})
    assert not timing.topic_break({"asset": "x.png"}, {"asset": "x.png", "target": "card-1"})
