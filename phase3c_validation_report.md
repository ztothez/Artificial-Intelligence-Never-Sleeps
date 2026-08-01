# Phase 3C Terminal Palette Candidate Validation

Status: **PASS**

## Scope

- Modified source file: `source/engine/palette.py`
- No C1/C2/C3 changes applied.
- Restored baseline archive was not overwritten.
- Protected baseline archive SHA-256: `8c089cf0a5a954f9ba9237f29117163c80c82dcf288b9960f7a53152c9183392`

## Exact Palette Changes

- `ICE_BLUE = (74, 124, 255)` -> `ICE_BLUE = (82, 136, 255)`
- `TERMINAL_GREEN = (46, 204, 113)` -> `TERMINAL_GREEN = (52, 220, 120)`
- `WARNING_AMBER = (230, 160, 32)` -> `WARNING_AMBER = (240, 170, 36)`
- `ALERT_RED = (224, 32, 32)` -> `ALERT_RED = (240, 40, 44)`
- `ARCHIVE_GREY = (138, 143, 152)` -> `ARCHIVE_GREY = (154, 160, 170)`
- `WHITE = (240, 240, 245)` -> `WHITE = (248, 248, 252)`
- `VOID` and `COLD_STEEL` unchanged.

## Exact Source Diff

```diff
--- /home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/baseline_palette_from_zip.py	2026-07-26 17:44:24.607657156 +0300
+++ /home/ztothez/Studio/experiments/DemoScene/phase3c_candidate_20260726T143158Z/source-restored/source/engine/palette.py	2026-07-26 17:43:46.594755375 +0300
@@ -4,9 +4,9 @@
 
 VOID = (8, 8, 12)
 COLD_STEEL = (26, 35, 50)
-ICE_BLUE = (74, 124, 255)
-TERMINAL_GREEN = (46, 204, 113)
-WARNING_AMBER = (230, 160, 32)
-ALERT_RED = (224, 32, 32)
-ARCHIVE_GREY = (138, 143, 152)
-WHITE = (240, 240, 245)
+ICE_BLUE = (82, 136, 255)
+TERMINAL_GREEN = (52, 220, 120)
+WARNING_AMBER = (240, 170, 36)
+ALERT_RED = (240, 40, 44)
+ARCHIVE_GREY = (154, 160, 170)
+WHITE = (248, 248, 252)
```

## Determinism

- Baseline run A: `d5f2e450ac7dc67628af5464e865505a1c4168718f9c0ca4e8d58ac2ca96a29b`
- Baseline run B: `d5f2e450ac7dc67628af5464e865505a1c4168718f9c0ca4e8d58ac2ca96a29b`
- Baseline A/B match: `True`
- Enhanced run A: `d27bd9ce4c586734b6569cca1c315925fcc7cf47e433b6ae84791e0a17c1ed2f`
- Enhanced run B: `d27bd9ce4c586734b6569cca1c315925fcc7cf47e433b6ae84791e0a17c1ed2f`
- Enhanced A/B match: `True`
- Enhanced differs from baseline as expected: `True`
- Existing deterministic validation harness also passed twice for baseline and enhanced: `e0b35f94748b4656cbc23fce1ade8cb0efdbac183c51095836319734a204669f`.

## Changed Timestamps

- Changed seconds: `[32.4, 48.0, 99.0, 118.0]`
- Unexpected changed seconds: `[]`
- Confirmed unchanged at representative non-terminal/raw/tunnel/black/eye points: `2.0`, `10.0`, `23.0`, `54.0`, `60.0`, `77.0`, `82.5`, `87.5`, `92.5`, `106.0`, `110.5`.

## Visual Metrics

| sec | segment | baseline hash | enhanced hash | baseline mean/median/p95/p99/min/max | enhanced mean/median/p95/p99/min/max | clipped black/white |
| --- | --- | --- | --- | --- | --- | --- |
| 32.4 | ui_access_denied | `911e3181a54b2293165a2539e897b4fc617e22f1c07053ebec270c3ef445ad83` | `65aa2fd3f0d4fae6b3ae743481a569f064f439c2711fe51fed7dd04b7e532e84` | 18.626211/17.549999/23.472601/75.127602/10.13/118.959206 | 18.703426/17.549999/23.472601/80.353966/10.13/127.322601 | 0/0 |
| 48.0 | ui_deploy_terminal | `9487a1d773d88f139e9019d6bf9e4b79092ec98e16bdc5a70cefe15031bf05e7` | `433005a39af48074c001f78bd19c85bed8d9b9b35a8fa0f149441e1d298bed7b` | 11.700194/10.2888/13.360999/96.780197/6.1444/163.288803 | 11.828538/10.2888/13.360999/104.564796/6.1444/169.072205 | 0/0 |
| 99.0 | ui_prompt_guardrails | `f325d040c191e24896bbc913cfb4f81819069038fdef21bf1db1faa726f5f15f` | `b22019196ddcedc1a7bc7d275b2a8e344c0e9448a70e4c438090bae7db00b45f` | 10.837096/10.2888/13.360999/20.023998/6.1444/136.729202 | 10.894031/10.2888/13.360999/20.514599/6.1444/147.310394 | 0/0 |
| 118.0 | ui_tagline | `522833d9eeef5f2aef6175cb1c954949f09bb1e2361105df39a26c14d88fc7d4` | `1cd80ef3cf951fd0b4465cb03dabf31805c3ae7d02388679b009d3ce0421b56c` | 12.354878/10.2888/13.360999/124.645401/6.1444/235.722 | 12.363863/10.2888/13.360999/133.008804/6.1444/235.722 | 0/0 |

