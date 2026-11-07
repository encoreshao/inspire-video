#!/usr/bin/env bash
# InspireVideo online installer.
#   curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- claude
#
# Usage: install.sh [claude|codex|both] [--no-deps]
# Env:   INSPIRE_VIDEO_HOME  install folder (default: ~/.inspire-video)
#        INSPIRE_VIDEO_REPO  git URL to clone (default: the GitHub repo)
# Re-running updates an existing install (git pull) and re-links the skill.
set -euo pipefail

REPO="${INSPIRE_VIDEO_REPO:-https://github.com/encoreshao/inspire-video.git}"
DEST="${INSPIRE_VIDEO_HOME:-$HOME/.inspire-video}"
TARGET="both"
EXTRA=()
for arg in "$@"; do
  case "$arg" in
    claude|codex|both) TARGET="$arg" ;;
    --no-deps) EXTRA+=("--no-deps") ;;
    -h|--help) sed -n '2,9p' "$0" 2>/dev/null || true; exit 0 ;;
    *) echo "Unknown option: $arg (use claude|codex|both, --no-deps)" >&2; exit 2 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1; }
if ! need git; then
  echo "git is required. Install it first (macOS: xcode-select --install; Debian/Ubuntu: sudo apt install git)." >&2
  exit 1
fi

if [[ -d "$DEST/.git" ]]; then
  echo "Updating existing install in $DEST"
  git -C "$DEST" pull --ff-only
elif [[ -e "$DEST" && -n "$(ls -A "$DEST" 2>/dev/null)" ]]; then
  echo "$DEST exists and is not an InspireVideo checkout. Move it or set INSPIRE_VIDEO_HOME." >&2
  exit 1
else
  echo "Cloning $REPO into $DEST"
  git clone --depth 1 "$REPO" "$DEST"
fi

# Heads-up for system tools the installer cannot add by itself.
for t in python3 node npm ffmpeg ffprobe; do
  need "$t" || echo "Note: '$t' not found. macOS: brew install python node ffmpeg   Debian/Ubuntu: sudo apt install python3 python3-pip nodejs npm ffmpeg"
done

bash "$DEST/scripts/install.sh" "$TARGET" ${EXTRA[@]+"${EXTRA[@]}"}

echo
echo "Installed (inspire-video and inspire-showcase). Start a NEW Claude Code / Codex session, then try:"
echo "  /inspire-video create from ./podcast.mp4"
echo "  /inspire-showcase make a video from https://github.com/owner/repo"
