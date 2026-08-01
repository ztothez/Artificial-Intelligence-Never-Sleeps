# Phase 3 Strict Non-Degradation Visual Pass

Candidate workspace: `/home/ztothez/Studio/experiments/DemoScene/phase3_candidate_20260726T131534Z/source-restored`
Report directory: `/home/ztothez/Studio/experiments/DemoScene/phase3_report_20260726T131534Z`
Protected archive SHA-256: `8c089cf0a5a954f9ba9237f29117163c80c82dcf288b9960f7a53152c9183392`
Baseline full timeline SHA-256: `d5f2e450ac7dc67628af5464e865505a1c4168718f9c0ca4e8d58ac2ca96a29b`
Baseline full hash A/B: PASS (`full_hash_A.json` == `full_hash_B.json`).
Final promotion result: no candidates accepted; candidate workspace restored to baseline hashes; no final capture created.

## Baseline Sampled Performance

- Original sampled baseline: avg `88.490 ms`, max `237.332 ms`, over-16.67 count mean `11.67` across 15 fixed frames.
- Fresh c4 control baseline: avg `96.042 ms`, max `259.928 ms`, over-16.67 count mean `12.67`.

## Candidate 1: evolution darken

Diff:
```diff
-        "darken": 0.68,
+        "darken": 0.76,
```
Recommendation: **REJECT**. Subtle lift only; sampled average/max render time regressed >2% and over-threshold count increased.
Changed timestamp hashes: `[10.0]`; unexpected timestamp changes: `[]`.
Full timeline hash A: `42c291b898d910e19e15ea3e7d9f41f598550416888c0b502c98ddc388ec18f9` (257.803s)
Full timeline hash B: `42c291b898d910e19e15ea3e7d9f41f598550416888c0b502c98ddc388ec18f9` (269.848s)
Determinism: `True`; differs from baseline: `True`.
Sampled performance: avg `96.447 ms`, max `263.027 ms`, over mean `12.33` vs baseline avg `88.490`, max `237.332`, over `11.67`.

| sec | segment | baseline hash | candidate hash | baseline p01/p05/p50/p95/p99 | candidate p01/p05/p50/p95/p99 | clip high % |
| --- | --- | --- | --- | --- | --- | --- |
| 10.0 | scene02_evolution | `499db09eec49f43fbf64ca1fa02751f52b7a5ad98da038ce196e596edc57965b` | `85b8e59822a4e01c75d409d7751406f08e9a101d90649cdab33ef9f2f9c13239` | 4.0722/4.9318/15.2258/61.3914/94.6132 | 4.1444/5.1444/16.5106/67.9662/104.9714 | luma 0.0, channel 0.0 |

Comparison images/video: `/home/ztothez/Studio/experiments/DemoScene/phase3_report_20260726T131534Z/comparisons/c1_evolution_darken`

## Candidate 2: archive darken

Diff:
```diff
-        "darken": 0.76,
+        "darken": 0.84,
```
Recommendation: **REJECT**. Subtle lift only; sampled average/max render time regressed >2% and over-threshold count increased.
Changed timestamp hashes: `[23.0]`; unexpected timestamp changes: `[]`.
Full timeline hash A: `4f0c2b1e8f85f47204ff4668eea025c2368f5885ad8f29c55da6b7cf0bc77b2c` (255.585s)
Full timeline hash B: `4f0c2b1e8f85f47204ff4668eea025c2368f5885ad8f29c55da6b7cf0bc77b2c` (244.182s)
Determinism: `True`; differs from baseline: `True`.
Sampled performance: avg `103.297 ms`, max `283.610 ms`, over mean `13.33` vs baseline avg `88.490`, max `237.332`, over `11.67`.

| sec | segment | baseline hash | candidate hash | baseline p01/p05/p50/p95/p99 | candidate p01/p05/p50/p95/p99 | clip high % |
| --- | --- | --- | --- | --- | --- | --- |
| 23.0 | scene03_archive | `ba21457495757b899878f7e2fda577e2d8df127ee2ad7600391d982dd741b2dc` | `9583d6a3223272eec34fe8325abd9f17a73ceefb4e142fff94594824ec49cc6f` | 4.8596/6.7192/16.4384/48.6682/69.7496 | 5.0722/6.9318/17.7232/53.1708/76.592 | luma 0.0, channel 0.0 |

Comparison images/video: `/home/ztothez/Studio/experiments/DemoScene/phase3_report_20260726T131534Z/comparisons/c2_archive_darken`

## Candidate 3: plasma colour

