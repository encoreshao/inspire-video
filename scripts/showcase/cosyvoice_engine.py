"""CosyVoice 3 narration engine. Runs the model in its own venv (see setup_cosyvoice.sh)
as one subprocess per batch, so the 0.5B model loads once per run."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from showcase.audio_polish import polish_wav
from showcase.engines import Engine, EngineUnavailable

RUNNER = Path(__file__).with_name("cosyvoice_runner.py")
MODEL_DIR = "Fun-CosyVoice3-0.5B"


def cv_home() -> Path:
    return Path(os.environ.get("INSPIRE_CV_HOME") or Path.home() / ".cache" / "inspire-video" / "cosyvoice")


# Zero-shot copies the delivery of the reference clip, and a clip read flatly gives flat narration. Instruct mode
# keeps the timbre of the clip and takes the delivery from an instruction instead. CosyVoice 3 expects
# "You are a helpful assistant. <instruction><|endofprompt|>"; the instruction is per language.
INSTRUCT_PREFIX = "You are a helpful assistant. "
ENDOFPROMPT = "<|endofprompt|>"
DEFAULT_STYLES = {
    "zh": "请用自然、亲切、抑扬顿挫的语气，像真人在向朋友讲述一样说这句话。",
    "en": "Please speak in a natural, warm and engaging way, with a lively rise and fall in pitch, "
          "like a person telling a friend about something they care about.",
}
DELIVERIES = ("instruct", "zero_shot")
_BASE_VERSION = "Fun-CosyVoice3-0.5B-2512"
POLISH_VERSION = 1       # bump when audio_polish changes what it writes


def _style_for(voice, lang: str) -> str:
    return (getattr(voice, "style", "") or DEFAULT_STYLES.get(lang) or DEFAULT_STYLES["zh"]).strip()


def instruct_text(style: str) -> str:
    style = style.replace(ENDOFPROMPT, "").strip()
    return f"{INSTRUCT_PREFIX}{style}{ENDOFPROMPT}"


class CosyVoiceEngine(Engine):
    name = "cosyvoice"
    # Changes whenever the default instructions or the clean-up change, so cached audio is regenerated.
    version = f"{_BASE_VERSION}+instruct-{hashlib.sha256(json.dumps(DEFAULT_STYLES, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:8]}+polish{POLISH_VERSION}"
    needs_voice = True

    def _paths(self):
        home = cv_home()
        return home / "venv" / "bin" / "python", home / "repo", home / "repo" / "pretrained_models" / MODEL_DIR

    def check(self) -> None:
        py, _, model = self._paths()
        if not py.exists() or not (model / "llm.pt").exists():
            raise EngineUnavailable(
                "CosyVoice 3 is not set up: run `bash scripts/showcase/setup_cosyvoice.sh` (about 9 GB download)"
            )

    def synth_batch(self, items, voice) -> None:
        self.check()
        if voice is None:
            raise EngineUnavailable("the cosyvoice engine needs a voice profile (--voice NAME)")
        py, repo, _ = self._paths()
        job = {"prompt_wav": str(voice.prompt_wav), "prompt_text": voice.prompt_text, "speed": voice.speed,
               # The runner starts in the CosyVoice repo: relative paths would be written there.
               "items": [{"text": it.text, "out": str(Path(it.out).resolve()),
                          **({"instruct": instruct_text(_style_for(voice, it.lang))}
                             if getattr(voice, "delivery", "instruct") == "instruct" else {})}
                         for it in items]}
        for it in items:
            Path(it.out).parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            jp = Path(td) / "job.json"
            jp.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
            subprocess.run([str(py), str(RUNNER), str(jp)], cwd=repo, check=True,
                           env={**os.environ, "PYTORCH_ENABLE_MPS_FALLBACK": "1"})
        for it in items:
            if Path(it.out).exists():        # a missing file is reported by narrate with the beat's name
                polish_wav(it.out)
