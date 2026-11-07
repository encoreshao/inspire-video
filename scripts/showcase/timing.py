"""Durations, the total-length rule and the audio cache key for narration."""
from __future__ import annotations

import hashlib
import json
import wave

PAD = 0.4
MIN_TOTAL = 40.0
MAX_TOTAL = 150.0


class LengthError(ValueError):
    pass


def wav_seconds(path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def beat_seconds(audio_seconds: float) -> float:
    return round(audio_seconds + PAD, 2)


def check_total(beat_secs, lo: float = MIN_TOTAL, hi: float = MAX_TOTAL) -> float:
    if not beat_secs:
        raise LengthError("no beats to narrate")
    total = round(sum(beat_secs), 2)
    if total > hi:
        raise LengthError(f"narration is {total} s but the maximum is {hi:g} s: shorten the script")
    if total < lo:
        raise LengthError(f"narration is {total} s but the minimum is {lo:g} s: write a longer script")
    return total


def cache_key(text: str, lang: str, voice_id: str, engine: str, speed: float, engine_version: str) -> str:
    payload = json.dumps([text, lang, voice_id, engine, speed, engine_version], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
