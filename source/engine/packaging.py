"""Scene release packaging — file_id.diz, readme, ffmpeg hints."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY_DIR = ROOT / "entry"


def write_file_id_diz() -> Path:
    path = ENTRY_DIR / "file_id.diz"
    path.write_text(
        "artificialintelligenceneversleeps - vibe demo - assembly summer 2026\n"
        "by ztothez - python/pygame real-time - 1920x1080@60\n",
        encoding="ascii",
    )
    return path


def write_readme() -> Path:
    path = ENTRY_DIR / "readme.txt"
    body = """\
================================================================================
  ARTIFICIAL INTELLIGENCE NEVER SLEEPS
  Assembly Summer 2026 — AI Coding (Vibe Demo)
  Handle: ztothez
================================================================================

RUN
---
  Linux/macOS:  ./entry/run.sh
  Windows:      entry\\run.bat

  Controls: ESC or Q to quit. Mouse cursor hidden during playback.

REQUIREMENTS
------------
  Python 3.10+
  pip install -r requirements.txt

  Assets: source/visuals/raw/*.png, source/audio/playback.wav
          (music.wav and narration.wav are retained as source masters)

CAPTURE (1080p60)
-----------------
  Live: record ./entry/run.sh fullscreen @ 60fps

  Offline final capture:
    ./capture.sh
    # writes capture/compo.mp4

HARDWARE TESTED
---------------
  Dev:  Intel UHD 630, Linux, Python 3.12
  Target compo: AMD Ryzen 7 9800X3D, RTX 5070 12 GB, Windows 11 / Ubuntu 26.04 LTS

ENGINE
------
  - Pre-calculated NumPy STFT → sub_bass + treble curves
  - Procedural terminal UI (JetBrains Mono / IBM Plex Mono fallback)
  - NumPy polar tunnel rasterizer (inference + binary textures)
  - Subtle global post-process: scanlines, vignette, cue accents
  - Final live mix: -15.61 LUFS integrated, -1.42 dB true peak
  - Audio-master clock drops late visual frames to preserve synchronization
  - Deterministic offline frame clock @ 60fps (frame_idx / FPS)

AI TOOLS USED
-------------
  Code:     Cursor / Claude — engine, player, timeline, packaging
  Visuals:  Together FLUX.1-schnell / FLUX.1.1-pro (keyframes)
  Voice:    Together Orpheus TTS + ffmpeg robot post-FX
  Music:    Suno / Stable Audio 3 (Hugging Face) via generate_music.py

  Human:    Direction, timeline, sync, copyright review

LICENSE
-------
  Original script and code. AI imagery/voice per tool ToS.
  No copyrighted characters or fan art.
================================================================================
"""
    path.write_text(body, encoding="utf-8")
    return path


def ffmpeg_assemble_command(frames_dir: Path, out_file: Path) -> str:
    return (
        f'ffmpeg -y -framerate 60 -i "{frames_dir}/frame_%06d.png" '
        f'-c:v libx264 -pix_fmt yuv420p -crf 15 -preset slow '
        f'"{out_file}"'
    )


if __name__ == "__main__":
    write_file_id_diz()
    write_readme()
    print("Wrote entry/file_id.diz and entry/readme.txt")
