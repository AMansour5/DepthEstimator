# P03: "No match" pixels become a confident wrong depth when `minDisparity` is not 0

| | |
|---|---|
| **Severity** | High for the tuner path, latent for the configured path (the config uses `minDisparity: 0`) |
| **Status** | **Partly fixed, reopened**. The configured value is handled; the `overrides` path used by `DisparityTuner` is not. `evidence/p03_min_disparity.py` prints `VERDICT PARTLY FIXED` |
| **Where** | `src/services/StereoProcessor.py:144` (the clamp, compares with `self.matcher_params["minDisparity"]`) and `:133` (the override reaches the matcher only); `src/tuners/DisparityTuner.py:32` (slider 0-10), `:51`, `:153` (passes the slider as an override), `:107-117` (`__writeParams` stores it); `src/services/DepthEstimator.py:72` and `src/utils/DisparityVisualizer.py:13` (`> 0` means valid) |

## Summary

SGBM writes `minDisparity - 1` into pixels it could not match. With `minDisparity = 0` that is `-1`, and with `minDisparity = 1` it is
`0`; both fail the codebase's "valid means `> 0`" test, so they are correctly ignored. With `minDisparity >= 2` the sentinel
(`1`, `2`, ...) is a small **positive** number, which the code reads as a real measurement of a very distant surface.

## What was fixed (`9483759`)

`computeDisparity` now ends with

```python
disparity[disparity < self.matcher_params["minDisparity"]] = -1.0   # SGBM's 'no match' is minDisparity - 1
```

For a `minDisparity` in the config this is correct: part A of the script finds **0** raw sentinel pixels counted as valid for
`minDisparity` 0, 3 and 8.

## What is still wrong

`computeDisparity(left, right, overrides)` builds the matcher with the overridden `minDisparity` but clamps with the
**configured** one. `DisparityTuner` calls it that way with its `minDisparity` slider (0-10), so while tuning at slider
value `m > 1`, SGBM's `m - 1` sentinel stays in the map as a valid-looking disparity (part B, flat scene, true `d = 40`):

```
override minDisparity=3: raw sentinel pixels counted as valid = 14274   box at the left edge: z=15000 mm  d=2.0  reliable=True
override minDisparity=8: raw sentinel pixels counted as valid = 14446   box at the left edge: z=4286 mm   d=7.0  reliable=True
```

Both are wrong (the truth is 750 mm) and both are flagged reliable, because the sentinel region is perfectly uniform
(`valid_frac = 1.0`, spread 0), exactly what the `reliable` heuristic rewards.

Consequences:

- The tuner's disparity panel and its click probe (`__measureAt`) draw and report the sentinel as a very distant surface, so
  you tune against a picture that is wrong exactly where matching failed.
- Pressing `d` writes the slider value into `config/stereo_processor.yaml` (`__writeParams`). From then on the *configured*
  path is the one used, and it is clamped correctly, so the damage is limited to the tuning session. A tuned
  `minDisparity > 0` is still unusual: it shifts the whole search window.

## Suggested fix

Use the effective value, not the configured one:

```python
params = {**self.matcher_params, **overrides}
...
disparity[disparity < params["minDisparity"]] = -1.0
```

(the merged `params` already exists in `computeDisparity` for the padding). Add a regression test that calls
`computeDisparity(..., {"minDisparity": 3})` on a textured pair and asserts that no pixel equals `2.0`: there is none for
the override path today (`src/tests/test_stereo_dead_band.py` only uses `minDisparity: 0`).

## How to verify

`python3 docs/problems/evidence/p03_min_disparity.py`: part B should show 0 sentinel pixels and `None` for the edge box,
ending in `VERDICT FIXED`.
