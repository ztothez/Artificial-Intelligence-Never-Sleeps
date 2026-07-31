#!/usr/bin/env bash
# Build the final deterministic 1080p60 H.264/AAC capture using the required
# approved live playback master.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

CAPTURE_DIR="$ROOT/capture"
FRAMES_DIR="$CAPTURE_DIR/raw_frames"
FINAL="$CAPTURE_DIR/compo.mp4"
VIDEO_TMP="$CAPTURE_DIR/compo_video.mp4"
NEW="$CAPTURE_DIR/compo_new.mp4"
PLAYBACK_MASTER="$ROOT/source/audio/playback.wav"
WORKERS="${ZTTZ_CAPTURE_WORKERS:-8}"

if [[ ! -f "$PLAYBACK_MASTER" ]]; then
  echo "ERROR: required audio master is missing:" >&2
  echo "  $PLAYBACK_MASTER" >&2
  echo "Re-extract the complete submission package. No alternate audio will be used." >&2
  exit 1
fi

mkdir -p "$CAPTURE_DIR"

if [[ ! "$WORKERS" =~ ^[0-9]+$ ]] || [[ "$WORKERS" -lt 1 ]]; then
  echo "ZTTZ_CAPTURE_WORKERS must be a positive integer; got '$WORKERS'" >&2
  exit 1
fi

if [[ ! -d "$ROOT/.venv" ]]; then
  python3 -m venv "$ROOT/.venv"
fi
"$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"
PY="$ROOT/.venv/bin/python"

EXPECTED_FRAMES="$("$PY" - <<'PY'
import sys
sys.path.insert(0, "source")
from timeline import FPS, total_duration
print(int(round(total_duration() * FPS)))
PY
)"

rm -rf "$FRAMES_DIR"
mkdir -p "$FRAMES_DIR"

PYTHONDONTWRITEBYTECODE=1 SDL_VIDEODRIVER=dummy "$PY" "$ROOT/source/parallel_dump.py" \
  --workers "$WORKERS" \
  --resolution 1920x1080 \
  --dump-dir "$FRAMES_DIR"

FRAME_COUNT="$(find "$FRAMES_DIR" -maxdepth 1 -name 'frame_*.png' | wc -l)"
if [[ "$FRAME_COUNT" -ne "$EXPECTED_FRAMES" ]]; then
  echo "Expected $EXPECTED_FRAMES rendered frames, found $FRAME_COUNT" >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 "$PY" - "$FRAMES_DIR" "$EXPECTED_FRAMES" <<'PY'
import sys
from pathlib import Path

import pygame

frames_dir = Path(sys.argv[1])
expected = int(sys.argv[2])
pygame.init()
bad = []
for idx in range(expected):
    path = frames_dir / f"frame_{idx:06d}.png"
    if not path.exists():
        bad.append(f"missing:{path.name}")
        continue
    image = pygame.image.load(str(path))
    if image.get_size() != (1920, 1080):
        bad.append(f"size:{path.name}:{image.get_size()}")
pygame.quit()
if bad:
    raise SystemExit("frame validation failed: " + ", ".join(bad[:20]))
print(f"frame validation passed: {expected} complete 1920x1080 PNG frames")
PY

ffmpeg -hide_banner -loglevel error -y \
  -framerate 60 -i "$FRAMES_DIR/frame_%06d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 15 -preset slow "$VIDEO_TMP"

ffmpeg -hide_banner -loglevel error -y \
  -i "$VIDEO_TMP" -i "$PLAYBACK_MASTER" \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest "$NEW"

PYTHONDONTWRITEBYTECODE=1 "$PY" - "$NEW" <<'PY'
import json
import subprocess
import sys

path = sys.argv[1]
data = json.loads(
    subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate,sample_rate,channels",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            path,
        ],
        text=True,
    )
)
streams = data.get("streams", [])
video = next((s for s in streams if s.get("codec_type") == "video"), None)
audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
checks = {
    "h264": video and video.get("codec_name") == "h264",
    "1920x1080": video and video.get("width") == 1920 and video.get("height") == 1080,
    "fps_60": video and video.get("r_frame_rate") == "60/1",
    "yuv420p": video and video.get("pix_fmt") == "yuv420p",
    "aac": audio and audio.get("codec_name") == "aac",
    "audio_48k": audio and audio.get("sample_rate") == "48000",
    "audio_mono": audio and audio.get("channels") == 1,
    "duration": abs(float(data.get("format", {}).get("duration", 0.0)) - 122.5) <= 1.0 / 60.0,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit(f"capture validation failed: {failed}")
print("stream validation passed")
PY

mv -f "$NEW" "$FINAL"
rm -f "$VIDEO_TMP"
echo "Wrote $FINAL"
