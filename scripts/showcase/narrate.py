#!/usr/bin/env python3
"""Narrate a project's beats: writes audio/<beat>.wav and timings.json.

  python scripts/showcase/narrate.py <project-dir> [--engine say|kokoro|cosyvoice] [--voice NAME] [--lang en|zh]

Reads <project-dir>/video_manifest.json: beats[] with id, en, zh; optional
narration_lang ("en" default) and voice. Unchanged beats are reused from the cache.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # so `python scripts/showcase/narrate.py` finds the package

from showcase import engines  # noqa: E402
from showcase.engines import Item  # noqa: E402
from showcase.timing import MAX_TOTAL, MIN_TOTAL, LengthError, beat_seconds, cache_key, check_total, wav_seconds  # noqa: E402
from showcase.voices import VoiceError, load_voice  # noqa: E402

BEAT_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")
LANGS = ("en", "zh")


class NarrationError(ValueError):
    pass


def _voice_id(voice) -> str:
    if voice is None:
        return "-"
    digest = hashlib.sha256(Path(voice.prompt_wav).read_bytes() + voice.prompt_text.encode("utf-8")).hexdigest()
    style = f"{getattr(voice, 'delivery', 'instruct')}:{getattr(voice, 'style', '')}"
    return f"{voice.name}:{digest}:{hashlib.sha256(style.encode('utf-8')).hexdigest()[:12]}"


def _manifest_voice(project: Path):
    """The manifest's optional `voice` name; problems with the manifest itself are reported by narrate()."""
    try:
        name = json.loads((project / "video_manifest.json").read_text(encoding="utf-8")).get("voice")
    except (OSError, ValueError, AttributeError):
        return None
    return name if isinstance(name, str) and name else None


def narrate(project, engine, voice=None, lang=None, min_total=MIN_TOTAL, max_total=MAX_TOTAL) -> dict:
    project = Path(project)
    (project / "timings.json").unlink(missing_ok=True)      # never leave a stale timings file, whatever fails below
    mpath = project / "video_manifest.json"
    try:
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise NarrationError(f"cannot read {mpath}: {e}") from None
    beats = manifest.get("beats")
    if not beats:
        raise NarrationError("the manifest has no beats")
    if not isinstance(beats, list) or not all(isinstance(b, dict) for b in beats):
        raise NarrationError("the manifest's beats must be a list of beat objects")
    lang = lang or manifest.get("narration_lang") or (voice.language if voice else "en")
    if lang not in LANGS:
        raise NarrationError(f"narration language must be one of {LANGS}, got {lang!r}")
    if engine.needs_voice and voice is None:
        raise NarrationError(f"the {engine.name} engine needs a voice profile: pass --voice NAME")
    if voice is not None and not engine.needs_voice:
        raise NarrationError(
            f"the {engine.name} engine does not use voice profiles: drop --voice, or use --engine cosyvoice")
    engine.check()

    # Validate every beat before touching the disk.
    seen, plan = set(), []
    for b in beats:
        bid = b.get("id")
        if not isinstance(bid, str) or not BEAT_ID.fullmatch(bid):
            raise NarrationError(f"invalid beat id {bid!r}: use a-z, 0-9, '_' or '-', 1-48 characters")
        if bid in seen:
            raise NarrationError(f"duplicate beat id {bid!r}")
        seen.add(bid)
        text = (b.get(lang) or "").strip()
        if not text:
            raise NarrationError(f"beat {bid!r} has no text for language {lang!r}")
        plan.append((bid, text))

    audio_dir = project / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    speed = voice.speed if voice else 1.0
    vid = _voice_id(voice)
    todo = []
    for bid, text in plan:
        wav, keyfile = audio_dir / f"{bid}.wav", audio_dir / f"{bid}.key"
        key = cache_key(text, lang, vid, engine.name, speed, engine.version)
        if wav.exists() and keyfile.exists() and keyfile.read_text() == key:
            continue
        wav.unlink(missing_ok=True)
        keyfile.unlink(missing_ok=True)
        todo.append((Item(text, lang, wav), keyfile, key))

    if todo:
        engine.synth_batch([t[0] for t in todo], voice)
        for item, keyfile, key in todo:
            if not Path(item.out).exists():
                raise RuntimeError(f"the {engine.name} engine produced no audio for {Path(item.out).name}")
            keyfile.write_text(key)                          # only after the audio exists

    # A beat is held at least min_total / beats seconds: a few spoken sentences are shorter than the minimum
    # video length, and the camera move needs the time anyway. The audio itself is never stretched.
    floor = math.ceil(min_total / len(plan) * 100) / 100
    rows = []
    for bid, text in plan:
        secs = wav_seconds(audio_dir / f"{bid}.wav")
        rows.append({"id": bid, "audio": f"audio/{bid}.wav", "audio_seconds": round(secs, 2),
                     "seconds": max(beat_seconds(secs), floor),
                     "text_sha": hashlib.sha256(text.encode("utf-8")).hexdigest()})   # lets render notice stale audio
    total = check_total([r["seconds"] for r in rows], lo=min_total, hi=max_total)
    timings = {"engine": engine.name, "voice": voice.name if voice else None, "lang": lang,
               "total": total, "beats": rows}
    (project / "timings.json").write_text(json.dumps(timings, ensure_ascii=False, indent=1), encoding="utf-8")
    return timings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Narrate a showcase project")
    ap.add_argument("project_dir")
    ap.add_argument("--engine", default="say", choices=engines.ENGINE_NAMES)
    ap.add_argument("--voice", help="voice profile name (required by cosyvoice)")
    ap.add_argument("--lang", choices=LANGS, help="narration language (default: manifest narration_lang, else en)")
    a = ap.parse_args(argv)
    try:
        engine = engines.get_engine(a.engine)
        voice_name = a.voice or (_manifest_voice(Path(a.project_dir)) if engine.needs_voice else None)
        voice = load_voice(voice_name) if voice_name else None
        t = narrate(Path(a.project_dir), engine, voice, a.lang, min_total=MIN_TOTAL, max_total=MAX_TOTAL)
    except subprocess.CalledProcessError as e:
        print(f"error: the {a.engine} engine failed (exit status {e.returncode}); see its output above", file=sys.stderr)
        return 1
    except (ValueError, RuntimeError, OSError, KeyError, wave.Error, ZeroDivisionError) as e:
        # ValueError covers NarrationError, LengthError, VoiceError and bad JSON; RuntimeError covers EngineUnavailable.
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"{len(t['beats'])} beats, {t['total']} s total, engine={t['engine']}, lang={t['lang']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
