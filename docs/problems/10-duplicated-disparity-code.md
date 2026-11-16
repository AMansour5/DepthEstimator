# P10: Disparity code was copied in three places

| | |
|---|---|
| **Severity** | Low (before the fix) |
| **Status** | **Fixed** in `084b056`. Re-checked: `evidence/p10_interpolation.py` part A scans the source and prints `VERDICT FIXED` |
| **Where** | `src/services/StereoProcessor.py:101-146` (`buildMatcher`, `computeDisparity` with `overrides`); `src/utils/DisparityVisualizer.py:12-18` (`colorizeDisparity`); callers `src/tuners/DisparityTuner.py:153,158` and `src/services/Orchestrator.py:63,94` |

## Resolution

There is one implementation of each piece now:

- **Matcher and image preparation:** `StereoProcessor.buildMatcher(overrides)` builds the SGBM object and
  `computeDisparity(left, right, overrides)` does grey conversion, downscale (`INTER_AREA`), padding, matching and the
  sentinel clamp. `DisparityTuner` calls it with its slider values (`{**params, "process_scale": scale}`) instead of owning a
  copy, and the Orchestrator calls it with no overrides.
- **Colouring:** `DisparityVisualizer.colorizeDisparity` (plus `drawText` and `highlightLeftInvalidBand`) is used by both views.

The script confirms it from the source: the tuner has no `StereoSGBM_create`, no colourizer of its own, the Orchestrator has no
colourizer, and `StereoProcessor` downscales only with `INTER_AREA`.

A good illustration of why it mattered: the [P01](01-sgbm-dead-band.md) padding fix landed once and both the tuner and the runtime got
it. The same sharing is also why the override bug in [P03](03-invalid-disparity-assumes-min-disparity-zero.md) sits in one
place and is fixed in one place.

## Original finding (kept for context)

The tuner shrank images with `INTER_AREA`, the runtime with `INTER_LINEAR`. At the configured `process_scale: 0.5` the two give
**identical** images (averaging 2x2 blocks is what bilinear sampling does at exactly half size); at other scales they differ
slightly, but on the clean synthetic pair the disparity results did not (part B of the script, still reproducible as a historical
check):

```
scale | mean |pixel diff| | median disp AREA  LINEAR | valid% AREA  LINEAR
  0.5 |              0.00 |            40.00   40.00 |        91.6    91.6
  0.4 |              2.05 |            32.00   32.00 |        91.5    91.6
  0.3 |              3.84 |            24.00   24.00 |        88.7    88.7
  0.7 |              0.84 |            56.00   56.00 |        92.8    92.8
```

Noisy or finely textured real images may behave differently; this was not tested. There was no measurable effect then, so
the fix was preventive.

## What still differs on purpose

`DisparityTuner.__measureAt` (a 5x5-patch click probe) and the Orchestrator's per-box `DepthEstimator.computeObjectDepth` are two
different depth readouts: the tuner's is a quick probe, the runtime's uses the central crop, the median and the `reliable`
flag. Treat the tuner's number as a rough check, not a prediction of what the demo will show for a box.

## How to verify

`python3 docs/problems/evidence/p10_interpolation.py`: part A should list no duplicated code, ending with `VERDICT FIXED`.
