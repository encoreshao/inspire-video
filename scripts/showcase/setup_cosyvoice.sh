#!/usr/bin/env bash
# One-time, opt-in setup of CosyVoice 3 for showcase narration (about 9 GB, Apple Silicon).
# Installs into $INSPIRE_CV_HOME (default ~/.cache/inspire-video/cosyvoice), never into the repo.
set -euo pipefail

HOME_DIR="${INSPIRE_CV_HOME:-$HOME/.cache/inspire-video/cosyvoice}"
REPO="$HOME_DIR/repo"
VENV="$HOME_DIR/venv"
MODEL="$REPO/pretrained_models/Fun-CosyVoice3-0.5B"

command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/" >&2; exit 1; }
echo "Installing into $HOME_DIR (needs about 9 GB free)"
mkdir -p "$HOME_DIR"

[[ -d "$REPO/.git" ]] || git clone --depth 1 https://github.com/FunAudioLLM/CosyVoice.git "$REPO"
git -C "$REPO" submodule update --init --depth 1 third_party/Matcha-TTS

uv python install 3.10
# --python-preference only-managed: ignore any broken system python (for example an x86-only /usr/local/bin/python3)
[[ -x "$VENV/bin/python" ]] || uv venv --python 3.10 --python-preference only-managed "$VENV"

# The repo's requirements.txt pins Linux/CUDA packages; keep only what a Mac needs.
grep -v -E '^--extra|deepspeed|onnxruntime-gpu|tensorrt|gradio|grpcio|tensorboard|fastapi|uvicorn|lightning|gdown|wget|openai-whisper|^torch|pyworld|matplotlib' \
  "$REPO/requirements.txt" > "$HOME_DIR/requirements-mac.txt"
uv pip install --python "$VENV/bin/python" torch==2.3.1 torchaudio==2.3.1 -r "$HOME_DIR/requirements-mac.txt"
# Packages Matcha-TTS/CosyVoice import at load time that the filter above dropped.
uv pip install --python "$VENV/bin/python" openai-whisper lightning==2.2.4 matplotlib==3.7.5 \
  gdown==5.1.0 wget==3.2 pyworld 'setuptools<81'

"$VENV/bin/python" - <<PY || true
# ModelScope may print a harmless symlink error at the end; the files are verified below.
from modelscope import snapshot_download
snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', local_dir='$MODEL')
PY

for f in llm.pt flow.pt hift.pt cosyvoice3.yaml; do
  [[ -f "$MODEL/$f" ]] || { echo "Model download incomplete: missing $f" >&2; exit 1; }
done
echo "CosyVoice 3 is ready. Next: python scripts/showcase/voices.py add --name <you> --wav clip.wav --text-file clip.txt"
