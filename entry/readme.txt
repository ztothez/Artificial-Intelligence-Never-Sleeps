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

  Assets: source/visuals/raw/*.png, source/audio/playback.wav
          (music.wav and narration.wav are retained as source masters)
          playback.wav is required for live playback; there is no quiet fallback

CAPTURE (1080p60)
-----------------
  Live: record ./entry/run.sh fullscreen @ 60fps

  Offline final capture:
    ./capture.sh
    # writes capture/compo.mp4 using required source/audio/playback.wav

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
            OpenAI Codex / GPT-5.5 — Phase 4 candidate implementation,
            optimization, deterministic validation and integration
  Visuals:  Together FLUX.1-schnell / FLUX.1.1-pro (keyframes)
            OpenAI / ChatGPT image generation — matched city lights-on and
            total-power-failure frames:
              source/visuals/raw/scene11c_blackout_01_city_lights_on.png
              SHA-256 a6f65478c765cc245a3266a8f36c492703d9e0153bb116438883d85547b1cca7
              source/visuals/raw/scene11d_blackout_02_total_power_failure.png
              SHA-256 a7464f12318afb4995c2424ad744e8bdde913ddaf29a7cdcb14c6eef2592e0a6
            Exact blackout generation prompts were not retained.
  Voice:    Together Orpheus TTS + ffmpeg robot post-FX
  Music:    Suno / Stable Audio 3 (Hugging Face) via generate_music.py

  Human:    Direction, timeline, sync, copyright review

LICENSE
-------
  Original script and code. AI imagery/voice per tool ToS.
  No copyrighted characters or fan art.
================================================================================
