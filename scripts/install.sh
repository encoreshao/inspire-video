#!/usr/bin/env bash
# Install InspireVideo as an agent skill (symlink to this clone) and set up dependencies.
# Usage: bash scripts/install.sh [claude|codex|both] [--no-deps]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-both}"
DEPS=1
[[ "${2:-}" == "--no-deps" ]] && DEPS=0

link_to() {
  local dest="$1/inspire-video"
  mkdir -p "$1"
  if [[ "$(cd "$1" && pwd)/inspire-video" == "$ROOT" ]]; then
    echo "Already installed in place: $ROOT"; return
  fi
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    echo "Refusing to replace existing non-symlink: $dest (move it first)" >&2; exit 1
  fi
  ln -sfn "$ROOT" "$dest"
  echo "Linked $dest -> $ROOT"
}

link_showcase() {
  local dest="$1/inspire-showcase"
  mkdir -p "$1"
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    echo "Refusing to replace existing non-symlink: $dest (move it first)" >&2; exit 1
  fi
  ln -sfn "$ROOT/skills/inspire-showcase" "$dest"
  echo "Linked $dest -> $ROOT/skills/inspire-showcase"
}

case "$TARGET" in
  claude) link_to "$HOME/.claude/skills"; link_showcase "$HOME/.claude/skills" ;;
  codex)  link_to "$HOME/.agents/skills"; link_showcase "$HOME/.agents/skills" ;;
  both)   link_to "$HOME/.claude/skills"; link_showcase "$HOME/.claude/skills"
          link_to "$HOME/.agents/skills"; link_showcase "$HOME/.agents/skills" ;;
  *) echo "Usage: $0 [claude|codex|both] [--no-deps]" >&2; exit 2 ;;
esac

if [[ $DEPS -eq 1 ]]; then
  echo "Installing Python deps..."
  python3 -m pip install -e "$ROOT"
  echo "Installing Remotion deps..."
  (cd "$ROOT/video" && npm install --no-audit --no-fund)
fi
python3 "$ROOT/scripts/check_env.py"
