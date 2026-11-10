"""Durations, the total-length rule and the audio cache key for narration."""
from __future__ import annotations

import hashlib
import json
import wave

PAD = 0.4                        # the fixed pause after a line, when the caller gives none
PAUSE_MIN, PAUSE_MAX = 0.4, 1.0  # a natural pause after a line, in seconds
PAUSE_LONG_LINE = 0.3            # a full-length line (about 6.5 s of speech) earns this much more than a short one
PAUSE_TOPIC = 0.3                # and so does the end of a block: the next beat changes topic
MIN_TOTAL = 120.0                # 2 min
MAX_TOTAL = 300.0                # 5 min


class LengthError(ValueError):
    pass


def wav_seconds(path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def beat_seconds(audio_seconds: float, pause: float = PAD) -> float:
    return round(audio_seconds + pause, 2)


def topic_break(beat: dict, next_beat: dict) -> bool:
    """Whether the next beat starts a new block: the rule the video's transitions use (video/src/showcase/transitions.mjs
    `topicChanged`): the topics differ when either beat names one, otherwise the captured page differs."""
    a, b = beat.get("topic") or "", next_beat.get("topic") or ""
    if a or b:
        return a != b
    return (beat.get("asset") or "") != (next_beat.get("asset") or "")


def pause_after(audio_seconds: float, topic_change: bool = False) -> float:
    """The pause after a spoken line, as a person would leave it: short after a short remark, longer after a full sentence,
    longest where one block ends and the next begins. 0.4 s (a line of 3 s or less, same block) to 1.0 s (a full line, new block)."""
    size = min(1.0, max(0.0, (audio_seconds - 3.0) / 3.5))          # 0 for a short line, 1 for one of 6.5 s or more
    pause = PAUSE_MIN + PAUSE_LONG_LINE * size + (PAUSE_TOPIC if topic_change else 0.0)
    return round(min(PAUSE_MAX, pause), 2)


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
