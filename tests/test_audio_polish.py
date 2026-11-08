import array
import math
import wave

from showcase import audio_polish as ap

RATE = 24000


def tone(seconds, amp, freq=200):
    return array.array("h", [int(amp * math.sin(2 * math.pi * freq * i / RATE)) for i in range(int(RATE * seconds))])


def clip(lead, body, tail):
    return array.array("h", bytes(2 * int(RATE * lead))) + body + array.array("h", bytes(2 * int(RATE * tail)))


def rms_db(s):
    return 20 * math.log10(math.sqrt(sum(x * x for x in s) / len(s)) / 32768)


def test_silence_is_trimmed_to_a_fixed_margin():
    out, rep = ap.polish_samples(clip(0.8, tone(1, 6000), 1.5), RATE)
    secs = len(out) / RATE
    assert abs(secs - (1 + ap.LEAD_S + ap.TAIL_S)) < 0.03


def test_edges_are_faded_to_zero():
    out, _ = ap.polish_samples(clip(0.1, tone(1, 6000), 0.1), RATE)
    assert out[0] == 0 and abs(out[-1]) <= 1 and max(abs(x) for x in out[:20]) < 200


def test_different_levels_end_up_at_the_same_loudness():
    a, _ = ap.polish_samples(clip(0.2, tone(1, 2000), 0.2), RATE)
    b, _ = ap.polish_samples(clip(0.2, tone(1, 9000), 0.2), RATE)
    assert abs(rms_db(a) - rms_db(b)) < 0.5


def test_peak_never_exceeds_the_ceiling():
    spiky = tone(1, 3000) + array.array("h", [32000]) + tone(1, 3000)
    out, _ = ap.polish_samples(clip(0.1, spiky, 0.1), RATE)
    assert max(abs(x) for x in out) <= 0.9 * 32768


def test_silent_clip_is_left_alone():
    s = array.array("h", [0] * RATE)
    out, rep = ap.polish_samples(s, RATE)
    assert out == s and rep["trimmed"] is False


def test_deterministic(tmp_path):
    src = clip(0.3, tone(1, 5000), 0.4)
    assert ap.polish_samples(src, RATE)[0] == ap.polish_samples(src, RATE)[0]


def test_wav_format_is_preserved(tmp_path):
    p = tmp_path / "a.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(clip(0.3, tone(1, 5000), 0.3).tobytes())
    ap.polish_wav(p)
    with wave.open(str(p)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, RATE)