Diff:
```diff
-    r = (wave * (180 + 70 * hue_shift)).astype(np.uint8)
-    g = (wave * (175 + 90 * (1 - hue_shift))).astype(np.uint8)
+    r = (wave * (185 + 75 * hue_shift)).astype(np.uint8)
+    g = (wave * (168 + 85 * (1 - hue_shift))).astype(np.uint8)
```
Recommendation: **REJECT**. Plasma luma p50/p95/p99 moved slightly down at both test frames; not a clear visual upgrade.
Changed timestamp hashes: `[54.0, 60.0]`; unexpected timestamp changes: `[]`.
Full timeline hash A: `6a32e674d228868a6fdee8bede379f43f46d74d6385f93ece31f359d73855a3e` (244.432s)
Full timeline hash B: `6a32e674d228868a6fdee8bede379f43f46d74d6385f93ece31f359d73855a3e` (244.632s)
Determinism: `True`; differs from baseline: `True`.
Sampled performance: avg `95.699 ms`, max `260.998 ms`, over mean `12.33` vs baseline avg `88.490`, max `237.332`, over `11.67`.

| sec | segment | baseline hash | candidate hash | baseline p01/p05/p50/p95/p99 | candidate p01/p05/p50/p95/p99 | clip high % |
| --- | --- | --- | --- | --- | --- | --- |
| 54.0 | scene08a_inference | `56e5d7faec3c28fe71f7862b3da632f310cb00ccb8671ffd251b40e23cf5c99b` | `f2263ab366b3f1fd332c3660654168a64b064fd9c21fe230cf779ec69520199a` | 11.008/16.2206/56.5948/119.968/142.1948 | 11.008/16.2206/56.083/118.935/141.251 | luma 0.0, channel 0.0 |
| 60.0 | scene08b_graph | `7568774eeb4f2692cb5f35fc9e6f05d02365604e10d212895b80796e255fd45e` | `b0cd9490f169f2e423c99d33e4147e30aee6239002a7ce189bb2ba1182de0ba5` | 14.361/17.2206/45.3048/130.3416/161.6172 | 14.361/17.1484/44.8704/129.5294/161.188 | luma 0.0, channel 0.0 |

Comparison images/video: `/home/ztothez/Studio/experiments/DemoScene/phase3_report_20260726T131534Z/comparisons/c3_plasma_colour`

## Candidate 4: terminal palette

Diff:
```diff
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
Recommendation: **REJECT**. Terminal p99/readability improved without clipping, but fresh sampled over-threshold count still increased by one; strict rule preserves baseline.
Changed timestamp hashes: `[32.4, 48.0, 99.0, 118.0]`; unexpected timestamp changes: `[]`.
Full timeline hash A: `d27bd9ce4c586734b6569cca1c315925fcc7cf47e433b6ae84791e0a17c1ed2f` (243.877s)
Full timeline hash B: `d27bd9ce4c586734b6569cca1c315925fcc7cf47e433b6ae84791e0a17c1ed2f` (240.055s)
Determinism: `True`; differs from baseline: `True`.
Sampled performance: avg `95.347 ms`, max `259.602 ms`, over mean `12.00` vs baseline avg `88.490`, max `237.332`, over `11.67`.
Fresh c4 performance: avg `95.750 ms`, max `258.563 ms`, over mean `13.00` vs fresh baseline avg `96.042`, max `259.928`, over `12.67`.

| sec | segment | baseline hash | candidate hash | baseline p01/p05/p50/p95/p99 | candidate p01/p05/p50/p95/p99 | clip high % |
| --- | --- | --- | --- | --- | --- | --- |
| 32.4 | ui_access_denied | `911e3181a54b2293165a2539e897b4fc617e22f1c07053ebec270c3ef445ad83` | `65aa2fd3f0d4fae6b3ae743481a569f064f439c2711fe51fed7dd04b7e532e84` | 10.13/12.3426/17.55/23.4726/75.1276 | 10.13/12.3426/17.55/23.4726/80.354 | luma 0.0, channel 0.0 |
| 48.0 | ui_deploy_terminal | `9487a1d773d88f139e9019d6bf9e4b79092ec98e16bdc5a70cefe15031bf05e7` | `433005a39af48074c001f78bd19c85bed8d9b9b35a8fa0f149441e1d298bed7b` | 6.1444/7.1444/10.2888/13.361/96.7802 | 6.1444/7.1444/10.2888/13.361/104.5648 | luma 0.0, channel 0.0 |
| 99.0 | ui_prompt_guardrails | `f325d040c191e24896bbc913cfb4f81819069038fdef21bf1db1faa726f5f15f` | `b22019196ddcedc1a7bc7d275b2a8e344c0e9448a70e4c438090bae7db00b45f` | 6.1444/7.1444/10.2888/13.361/20.024 | 6.1444/7.1444/10.2888/13.361/20.5146 | luma 0.0, channel 0.0 |
| 118.0 | ui_tagline | `522833d9eeef5f2aef6175cb1c954949f09bb1e2361105df39a26c14d88fc7d4` | `1cd80ef3cf951fd0b4465cb03dabf31805c3ae7d02388679b009d3ce0421b56c` | 6.1444/7.1444/10.2888/13.361/124.6454 | 6.1444/7.1444/10.2888/13.361/133.0088 | luma 0.0, channel 0.0 |

Comparison images/video: `/home/ztothez/Studio/experiments/DemoScene/phase3_report_20260726T131534Z/comparisons/c4_palette`

