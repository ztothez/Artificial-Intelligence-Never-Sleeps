# Visual Enhancement Report — Code-Locked Source Audit

The restored archive was analyzed without modifying the uploaded ZIP or production source.

The Phase 3 draft must not be implemented as written. Several assumed values and tests do not match the restored source, and blindly following it would likely make the image darker and less readable.

## 1. Verified baseline

The capture itself is valid:

* 1920×1080.
* H.264, YUV420p.
* 60/1 fps.
* 7,350 frames.
* 122.5 seconds.
* AAC 48 kHz mono.
* Approximately 11.5 Mbps video.
* Timeline contains 22 segments.

Relevant audited files:

* [post_process.py](sandbox:/workspace/scratch/1bc26ba56bc9/analysis_workspace/source-restored/source/engine/post_process.py)
* [player_fx.py](sandbox:/workspace/scratch/1bc26ba56bc9/analysis_workspace/source-restored/source/player_fx.py)
* [palette.py](sandbox:/workspace/scratch/1bc26ba56bc9/analysis_workspace/source-restored/source/engine/palette.py)
* [timeline.py](sandbox:/workspace/scratch/1bc26ba56bc9/analysis_workspace/source-restored/source/timeline.py)

### Phase 3 prompt mismatches

| Draft assumption                   | Restored source                            |
| ---------------------------------- | ------------------------------------------ |
| `SCANLINE_DIM = 0.025`             | Already `0.040`                            |
| `VIGNETTE_STRENGTH = 0.4` constant | No such constant                           |
| `VIGNETTE_FALLOFF = 2.0`           | No such constant                           |
| `CONTRAST_BOOST = 1.0`             | Does not exist                             |
| `BLACK_FLOOR = 0.02`               | Does not exist                             |
| 16 raw scene images                | 18 scene images                            |
| `benchmark_renderer.py` available  | File does not exist                        |
| Old and new hashes should match    | Incorrect after intentional visual changes |

The project’s black is already `(8, 8, 12)`, equivalent to `#08080c`. It is already deeper than the proposed `#0a0a0f`.

## 2. Measured visual findings

Representative captured frames show:

* Evolution at 10 seconds: median luma approximately 14; 99th percentile approximately 93.
* Archive at 23 seconds: median approximately 15; 99th percentile approximately 68.
* Inference at 54 seconds: median approximately 56; 99th percentile approximately 141.
* Graph at 60 seconds: median approximately 45; 99th percentile approximately 160.
* Scene10 at 82.5 seconds: deliberately black-heavy, but highlights reach approximately 172.
* Binary at 92.5 seconds: median approximately 14; 99th percentile approximately 64.
* Eye at 110.5 seconds: median approximately 14; 99th percentile approximately 155.

The encoded video reaches around studio-black level already. Its problem is not raised blacks globally.

The actual problems are:

1. Evolution and Archive are darkened too heavily.
2. Plasma is bright enough, but its highest values converge toward pale lavender/white. It needs colour separation, not more opacity.
3. Terminal colours could be more legible on the Assembly screen.
4. Binary is dark, but it should not be corrected with a global brightness operation.
5. Scanlines and vignette are already sufficiently strong.

## 3. Global post-process values: lock them

### FILE: `source/engine/post_process.py`

#### Scanline visibility — no change

```python
# Line 16
SCANLINE_DIM = 0.040
```

Recommendation:

```text
Current:     0.040
Recommended: 0.040 — LOCK
```

Reason:

* Scanlines are plainly visible in 1:1 frames.
* They use alternating two-row bands.
* Inference also receives a second local scanline layer from `player_fx.py`.
* Raising this to `0.050–0.055` would darken half the rows further and increase moiré/compression risk.
* It would not make plasma more vivid.

#### Global vignette — no change

```python
# Line 72
mask = np.clip(1.0 - 0.38 * (dist ** 1.55), 0.42, 1.0)
```

Recommendation:

```text
Strength: 0.38 — LOCK
Exponent: 1.55 — LOCK
Floor:    0.42 — LOCK
```

Reason:

Some scenes already receive two vignettes:

