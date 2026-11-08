"""Runs inside the CosyVoice venv, cwd = the CosyVoice repo. Usage: cosyvoice_runner.py job.json"""
import inspect
import json
import os
import sys

repo = os.getcwd()
sys.path.insert(0, repo)                                   # the repo's `cosyvoice` package must win
sys.path.append(os.path.join(repo, "third_party", "Matcha-TTS"))

import torch  # noqa: E402
import torchaudio  # noqa: E402
from cosyvoice.cli.cosyvoice import AutoModel  # noqa: E402

PREFIX = "You are a helpful assistant.<|endofprompt|>"


def main() -> None:
    with open(sys.argv[1], encoding="utf-8") as f:
        job = json.load(f)
    cv = AutoModel(model_dir="pretrained_models/Fun-CosyVoice3-0.5B")
    kwargs = {"stream": False}
    if "speed" in inspect.signature(cv.inference_zero_shot).parameters:
        kwargs["speed"] = job["speed"]
    for it in job["items"]:
        if it.get("instruct"):
            # Instruct mode keeps the timbre of the reference clip but takes the delivery from the instruction.
            gen = cv.inference_instruct2(it["text"], it["instruct"], job["prompt_wav"], **kwargs)
        else:
            gen = cv.inference_zero_shot(it["text"], PREFIX + job["prompt_text"], job["prompt_wav"], **kwargs)
        chunks = [r["tts_speech"] for r in gen]
        if not chunks:
            sys.exit(f"CosyVoice returned no audio for: {it['text'][:40]!r}")
        torchaudio.save(it["out"], torch.cat(chunks, dim=1), cv.sample_rate, encoding="PCM_S", bits_per_sample=16)


if __name__ == "__main__":
    main()
