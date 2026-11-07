#!/usr/bin/env python3
"""Voice profiles for narration.

A profile is a folder `voices/<name>/` holding the reference clip (`prompt.wav`,
16 kHz mono, 3-30 s), its exact transcript (`prompt.txt`) and `meta.json`.

  python scripts/showcase/voices.py add --name encore --wav clip.wav --text-file clip.txt [--lang zh]
  python scripts/showcase/voices.py list
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import wave
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOICES = ROOT / "voices"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
MIN_SECONDS, MAX_SECONDS = 3.0, 30.0
FIX = "convert it with: ffmpeg -i <input> -ar 16000 -ac 1 clip.wav"


class VoiceError(ValueError):
    pass


@dataclass(frozen=True)
class VoiceProfile:
    name: str
    prompt_wav: Path
    prompt_text: str
    language: str
    engine: str
    speed: float
    created: str


def _check_name(name) -> None:
    if not isinstance(name, str) or not NAME_RE.match(name):
        raise VoiceError(
            f"invalid voice name {name!r}: use 1-32 characters from a-z, 0-9, '_' or '-', "
            "starting with a letter or digit"
        )


def _wav_info(path: Path) -> tuple[int, int, float]:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getframerate(), w.getnchannels(), w.getnframes() / w.getframerate()
    except (wave.Error, EOFError, ZeroDivisionError, OSError) as e:
        raise VoiceError(f"{path} is not a readable wav file ({e}); {FIX}") from None


def create_voice(name, wav, transcript, *, language="zh", engine="cosyvoice",
                 speed=1.0, overwrite=False, root=None) -> VoiceProfile:
    root = Path(root) if root else VOICES
    _check_name(name)
    transcript = (transcript or "").strip()
    if not transcript:
        raise VoiceError("the transcript of the clip is required (the exact words spoken)")
    if language not in ("zh", "en"):
        raise VoiceError(f"language must be 'zh' or 'en', got {language!r}")
    wav = Path(wav)
    rate, channels, seconds = _wav_info(wav)
    if rate != 16000 or channels != 1:
        raise VoiceError(f"{wav} is {rate} Hz, {channels} channel(s); it must be 16000 Hz mono; {FIX}")
    if not MIN_SECONDS <= seconds <= MAX_SECONDS:
        raise VoiceError(
            f"{wav} is {seconds:.1f} s; use a clean clip of {MIN_SECONDS:.0f}-{MAX_SECONDS:.0f} s (10-20 s is best)"
        )
    folder = root / name
    if folder.exists() and not overwrite:
        raise VoiceError(f"voice {name!r} already exists; pass --overwrite to replace it")
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(wav, folder / "prompt.wav")
    (folder / "prompt.txt").write_text(transcript + "\n", encoding="utf-8")
    meta = {"name": name, "language": language, "engine": engine, "speed": speed,
            "created": date.today().isoformat(), "seconds": round(seconds, 2)}
    (folder / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return load_voice(name, root=root)


def load_voice(name, root=None) -> VoiceProfile:
    root = Path(root) if root else VOICES
    _check_name(name)
    folder = root / name
    try:
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        text = (folder / "prompt.txt").read_text(encoding="utf-8").strip()
    except OSError:
        raise VoiceError(
            f"voice {name!r} not found in {root}; create it with: "
            f"python scripts/showcase/voices.py add --name {name} --wav clip.wav --text-file clip.txt"
        ) from None
    wav = folder / "prompt.wav"
    if not wav.exists():
        raise VoiceError(f"voice {name!r} is missing {wav}")
    return VoiceProfile(name=name, prompt_wav=wav, prompt_text=text, language=meta["language"],
                        engine=meta["engine"], speed=float(meta["speed"]), created=meta["created"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Manage narration voice profiles")
    ap.add_argument("--root", help="voices folder (default: <repo>/voices)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add", help="create a voice profile from a reference clip")
    add.add_argument("--name", required=True)
    add.add_argument("--wav", required=True)
    add.add_argument("--text-file", required=True, help="file with the exact transcript of the clip")
    add.add_argument("--lang", default="zh", choices=["zh", "en"])
    add.add_argument("--overwrite", action="store_true")
    sub.add_parser("list", help="list voice profiles")
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else VOICES
    try:
        if a.cmd == "add":
            text = Path(a.text_file).read_text(encoding="utf-8")
            p = create_voice(a.name, a.wav, text, language=a.lang, overwrite=a.overwrite, root=root)
            print(f"created voice {p.name} ({p.language}) in {p.prompt_wav.parent}")
        else:
            names = sorted(d.name for d in root.iterdir() if (d / "meta.json").exists()) if root.exists() else []
            print("\n".join(names) if names else "no voices yet")
    except (VoiceError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