1. Local vignette in `player_fx.py`.
2. Global vignette in `post_process.py`.

Evolution’s local vignette is already `0.70`; Archive uses `0.63`; Inference uses `0.55`; Graph uses `0.53`. Increasing the global value to `0.55` would crush corners rather than produce championship contrast.

#### Phase-grade lift — no change

```python
# Line 101
lift = 5 + int(10 * exposure)
```

Recommendation: lock.

The terminal and blackout scenes are already extremely dark. Reducing this base lift to deepen blacks would hurt text, loaders and the tagline more than it would improve cinematic material.

#### Contrast/gamma — do not add

Do not introduce `CONTRAST_BOOST`, gamma correction, curves, LUTs or levels code.

Reason:

* Those operations do not currently exist.
* Adding them would be a new algorithm and violate the code-locked constraint.
* Global gamma would harm the intentionally dark eye, tunnel, binary and terminal phases.
* “Gamma 1.1” is ambiguous: depending on implementation, it can either darken or brighten midtones.

## 4. Approved targeted effect candidates

These are the safest measured changes. They modify existing numeric effect parameters only.

### Change 1: Evolution tonal recovery

FILE: `source/player_fx.py`
LINE: 32

```python
Current:
"darken": 0.68,

Recommended:
"darken": 0.76,
```

Expected effect:

* Approximately 11.8% more scene luminance before global grading.
* Restores nebula, DNA, silicon and neural detail.
* Keeps the sequence darker than the later machine scenes.
* Does not add an operation or change performance.

Do not exceed `0.78` without reviewing the Big Bang and neural transition for clipping.

### Change 2: Archive tonal recovery

FILE: `source/player_fx.py`
LINE: 40

```python
Current:
"darken": 0.76,

Recommended:
"darken": 0.84,
```

Expected effect:

* Approximately 10.5% more luminance before global grading.
* Makes the archive/server information readable without flattening the scene.
* Preserves the red signal fragments.
* Does not change other raw scenes.

Do not set this to `1.0`. The archive should remain darker than the datacenter and inference act.

### Change 3: Plasma colour separation

FILE: `source/player_fx.py`
LINES: 94–96

Current:

```python
r = (wave * (180 + 70 * hue_shift)).astype(np.uint8)
g = (wave * (175 + 90 * (1 - hue_shift))).astype(np.uint8)
b = (36 + wave * 219).astype(np.uint8)
```

Candidate:

```python
r = (wave * (185 + 75 * hue_shift)).astype(np.uint8)
g = (wave * (168 + 85 * (1 - hue_shift))).astype(np.uint8)
b = (36 + wave * 219).astype(np.uint8)
```

Reason:

* Current maximum plasma tends toward approximately equal red, green and blue, creating pale lavender.
* The candidate slightly raises red, moderately separates green, and leaves blue/highlight range unchanged.
* This produces clearer blue-magenta plasma without increasing opacity.
* It preserves the same calculations, array types and operation count.

Keep these values locked:

```python
"inference": {"plasma_opacity": 0.72, ...}
"graph": {"plasma_opacity": 0.60, ...}
```

Increasing opacity would make the scenes brighter but also milkier. The problem is chroma separation, not insufficient overlay strength.

The plasma palette change must be treated as an A/B candidate, not an automatic final edit.

## 5. Terminal palette candidates

The terminal backgrounds are already deep. Improve text and signal colour instead of raising the background.

### FILE: `source/engine/palette.py`

Apply these one at a time:

```python
# Line 7
ICE_BLUE = (74, 124, 255)
→ ICE_BLUE = (82, 136, 255)

# Line 8
TERMINAL_GREEN = (46, 204, 113)
→ TERMINAL_GREEN = (52, 220, 120)

# Line 9
WARNING_AMBER = (230, 160, 32)
→ WARNING_AMBER = (240, 170, 36)

# Line 10
ALERT_RED = (224, 32, 32)
→ ALERT_RED = (240, 40, 44)

# Line 11
ARCHIVE_GREY = (138, 143, 152)
→ ARCHIVE_GREY = (154, 160, 170)

# Line 12
WHITE = (240, 240, 245)
→ WHITE = (248, 248, 252)
```

