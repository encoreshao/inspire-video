#!/usr/bin/env bash
# Make this copy of InspireVideo ready to run. Safe to run at the start of every session: it does nothing when
# everything is already in place.
#
# A plugin install lives in a versioned folder that is replaced on every update, so nothing a user makes may stay in
# it. For such a copy this script links output/ and voices/ to the data folder, which survives updates and is shared
# by every Claude Code profile (~/.claude, ~/.claude-loopx, any CLAUDE_CONFIG_DIR). A git clone keeps its own output/
# and voices/, as before.
#
# Usage: bash scripts/prepare.sh [--no-deps]
# Env:   INSPIRE_VIDEO_HOME  data folder (default: ~/.inspire-video for a plugin copy, the clone itself otherwise)
set -euo pipefail

ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
DEPS=1
for arg in "$@"; do
  case "$arg" in
    --no-deps) DEPS=0 ;;
    -h|--help) sed -n '2,12p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "Usage: $0 [--no-deps]" >&2; exit 2 ;;
  esac
done

PLUGIN_COPY=0
case "$ROOT" in */plugins/cache/*) PLUGIN_COPY=1 ;; esac

if [[ -n "${INSPIRE_VIDEO_HOME:-}" ]]; then
  DATA="$INSPIRE_VIDEO_HOME"
elif [[ $PLUGIN_COPY -eq 1 ]]; then
  DATA="$HOME/.inspire-video"
else
  DATA="$ROOT"
fi
mkdir -p "$DATA"
DATA="$(cd -P "$DATA" && pwd -P)"

link_data() {    # link_data <folder>: make ROOT/<folder> a link to DATA/<folder>, keeping anything already in it
  local name="$1" here="$ROOT/$1" there="$DATA/$1"
  mkdir -p "$there"
  if [[ -L "$here" ]]; then
    ln -sfn "$there" "$here"
    return
  fi
  if [[ -d "$here" ]]; then
    cp -Rn "$here/." "$there/" 2>/dev/null || true     # never overwrites a file in the data folder
    rm -rf "$here"
  fi
  ln -s "$there" "$here"
  echo "Linked $name -> $there"
}

if [[ "$DATA" != "$ROOT" ]]; then
  link_data output
  link_data voices
fi
mkdir -p "$ROOT/output/projects" "$ROOT/output/final" "$ROOT/output/cache"

if [[ $DEPS -eq 1 ]]; then
  if ! python3 -c 'import yaml, pydantic, faster_whisper, jsonschema, yt_dlp' >/dev/null 2>&1; then
    echo "Installing Python deps..."
    if [[ $PLUGIN_COPY -eq 1 ]]; then
      python3 -m pip install "$ROOT"        # not editable: this folder is replaced on the next plugin update
    else
      python3 -m pip install -e "$ROOT"
    fi
  fi
  if [[ ! -d "$ROOT/video/node_modules/remotion" ]]; then
    echo "Installing Remotion deps..."
    (cd "$ROOT/video" && npm install --no-audit --no-fund)
  fi
fi

echo "Engine: $ROOT"
echo "Data:   $DATA (videos are written to $DATA/output/final)"
