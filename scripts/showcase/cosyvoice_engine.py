"""CosyVoice 3 narration engine. Runs the model in its own venv (see setup_cosyvoice.sh)
as one subprocess per batch, so the 0.5B model loads once per run."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from showcase.engines import Engine, EngineUnavailable

RUNNER = Path(__file__).with_name("cosyvoice_runner.py")
MODEL_DIR = "Fun-CosyVoice3-0.5B"


def cv_home() -> Path:
    return Path(os.environ.get("INSPIRE_CV_HOME") or Path.home() / ".cache" / "inspire-video" / "cosyvoice")


class CosyVoiceEngine(Engine):
    name = "cosyvoice"
    version = "Fun-CosyVoice3-0.5B-2512"
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
               "items": [{"text": it.text, "out": str(Path(it.out).resolve())} for it in items]}
        for it in items:
            Path(it.out).parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            jp = Path(td) / "job.json"
            jp.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
            subprocess.run([str(py), str(RUNNER), str(jp)], cwd=repo, check=True,
                           env={**os.environ, "PYTORCH_ENABLE_MPS_FALLBACK": "1"})
