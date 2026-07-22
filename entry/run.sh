#!/usr/bin/env bash
# Run the real-time Vibe Demo player (Assembly Summer 2026)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d "$ROOT/.venv" ]]; then
  python3 -m venv "$ROOT/.venv"
fi

"$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"

exec "$ROOT/.venv/bin/python" "$ROOT/source/demo_player.py" "$@"