Keep unchanged:

```python
VOID = (8, 8, 12)
COLD_STEEL = (26, 35, 50)
```

These changes:

* Affect procedural UI, not photographic assets.
* Improve big-screen text separation.
* Preserve the surveillance/terminal identity.
* Do not change layout, font size, timing or rendering cost.

The most useful changes are `ARCHIVE_GREY`, `ICE_BLUE` and `WHITE`. The others can remain unchanged if their A/B difference is not clearly beneficial.

## 6. Asset brightness recommendations

### Do not apply a uniform operation to all assets

The 18 raw assets have radically different intentional distributions:

* Scene10 is 59% near-black.
* Scene12 Eye is approximately 69% near-black.
* Scene11b Binary is approximately 65% near-black.
* Bright datacenter and inference assets are already properly exposed.

A uniform `+8% brightness` would:

* Damage the eye reveal.
* Weaken scene10’s silhouette.
* Lift the binary background.
* Reduce contrast between narrative phases.
* Potentially clip datacenter fixtures and cosmic highlights.

### Initial recommendation

```text
Raw asset modifications: NONE
```

First evaluate the two existing `darken` parameters and terminal palette.

### Conditional scene11b candidate

Only if scene11b remains unreadable after reviewing the new encoded capture:

```text
Asset: scene11b_binary.png
Candidate test only: RGB brightness ×1.08
Saturation: unchanged
Contrast: unchanged
Black point: unchanged
```

Do not apply `+15%`, gamma, shadow lifting or automatic contrast.

Important: `scene11b_binary.png` is actually JPEG data stored under a `.png` filename. Rewriting it casually can change its format and bytes. Keep the original untouched and test with a separate lossless PNG variant.

## 7. Correct determinism strategy

The Phase 3 draft’s old-versus-new hash instruction is wrong.

If a visual value changes, rendered pixels must change:

```text
Baseline hash ≠ enhanced hash
```

Correct requirement:

```text
Enhanced run A hash = enhanced run B hash
```

Additionally:

* Frames outside the affected scene group should remain byte-identical.
* Evolution/Archive/plasma/UI frames should differ only when their corresponding parameter changes.
* Timeline JSON, audio, fonts and unrelated source hashes must remain unchanged.

There is no `source/benchmark_renderer.py`. The available validation utility is:

```bash
python3 source/render_postprocess_quality_approval.py \
  --out-dir /tmp/postprocess_validation \
  --validate-only
```

However, it primarily validates scanline/vignette orientation and one deterministic frame. Full sequential verification is still required.

### Required hash test

Render the candidate twice using the same renderer, resolution and worker count:

```bash
sha256sum candidate_run_a/frame_*.png > candidate_a.sha256
sha256sum candidate_run_b/frame_*.png > candidate_b.sha256

sed 's#candidate_run_a/#FRAMES/#' candidate_a.sha256 > candidate_a_normalized.sha256
sed 's#candidate_run_b/#FRAMES/#' candidate_b.sha256 > candidate_b_normalized.sha256

diff -u candidate_a_normalized.sha256 candidate_b_normalized.sha256
```

Expected: no difference.

Then compare baseline versus candidate. Differences are expected, but must be restricted to affected segments.

## 8. Before/after frame set

Use more than one arbitrary “frame 60.” Frame 60 is only one second into the production and cannot represent the changes.

Required timestamps:

|  Time | Purpose                                   |
| ----: | ----------------------------------------- |
|   2.0 | Origin; should remain unchanged           |
|  10.0 | Evolution                                 |
|  23.0 | Archive                                   |
|  32.4 | Access Denied terminal                    |
|  48.0 | Deploy terminal                           |
|  54.0 | Inference plasma                          |
|  60.0 | Graph/plasma                              |
|  77.0 | Tunnel; should remain unchanged           |
|  82.5 | Scene10; should remain unchanged          |
|  87.5 | Statue; should remain unchanged           |
|  92.5 | Binary; should remain unchanged initially |
|  99.0 | Guardrails terminal                       |
| 106.0 | Blackout; black must remain unchanged     |
| 110.5 | Eye; should remain unchanged              |
| 118.0 | Tagline terminal                          |

