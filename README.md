# Artificial Intelligence Never Sleeps — Assembly Summer 2026 Submission

**Compo:** AI Coding (Vibe Demo)  
**Author:** ztothez  
**Length:** 122.5s @ 1080p60

This folder is the **Partyman/USB submission package**. The parent `DemoScene/` repo is unchanged; only runtime deliverables are copied here.

## Contents

```
submission/
├── entry/
│   run.sh, run.bat          # launch real-time player
│   readme.txt               # scene-style readme + AI disclosure
│   file_id.diz              # file_id block
│   screenshot.png           # 1920×1080 tagline-frame capture
├── source/
│   demo_player.py           # deterministic 60fps engine
│   timeline.py, ui_manifest.json
│   player_fx.py, player_motions.py, animate_raw.py
│   engine/                  # FFT, terminal, tunnel, post-process, renderer
│   visuals/raw/*.png        # 16× FLUX keyframes (16:9 narrative arc)
│   audio/playback.wav       # approved final live mix, 48 kHz mono PCM
│   audio/music.wav          # 3-act score source/FFT master
│   audio/narration.wav      # voice source master
├── capture.sh                 # deterministic final video capture builder
├── capture/
│   compo.mp4                # 1080p60 submission video (A/V muxed)
└── requirements.txt         # runtime deps only (pygame-ce, numpy, Pillow)
```

**Excluded intentionally:** `visuals/ui/`, `visuals/animated/`, `rough_cut.mp4`, build scripts, API keys, `.venv`, raw frame dumps.

## Run (jury / compo PC)

```bash
./entry/run.sh                         # audio-enabled fullscreen 1920×1080, ESC/Q quit
./entry/run.sh --windowed --resolution 960x540   # preview window
./entry/run.sh --headless --duration 5              # smoke test
```

Windows: `entry\run.bat`

First run creates `.venv`, upgrades pip, and installs compatible binary
packages from `requirements.txt` for the detected Python version.

## Video & audio

**Use this file for compo playback / upload:** `capture/compo.mp4`

| Property | Value |
|----------|-------|
| Video | 1920×1080, 60fps, **122.5s**, H.264 (from parallel frame dump) |
| Audio | AAC mono, 48 kHz — approved final narration + music mix |
| Live playback | Required `source/audio/playback.wav` at unity gain; same approved mix. The player stops with a clear error if it is missing—no quieter source-master fallback is used. |
| Capture builder | Also requires and muxes `source/audio/playback.wav`; no preserved-video, music-only, or other alternate audio route is used. |
| Loudness | **-15.61 LUFS** integrated, **-1.42 dBTP** |
| Source masters | `music.wav` (also used for FFT) and `narration.wav` |

**Submission video:** `capture/compo.mp4` (122.5s, A/V muxed).

The entry launchers pass `--audio` by default so the executable starts the
approved final mix. Running `source/demo_player.py` directly remains silent
unless `--audio` is passed. During live playback, the audio position is the
master clock and late visual frames are dropped to preserve synchronization.
Offline frame rendering remains deterministic.

**Do not substitute** other `compo*.mp4` variants from the dev repo — only `submission/capture/compo.mp4` is the submission mix.

## Verification (passed before pack)

```bash
./entry/run.sh --headless --resolution 1920x1080 --duration 5
python3 -m py_compile source/demo_player.py source/timeline.py source/engine/*.py
grep -r "VideoCapture\|cv2" source/   # expect no matches in live path
```

## Zip for upload

From parent directory. **Do not include `.venv`** — it is created on first `./entry/run.sh` run on the compo PC.

```bash
cd /path/to/DemoScene

# Remove local test venv if you ran smoke test inside submission/
rm -rf submission/.venv submission/**/__pycache__

zip -r ztothez_never_sleeps.zip submission/ \
  -x "submission/.venv/*" \
  -x "submission/*/__pycache__/*" \
  -x "submission/*/*/__pycache__/*" \
  -x "*.pyc"

unzip -l ztothez_never_sleeps.zip | grep -E '\.venv|__pycache__'   # should print nothing
ls -lh ztothez_never_sleeps.zip   # expect approximately 223.4 MiB
```

## AI tools (summary)

See `entry/readme.txt` for full disclosure. Code: Cursor/Claude; OpenAI Codex / GPT-5.5 for Phase 4 candidate implementation, optimization, deterministic validation and integration. Visuals: Together FLUX keyframes plus OpenAI / ChatGPT matched blackout frames. Voice: Together Orpheus. Music: Suno/Stable Audio 3. Human: direction, timeline, sync.
