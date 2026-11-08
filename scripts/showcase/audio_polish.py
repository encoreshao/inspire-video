"""Deterministic clean-up for one narration clip, so dozens of separately synthesized beats join smoothly.

Pure standard library (wave + array): trims the silence around the speech to a fixed small value, fades the
edges (no clicks at the joins) and scales the clip to a common gated loudness with a peak ceiling.
The sample rate, channel count and sample width of the file are never changed.
"""
from __future__ import annotations

import array
import math
import sys
import wave
from pathlib import Path

LEAD_S = 0.06            # silence kept before the first word
TAIL_S = 0.12            # silence kept after the last word
FADE_S = 0.02            # fade in / out at the clip edges
FRAME_S = 0.01           # analysis window
SILENCE_DB = -45.0       # a frame quieter than this (dBFS RMS) is silence for trimming
GATE_DB = -40.0          # frames quieter than this do not count towards loudness
TARGET_DB = -20.0        # gated RMS every clip is scaled to (about -23 LUFS integrated for speech)
PEAK_CEIL = 0.89         # about -1 dBFS; the gain is reduced rather than letting a clip clip
MAX_GAIN_DB = 18.0


def _db(x: float) -> float:
    return 20 * math.log10(x) if x > 0 else -200.0


def _frame_rms(samples, size):
    for i in range(0, len(samples), size):
        chunk = samples[i:i + size]
        yield i, math.sqrt(sum(s * s for s in chunk) / len(chunk)) / 32768.0


def polish_samples(samples, rate: int):
    """samples: array('h') mono. Returns (polished array('h'), report dict)."""
    size = max(1, int(rate * FRAME_S))
    frames = list(_frame_rms(samples, size))
    voiced = [i for i, r in frames if _db(r) > SILENCE_DB]
    if not voiced:
        return samples, {"trimmed": False, "gain_db": 0.0}
    start, end = voiced[0], min(len(samples), voiced[-1] + size)
    body = samples[start:end]
    lead, tail = int(rate * LEAD_S), int(rate * TAIL_S)
    out = array.array("h", bytes(2 * lead)) + body + array.array("h", bytes(2 * tail))

    gated = [r for _, r in _frame_rms(body, size) if _db(r) > GATE_DB]
    rms = math.sqrt(sum(r * r for r in gated) / len(gated)) if gated else 0.0
    peak = max(max(out), -min(out)) / 32768.0
    gain_db = 0.0
    if rms > 0:
        gain_db = min(TARGET_DB - _db(rms), MAX_GAIN_DB)
        if peak * 10 ** (gain_db / 20) > PEAK_CEIL:
            gain_db = _db(PEAK_CEIL / peak)
    g = 10 ** (gain_db / 20)
    fade = max(1, int(rate * FADE_S))
    n = len(out)
    for i in range(n):
        f = 1.0
        if i < fade:
            f = i / fade
        elif i >= n - fade:
            f = (n - 1 - i) / fade
        out[i] = max(-32768, min(32767, int(round(out[i] * g * f))))
    return out, {"trimmed": True, "gain_db": round(gain_db, 2), "seconds": round(n / rate, 3)}


def polish_wav(path) -> dict:
    """Rewrite a 16-bit mono wav in place (via a temp file); other formats are left untouched."""
    path = Path(path)
    with wave.open(str(path), "rb") as w:
        ch, width, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(w.getnframes())
    if ch != 1 or width != 2:
        return {"trimmed": False, "gain_db": 0.0}
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder == "big":
        samples.byteswap()
    out, report = polish_samples(samples, rate)
    if sys.byteorder == "big":
        out.byteswap()
    tmp = path.with_name(path.name + ".tmp")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(out.tobytes())
    tmp.replace(path)
    return report
