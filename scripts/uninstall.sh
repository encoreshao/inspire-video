#!/usr/bin/env bash
# Remove every skill link that points into this clone (does not delete this folder or your outputs).
# Also removes an old link that pointed at the repository root.
# Looks in ~/.claude/skills, in $CLAUDE_CONFIG_DIR/skills when that variable is set, and in ~/.agents/skills.
# A plugin install is removed with /plugin uninstall inspire-video@inspire-video instead.
# Usage: bash scripts/uninstall.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
# Find every link first and remove them afterwards: a link may pass through another link that is also removed
# (an old Codex link through the Claude Code root link), and could no longer be resolved once that one is gone.
found=()
for base in "$HOME/.claude/skills" ${CLAUDE_CONFIG_DIR:+"$CLAUDE_CONFIG_DIR/skills"} "$HOME/.agents/skills"; do
  [[ -d "$base" ]] || continue
  for d in "$base"/*; do
    [[ -L "$d" ]] || continue
    target="$(cd "$d" 2>/dev/null && pwd -P)" || continue
    if [[ "$target" == "$ROOT" || "$target" == "$ROOT/skills/"* ]]; then
      found+=("$d")
    fi
  done
done
for d in ${found[@]+"${found[@]}"}; do
  [[ -L "$d" ]] && rm "$d" && echo "Removed link $d"
done
echo "To delete everything, including outputs: rm -rf \"$ROOT\""