Review:

* Full 1920×1080 frames.
* 100% crops.
* Encoded H.264 frames, not only lossless render PNGs.
* Dark-room monitor and normal room lighting.
* At least one display viewed from several metres away.

## 9. Objective acceptance limits

A candidate passes only if:

* Evolution and Archive regain visible detail without looking lifted.
* Plasma is more chromatically distinct, not more white.
* Terminal text is easier to read.
* Blackout and Eye retain their current darkness.
* Scanlines do not become more visible.
* Vignette edges do not become darker.
* No new clipping appears.

Suggested limits on lossless rendered frames:

```text
Near-white pixels >=253: no more than 0.25% unless already present
Near-black pixels <=2: must not increase in targeted scenes
Target-scene median luma: increase no more than 15%
Target-scene p99 luma: increase approximately 5–15%
Unaffected-frame SHA-256: exact match
```

## 10. Performance verification

These edits retain exactly the same operations, so CPU/GPU cost should remain within measurement noise. Nevertheless, test on the same machine.

```bash
./entry/run.sh \
  --headless \
  --resolution 1920x1080 \
  --duration 122.5 \
  --profile
```

Acceptance:

* No increase in frames exceeding 16.67 ms.
* Maximum render time no more than 2% worse.
* Average render time no more than 2% worse.
* Three consecutive runs.
* No missing frames or exceptions.

Also run the single-worker offline renderer to measure uncapped renderer throughput:

```bash
python3 source/parallel_dump.py \
  --workers 1 \
  --resolution 1920x1080 \
  --dump-dir /tmp/phase3_single_worker
```

The live player’s `clock.tick(60)` caps the loop, so “achieved 60 fps” alone is not sufficient evidence. Per-frame render time is the meaningful figure.

## 11. Implementation order

1. Freeze baseline hashes for all locked files.
2. Render the 15 baseline timestamps.
3. Change Evolution `darken: 0.68 → 0.76`.
4. Render and review Evolution only.
5. Change Archive `darken: 0.76 → 0.84`.
6. Render and review Archive only.
7. Test plasma palette in a separate candidate copy.
8. Keep or reject plasma based on lossless and encoded comparisons.
9. Test `ARCHIVE_GREY`.
10. Test `ICE_BLUE`.
11. Test `WHITE`.
12. Test the remaining terminal colours only if needed.
13. Run complete determinism and performance verification.
14. Generate full capture.
15. Verify 7,350 frames, 122.5 seconds, 1080p60, H.264/AAC.
16. Refresh screenshot only after the final candidate is accepted.

### Automatic rollback conditions

Revert the last change if:

* Unaffected frame hashes change.
* Determinism fails.
* Runtime exceeds 122.5 seconds.
* Performance regresses by more than 2%.
* Blacks become grey.
* Plasma becomes paler.
* Text loses readability.
* Scene10, Eye, Tunnel or Statue change unexpectedly.
* The A/B preference is uncertain.

Uncertainty means rollback. The restored version remains the default winner.

# Code-locked Codex implementation prompt

Use this with Codex. It is deliberately designed so no candidate can replace the restored version without evidence.