Visual confirmation: terminal text and blue/green/red/grey/white accents are brighter and clearer; dark backgrounds, glyph shapes, scanlines, and vignette remain visually unchanged. No highlight clipping was introduced.

A/B comparison assets:
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/comparisons/side_by_side/032p400_ui_access_denied_baseline_enhanced.png`
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/comparisons/side_by_side/048p000_ui_deploy_terminal_baseline_enhanced.png`
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/comparisons/side_by_side/099p000_ui_prompt_guardrails_baseline_enhanced.png`
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/comparisons/side_by_side/118p000_ui_tagline_baseline_enhanced.png`
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/comparisons/absolute_diff/032p400_ui_access_denied_absolute_diff.png`
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/comparisons/absolute_diff/048p000_ui_deploy_terminal_absolute_diff.png`
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/comparisons/absolute_diff/099p000_ui_prompt_guardrails_absolute_diff.png`
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/comparisons/absolute_diff/118p000_ui_tagline_absolute_diff.png`

## Continuous Performance

Warmed 10-second, 600-frame uncapped render window, order: baseline, enhanced, enhanced, baseline. Startup/loading excluded.
- baseline: avg `29.761623 ms`, median `28.828948 ms`, p95 `55.972947 ms`, p99 `77.979529 ms`, max `92.421994 ms`, achieved `33.605018 fps`, dropped/over-16.67 `485.50`
- enhanced: avg `29.404370 ms`, median `28.556306 ms`, p95 `55.056394 ms`, p99 `76.436973 ms`, max `85.633048 ms`, achieved `34.007235 fps`, dropped/over-16.67 `479.00`

The local/headless environment does not reach real-time 60fps for either build; this is pre-existing baseline behavior. The palette candidate is neutral-to-slightly-better in the warmed comparison and adds no render operations.

## Timeline And Integrity

- Timeline duration: `122.5` seconds
- Scene order window: `['scene08a_inference', 'scene08b_graph', 'scene07_hands', 'scene09_pov', 'scene08_tunnel', 'scene10_threshold_awareness', 'scene11a_statue', 'scene11b_binary']`
- Asset count loaded: `18`
- Asset changes: `[]`
- Audio changes: `[]`
- Font changes: `[]`
- Dependency changes: `[]`
- Final integrity changed files: `['capture/compo.mp4', 'entry/screenshot.png', 'source/engine/palette.py']`
- Source diff only palette: `True`

Final project hash manifest:
- `/home/ztothez/Studio/experiments/DemoScene/phase3c_report_20260726T143158Z/phase3c_final_project_sha256_manifest.txt`

## Capture

- Render host: `root@134.199.206.58`
- Remote frame dump: `7350` frames, `212.5s`, `34.6` render-fps effective, 20 workers.
- Remote frame validation: `7350 complete 1920x1080 PNG frames`.
- Remote stream validation: passed.
- Capture SHA-256: `ff52d8478eb8404269d9ebc422155ef0ebf32bea23ab6ea023aff953875538ce`
- Capture log SHA-256: `b65387fe975d2d2c4d70d59375eb594152ff2ec9157e51e5ce1c7e0cd4b71d81`
- Video: `h264`, `1920x1080`, `yuv420p`, `60/1`, duration `122.500000`
- Audio: `aac`, `48000` Hz, channels `1`, duration `122.500000`
- Container duration: `122.500000`, size `178920447` bytes

## Deliverables

- Candidate archive: `/home/ztothez/Studio/experiments/DemoScene/phase3c_terminal_palette_candidate.zip`
- Candidate archive SHA-256: `145a248622a1a67598fa2e4fd557765150ffb3d84b245e5bbbf43b47eb085b1b`
- Validation report: `/home/ztothez/Studio/experiments/DemoScene/phase3c_validation_report.md`
- Final capture: `/home/ztothez/Studio/experiments/DemoScene/phase3c_candidate_20260726T143158Z/source-restored/capture/compo.mp4`
- Final screenshot SHA-256: `36285c1ad3bb8a8d7070821957d94cfbc8995ca2422dbe89007739aac5afc9fa`

## Baseline Safety

- Restored baseline archive `/home/ztothez/Studio/experiments/DemoScene/ztothez_never_sleeps_source_restored.zip` was not overwritten.
- Candidate package was written separately as `phase3c_terminal_palette_candidate.zip`.
