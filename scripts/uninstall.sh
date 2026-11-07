#!/usr/bin/env bash
# Remove every skill link that points into this clone (does not delete this folder or your outputs).
# Also removes an old link that pointed at the repository root.
# Usage: bash scripts/uninstall.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
for base in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  [[ -d "$base" ]] || continue
  for d in "$base"/*; do
    [[ -L "$d" ]] || continue
    target="$(cd "$d" 2>/dev/null && pwd -P)" || continue
    if [[ "$target" == "$ROOT" || "$target" == "$ROOT/skills/"* ]]; then
      rm "$d" && echo "Removed link $d"
    fi
  done
done
echo "To delete everything, including outputs: rm -rf \"$ROOT\""
