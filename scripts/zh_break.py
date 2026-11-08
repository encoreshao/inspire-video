"""Chinese caption units: pieces a caption line must never break inside.

Adapted from backend/services/studio/cjk_segment.py of autoclip (https://github.com/zhouxiaoka/autoclip),
Copyright (c) 2024 AutoClip Team, MIT License (LICENSES/MIT-autoclip.txt). Changes: dropped the highlight
and phrase helpers, removed the `protected` argument, added `zh_units`, moved the word list to assets/lexicon/.
The word list is derived from jieba's dictionary (MIT, LICENSES/MIT-jieba.txt).

  break_units("每周工作80小时") -> ["每周", "工作", "80小时"]

The renderer wraps captions between units, so a line is never "增长八|倍" or "每周工|作80小时".
Without the word list every Chinese character is its own unit (the old behaviour).
"""
from __future__ import annotations

import gzip
import math
import re
from functools import lru_cache
from pathlib import Path

LEXICON = Path(__file__).resolve().parent.parent / "assets" / "lexicon" / "zh_words.txt.gz"
_UNITS = ("小时", "分钟", "秒钟", "毫秒", "纳米", "公里", "千克", "公斤", "个月", "倍", "个", "元", "块", "年", "天", "秒", "点")
_NUMERAL = set("零一二两三四五六七八九十百千万亿几半")
_MEASURE = set("倍项个位种次年天件条家段步层份批台部周月岁成点名轮代张句")
_CJK = re.compile(r"[一-鿿]")


def _number_token(text: str, index: int) -> str | None:
    if not text[index].isdigit():
        return None
    end = index + 1
    while end < len(text) and (text[end].isdigit() or (text[end] == "." and end + 1 < len(text) and text[end + 1].isdigit())):
        end += 1
    if end < len(text) and text[end] in "十百千万亿":
        end += 1
    probe = end
    if probe < len(text) and text[probe] == " ":
        probe += 1
    for unit in _UNITS:
        if text.startswith(unit, probe):
            return text[index:probe + len(unit)]
    if probe < len(text) and text[probe] in "%％":
        return text[index:probe + 1]
    return text[index:end]


def _latin_token(text: str, index: int) -> str | None:
    if not ("A" <= text[index] <= "z"):
        return None
    end = index + 1
    while end < len(text) and text[end].isascii() and (text[end].isalnum() or text[end] in "+._-'"):
        end += 1
    if end < len(text) and text[end] in "里中":
        end += 1
    return text[index:end]


def _tokenize(text: str) -> list[str]:
    """A number with its unit and a Latin token are atomic; other characters are one token each."""
    tokens: list[str] = []
    index = 0
    while index < len(text):
        taken = _number_token(text, index) or _latin_token(text, index)
        if taken:
            tokens.append(taken)
            index += len(taken)
        elif text[index] == " ":
            if tokens and not tokens[-1].endswith(" "):
                tokens[-1] += " "
            index += 1
        else:
            tokens.append(text[index])
            index += 1
    return [t for t in tokens if t.strip()]


@lru_cache(maxsize=1)
def _lexicon() -> tuple[dict[str, float], float]:
    try:
        with gzip.open(LEXICON, "rt", encoding="utf-8") as handle:
            counts = {}
            for line in handle:
                word, _, freq = line.rstrip("\n").partition(" ")
                if word and freq.isdigit():
                    counts[word] = int(freq)
    except OSError:
        return {}, 0.0
    total = float(sum(counts.values()) or 1)
    return {w: math.log(f / total) for w, f in counts.items()}, math.log(1 / total)


def _is_cjk(token: str) -> bool:
    return len(token) == 1 and bool(_CJK.match(token))


def _segment_run(run: str) -> list[str]:
    """Fewest-words split of a Chinese run, ties broken by word frequency, so a known word wins over its characters."""
    words, floor = _lexicon()
    if not words:
        return list(run)
    n = len(run)
    best = [(0, 0.0)] + [(10 ** 6, 0.0)] * n
    back = [0] * (n + 1)
    for end in range(1, n + 1):
        for size in range(1, min(4, end) + 1):
            piece = run[end - size:end]
            score = words.get(piece)
            if score is None:
                if size > 1:
                    continue
                score = floor
            count, logp = best[end - size]
            candidate = (count + 1, logp - score)
            if candidate < best[end]:
                best[end], back[end] = candidate, end - size
    out, end = [], n
    while end > 0:
        out.append(run[back[end]:end])
        end = back[end]
    return out[::-1]


def break_units(text: str) -> list[str]:
    """Words, numbers with units and Latin tokens; a numeral and its measure word stay with the next word."""
    units: list[str] = []
    run = ""
    for token in _tokenize(text) + [""]:
        core = token.rstrip(" ")
        if token and _is_cjk(core):
            run += core                              # "行 " is the character 行 followed by a space, not a new word
            if core != token:                        # the space ends the run; it stays on the run's last unit
                units.extend(_segment_run(run)[:-1] + [_segment_run(run)[-1] + " "])
                run = ""
            continue
        if run:
            units.extend(_segment_run(run))
            run = ""
        if token:
            units.append(token)
    merged: list[str] = []
    for unit in units:
        if merged and unit[0] in _MEASURE and all(ch in _NUMERAL for ch in merged[-1]):
            merged[-1] += unit                       # 八 + 倍, 一 + 项
        else:
            merged.append(unit)
    joined: list[str] = []
    glue = False
    for unit in merged:
        if glue and joined and _is_cjk(unit[0]) and len(joined[-1] + unit) <= 6:
            joined[-1] += unit                       # 一项 + 预测
        else:
            joined.append(unit)
        glue = (len(unit) >= 2 and unit[-1] in _MEASURE and all(ch in _NUMERAL for ch in unit[:-1])
                and not unit.endswith("倍"))
    return joined


_CLOSING = set("，。、！？：；,.!?:;”’）》」』】…")
_OPENING = set("“‘（《「『【")


def _attach_punctuation(units: list[str]) -> list[str]:
    """Closing marks join the unit before and opening marks the unit after, because a unit rendered as an
    inline-block no longer follows the browser's rule that a line cannot start with a closing mark."""
    out: list[str] = []
    pending = ""
    for unit in units:
        if out and unit[0] in _CLOSING:
            out[-1] += unit
        elif all(ch in _OPENING for ch in unit):
            pending += unit
        else:
            out.append(pending + unit)
            pending = ""
    if pending:
        if out:
            out[-1] += pending
        else:
            out.append(pending)
    return out


def zh_units(text: str) -> list[str] | None:
    """Units for the renderer, or None when the text has no Chinese (nothing to protect)."""
    return _attach_punctuation(break_units(text)) if _CJK.search(text or "") else None


def with_units(items: list[dict], enabled: bool = True) -> list[dict]:
    """Copies of caption dicts (each with a `zh` text) plus `zhUnits` for the renderer; unchanged when disabled."""
    out = []
    for item in items:
        units = zh_units(item.get("zh", "")) if enabled else None
        out.append({**item, "zhUnits": units} if units else dict(item))
    return out
