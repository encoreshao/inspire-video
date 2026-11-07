"""Narration engines. Each writes one wav per item; text is always passed as data
(stdin or a single `--text=...` argument), never through a shell."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

ESPEAK_LIB = "/opt/homebrew/lib/libespeak-ng.dylib"
ESPEAK_DATA = "/opt/homebrew/share/espeak-ng-data"
KOKORO_MODEL = "mlx-community/Kokoro-82M-bf16"
KOKORO_VOICES = {"zh": ("z", "zf_xiaobei"), "en": ("a", "af_heart")}
SAY_VOICES = {"zh": "Tingting", "en": "Samantha"}


class EngineUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Item:
    text: str
    lang: str
    out: Path


class Engine:
    name = "base"
    version = "0"
    needs_voice = False

    def check(self) -> None:
        """Raise EngineUnavailable (naming the fix) if the engine cannot run here."""

    def synth_batch(self, items, voice) -> None:
        raise NotImplementedError


def _concat_wavs(paths, out) -> None:
    params = None
    frames = []
    for p in paths:
        with wave.open(str(p), "rb") as w:
            fmt = (w.getnchannels(), w.getsampwidth(), w.getframerate())
            if params is None:
                params = fmt
            elif fmt != params:
                raise ValueError(f"cannot join wav chunks with a different format ({fmt} vs {params})")
            frames.append(w.readframes(w.getnframes()))
    with wave.open(str(out), "wb") as w:
        w.setnchannels(params[0])
        w.setsampwidth(params[1])
        w.setframerate(params[2])
        for f in frames:
            w.writeframes(f)


class SayEngine(Engine):
    name = "say"
    version = "macos-say-1"

    def check(self) -> None:
        for tool in ("say", "afconvert"):
            if shutil.which(tool) is None:
                raise EngineUnavailable(f"'{tool}' not found: the say engine needs macOS")

    def synth_batch(self, items, voice) -> None:
        self.check()
        for it in items:
            v = SAY_VOICES.get(it.lang)
            if v is None:
                raise ValueError(f"unsupported language {it.lang!r}")
            Path(it.out).parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory() as td:
                aiff = Path(td) / "o.aiff"
                subprocess.run(["say", "-v", v, "-o", str(aiff), "-f", "-"],
                               input=it.text.encode("utf-8"), check=True)
                subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@24000", "-c", "1",
                                str(aiff), str(it.out)], check=True)


class KokoroEngine(Engine):
    name = "kokoro"
    version = "kokoro-82M-bf16"

    def check(self) -> None:
        if importlib.util.find_spec("mlx_audio") is None:
            raise EngineUnavailable(
                "mlx-audio is not installed: pip install mlx-audio 'misaki[zh]' 'misaki[en]' "
                "jieba pypinyin num2words spacy && python -m spacy download en_core_web_sm"
            )
        for p in (ESPEAK_LIB, ESPEAK_DATA):
            if not Path(p).exists():
                raise EngineUnavailable("espeak-ng is missing: brew install espeak-ng")

    def synth_batch(self, items, voice) -> None:
        self.check()
        env = {**os.environ, "PHONEMIZER_ESPEAK_LIBRARY": ESPEAK_LIB, "ESPEAK_DATA_PATH": ESPEAK_DATA}
        for it in items:
            if it.lang not in KOKORO_VOICES:
                raise ValueError(f"unsupported language {it.lang!r}")
            code, v = KOKORO_VOICES[it.lang]
            Path(it.out).parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory() as td:
                subprocess.run(
                    [sys.executable, "-m", "mlx_audio.tts.generate", "--model", KOKORO_MODEL,
                     f"--text={it.text}", "--voice", v, "--lang_code", code, "--file_prefix", "o"],
                    cwd=td, env=env, check=True)
                chunks = sorted(Path(td).glob("o_*.wav"))
                if not chunks:
                    raise RuntimeError(f"kokoro produced no audio for {Path(it.out).name}")
                _concat_wavs(chunks, it.out)


ENGINE_NAMES = ("say", "kokoro", "cosyvoice")


def get_engine(name: str) -> Engine:
    if name == "say":
        return SayEngine()
    if name == "kokoro":
        return KokoroEngine()
    if name == "cosyvoice":
        from showcase.cosyvoice_engine import CosyVoiceEngine  # lazy: avoids a circular import
        return CosyVoiceEngine()
    raise EngineUnavailable(f"unknown engine {name!r}; choose one of: {', '.join(ENGINE_NAMES)}")
