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
