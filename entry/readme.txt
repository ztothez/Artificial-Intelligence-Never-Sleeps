================================================================================
  ARTIFICIAL INTELLIGENCE NEVER SLEEPS
  Assembly Summer 2026 — AI Coding (Vibe Demo)
  Handle: ztothez
================================================================================

RUN
---
  Linux/macOS:  ./entry/run.sh
  Windows:      entry\run.bat

  Controls: ESC or Q to quit. Mouse cursor hidden during playback.

REQUIREMENTS
------------
  Python 3.10+
  pip install -r requirements.txt

  Assets: source/visuals/raw/*.png, source/audio/music.wav, narration.wav

CAPTURE (1080p60)
-----------------
  Live: record ./entry/run.sh fullscreen @ 60fps

  Offline frame dump (Intel UHD 630 friendly):
    ./entry/run.sh --dump-frames
    # ffmpeg command printed at end → capture/compo.mp4

HARDWARE TESTED
---------------
  Dev:  Intel UHD 630, Linux, Python 3.12
  Target compo: AMD Ryzen 9 9950X3D, RTX 5090, Windows 11 / Ubuntu 26.04 LTS

ENGINE
------
  - Pre-calculated STFT (scipy/numpy) → sub_bass + treble curves
  - Procedural terminal UI (JetBrains Mono / IBM Plex Mono fallback)
  - NumPy polar tunnel rasterizer (inference + binary textures)
  - Global CRT post-process: scanlines, vignette, bass-reactive shake
  - Deterministic frame clock @ 60fps (frame_idx / FPS)

AI TOOLS USED
-------------
  Code:     Cursor / Claude — engine, player, timeline, packaging
  Visuals:  Together FLUX.1-schnell / FLUX.1.1-pro (keyframes)
  Voice:    Together Orpheus TTS + ffmpeg robot post-FX
  Music:    Stable Audio 3 (Hugging Face) via generate_music.py

  Human:    Direction, timeline, sync, copyright review

LICENSE
-------
  Original script and code. AI imagery/voice per tool ToS.
  No copyrighted characters or fan art.
================================================================================
