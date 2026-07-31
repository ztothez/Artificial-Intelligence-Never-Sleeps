#!/usr/bin/env bash
# Run the real-time Vibe Demo player (Assembly Summer 2026)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PLAYBACK_MASTER="$ROOT/source/audio/playback.wav"
if [[ ! -f "$PLAYBACK_MASTER" ]]; then
  echo "ERROR: required live audio master is missing:" >&2
  echo "  $PLAYBACK_MASTER" >&2
  echo "Re-extract the complete submission package. No quiet fallback will be used." >&2
  exit 1
fi

if [[ ! -d "$ROOT/.venv" ]]; then
  python3 -m venv "$ROOT/.venv"
fi

"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/python" -m pip uninstall -y pygame >/dev/null 2>&1 || true
"$ROOT/.venv/bin/python" -m pip install --upgrade --prefer-binary -r "$ROOT/requirements.txt"

exec "$ROOT/.venv/bin/python" "$ROOT/source/demo_player.py" --audio "$@"
