# Artificial Intelligence Never Sleeps — Assembly Summer 2026 Submission

**Compo:** AI Coding (Vibe Demo)  
**Author:** ztothez  
**Length:** 2:00 @ 1080p60

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
│   audio/music.wav          # 3-act score (Stable Audio 3)
│   audio/narration.wav      # Together Orpheus TTS + robot post-FX
├── capture/
│   compo.mp4                # 1080p60 submission video (A/V muxed)
└── requirements.txt         # runtime deps only (pygame, numpy, scipy)
```

**Excluded intentionally:** `visuals/ui/`, `visuals/animated/`, `rough_cut.mp4`, build scripts, API keys, `.venv`, raw frame dumps.

## Run (jury / compo PC)

```bash
./entry/run.sh                         # fullscreen 1920×1080, ESC/Q quit
./entry/run.sh --windowed --resolution 960x540   # preview window
./entry/run.sh --headless --no-audio --duration 5   # smoke test
```

Windows: `entry\run.bat`

First run creates `.venv` and installs `requirements.txt`.

## Video & audio

**Use this file for compo playback / upload:** `capture/compo.mp4`

| Property | Value |
|----------|-------|
| Video | 1920×1080, 60fps, **122.5s**, H.264 (from parallel frame dump) |
| Audio | AAC — remuxed narration + music (matched to Telegram/backup original) |
| Narration | `source/audio/narration.wav` @ **1.0×** speed, volume **2.0×** in mix (clearer over bed) |
| Music | `source/audio/music.wav` @ **1.0×**, volume **0.22×** (unchanged) |
| Mastering | +16 dB pre-limiter, soft limiter **-1 dBFS** ceiling (Telegram limited loudness) |

**Submission video:** `capture/compo.mp4` (122.5s, A/V muxed). Dev remux: `./capture/mux_compo.sh 122.5`.

> Note: older README text saying narration @ **2.30×** referred to DAW authoring of the export, **not** an ffmpeg `atempo` step on `narration.wav`. Applying `atempo=2.0,atempo=1.15` makes chipmunk audio — do not use that.

The live player runs **silent** (`--no-audio` for capture). Audio exists only in `compo.mp4` for jury screening. Executable timeline must still match the video: deterministic `frame_idx` clock, no MP4 playback in player.

**Do not substitute** other `compo*.mp4` variants from the dev repo — only `submission/capture/compo.mp4` is the submission mix.

## Verification (passed before pack)

```bash
./entry/run.sh --headless --no-audio --resolution 1920x1080 --duration 5
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
ls -lh ztothez_never_sleeps.zip   # expect ~550–600 MB, not ~800 MB+
```

## AI tools (summary)

See `entry/readme.txt` for full disclosure. Code: Cursor/Claude. Visuals: Together FLUX.2-dev. Voice: Together Orpheus. Music: Stable Audio 3. Human: direction, timeline, sync.
