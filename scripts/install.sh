#!/usr/bin/env bash
# Install the InspireVideo skills (symlinks into this clone) and set up dependencies.
# Every folder under skills/ that holds a SKILL.md is linked, so a new skill needs no installer change.
# Usage: bash scripts/install.sh [claude|codex|both] [--no-deps]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-both}"
DEPS=1
[[ "${2:-}" == "--no-deps" ]] && DEPS=0

link_skill() {   # link_skill <skills-folder> <skill-folder>
  local name dest
  name="$(basename "$2")"
  dest="$1/$name"
  mkdir -p "$1"
  if [[ "$(cd "$1" && pwd)/$name" == "$ROOT" ]]; then
    echo "Already in place: $ROOT (its root SKILL.md points at skills/$name)"; return
  fi
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    echo "Refusing to replace existing non-symlink: $dest (move it first)" >&2; exit 1
  fi
  ln -sfn "$2" "$dest"           # also replaces an old link that pointed at the repository root
  echo "Linked $dest -> $2"
}

link_all() {     # link_all <skills-folder>
  local found=0 d
  for d in "$ROOT"/skills/*/; do
    [[ -f "${d}SKILL.md" ]] || continue
    link_skill "$1" "${d%/}"
    found=1
  done
  [[ $found -eq 1 ]] || { echo "No skills found in $ROOT/skills" >&2; exit 1; }
}

case "$TARGET" in
  claude) link_all "$HOME/.claude/skills" ;;
  codex)  link_all "$HOME/.agents/skills" ;;
  both)   link_all "$HOME/.claude/skills"; link_all "$HOME/.agents/skills" ;;
  *) echo "Usage: $0 [claude|codex|both] [--no-deps]" >&2; exit 2 ;;
esac

if [[ $DEPS -eq 1 ]]; then
  echo "Installing Python deps..."
  python3 -m pip install -e "$ROOT"
  echo "Installing Remotion deps..."
  (cd "$ROOT/video" && npm install --no-audit --no-fund)
fi
python3 "$ROOT/scripts/check_env.py"
