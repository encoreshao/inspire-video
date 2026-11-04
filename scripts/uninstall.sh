#!/usr/bin/env bash
# Remove the skill links (does not delete this folder or your outputs).
# Usage: bash scripts/uninstall.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for d in "$HOME/.claude/skills/inspire-video" "$HOME/.agents/skills/inspire-video"; do
  if [[ -L "$d" && "$(cd "$d" && pwd -P)" == "$(cd "$ROOT" && pwd -P)" ]]; then
    rm "$d" && echo "Removed link $d"
  fi
done
echo "To delete everything, including outputs: rm -rf \"$ROOT\""