```text
PHASE 3 — STRICT NON-DEGRADATION VISUAL PASS

You are working on “Artificial Intelligence Never Sleeps,” an Assembly Summer
2026 AI Coding entry.

The restored source is the protected baseline. Do not modify the original ZIP.
Extract or copy it into a separate Phase 3 candidate workspace.

DEFAULT OUTCOME:
If a change is not clearly and measurably better, preserve the baseline.
Doing nothing is preferable to uncertain improvement.

ABSOLUTELY LOCKED:
- Timeline, scene order, duration and cues
- demo_player.py
- renderer.py
- terminal.py
- tunnel.py
- player_motions.py
- audio
- fonts
- manifests
- run scripts
- capture script
- algorithms, imports, classes and functions
- random/time behaviour
- resolution and frame rate
- raw assets, unless separately authorised after all parameter tests

DO NOT:
- Refactor
- Add effects or passes
- Add gamma/contrast/LUT code
- Add new constants
- Change scanline structure
- Change vignette algorithm
- Regenerate assets
- Apply global asset brightness
- Change timing
- Change opacity merely to make plasma brighter
- overwrite the protected baseline
- claim old and enhanced hashes should match

VERIFIED BASELINE:
- SCANLINE_DIM is already 0.040
- Global vignette is already:
  np.clip(1.0 - 0.38 * (dist ** 1.55), 0.42, 1.0)
- VOID is already (8, 8, 12)
- There is no CONTRAST_BOOST or BLACK_FLOOR
- Existing scanlines and global vignette must remain unchanged

ALLOWED CANDIDATE CHANGES, ONE AT A TIME:

1. source/player_fx.py
   Evolution darken:
   0.68 -> 0.76

2. source/player_fx.py
   Archive darken:
   0.76 -> 0.84

3. source/player_fx.py plasma colour candidate:
   r = wave * (180 + 70 * hue_shift)
   ->
   r = wave * (185 + 75 * hue_shift)

   g = wave * (175 + 90 * (1 - hue_shift))
   ->
   g = wave * (168 + 85 * (1 - hue_shift))

   Keep the blue expression unchanged.
   Keep plasma opacity unchanged.

4. source/engine/palette.py, tested separately:
   ICE_BLUE       (74,124,255)  -> (82,136,255)
   TERMINAL_GREEN (46,204,113)  -> (52,220,120)
   WARNING_AMBER  (230,160,32)  -> (240,170,36)
   ALERT_RED      (224,32,32)   -> (240,40,44)
   ARCHIVE_GREY   (138,143,152) -> (154,160,170)
   WHITE          (240,240,245) -> (248,248,252)

   Keep VOID and COLD_STEEL unchanged.

BEFORE EDITING:
1. Record SHA-256 of every locked source file.
2. Record archive SHA-256.
3. Render baseline frames at:
   2.0, 10.0, 23.0, 32.4, 48.0, 54.0, 60.0, 77.0,
   82.5, 87.5, 92.5, 99.0, 106.0, 110.5, 118.0 seconds.
4. Record frame hashes and luma percentiles.
5. Record performance three times.

FOR EACH CHANGE:
1. Use apply_patch for the numeric value only.
2. Show the exact one-line diff.
3. Compile all Python files.
4. Render only relevant comparison timestamps.
5. Verify unrelated timestamp hashes remain identical.
6. Produce full-frame and 100% crop A/B comparisons.
7. Encode the comparison through the real H.264 settings.
8. Report luma p01, p05, p50, p95, p99 and clipped-pixel percentages.
9. Do not promote the candidate automatically.

DETERMINISM:
- Baseline and enhanced hashes are expected to differ.
- Candidate run A and candidate run B must match exactly.
- Run the complete candidate twice with the same worker count.
- If hashes differ, reject the candidate.

PERFORMANCE:
- Run three same-machine profile passes.
- Reject if average or maximum render time regresses by over 2%.
- Reject if the count of frames above 16.67 ms increases.
- Do not use clock-capped “60 fps” alone as proof.

VISUAL ACCEPTANCE:
- Evolution/Archive gain detail without grey blacks.
- Plasma gains blue/magenta separation without becoming pale.
- Terminal text becomes more readable.
- Scanlines do not become stronger.
- Vignette edges do not become darker.
- Scene10, Tunnel, Statue, Binary, Eye and Blackout remain unchanged
  unless directly affected by an authorised palette constant.
- If preference is uncertain, reject and restore baseline.

RAW ASSETS:
Do not modify any raw asset during the initial pass.
In particular, scene11b_binary.png contains JPEG data despite its extension.
Do not rewrite it.

FINAL OUTPUT:
Provide:
- Exact diff
- Baseline/candidate frame hashes
- Determinism result
- Performance result
- Before/after comparison images
- Luma statistics
- Recommendation: ACCEPT or REJECT for each isolated change

Do not create the final submission capture until every accepted candidate has
passed all checks. Never overwrite the protected restored baseline.
```
