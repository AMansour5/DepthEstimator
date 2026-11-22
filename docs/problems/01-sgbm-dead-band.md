# P01: SGBM leaves the leftmost `numDisparities` columns without a depth

| | |
|---|---|
| **Severity** | High (before the fix) |
| **Status** | **Fixed** in `c39cf63`. Re-checked: `evidence/p01_dead_band.py` prints `VERDICT FIXED` |
| **Where** | `depth_estimator/services/StereoProcessor.py:125-146` (`computeDisparity`, the padding is at `:138-142`); `depth_estimator/config/stereo_processor.yaml` (`numDisparities: 272`, `process_scale: 0.5`); `depth_estimator/utils/DisparityVisualizer.py:21-38` (`highlightLeftInvalidBand`) |

## Resolution

`computeDisparity` now pads both downscaled grayscale images on the left by `numDisparities` columns
(`cv2.BORDER_REPLICATE`), runs SGBM, and crops the same number of columns off the result, so the map keeps the
size and alignment of the left image. On the synthetic scene the first valid column went from **272 to 4** and an
object that used to show "no depth" is measured correctly (750 mm). The runtime panel and `DisparityTuner` tint the
invalid strip at the left edge (`highlightLeftInvalidBand`). Regression tests: `depth_estimator/tests/test_stereo_dead_band.py`.

What it costs (measured on the real 1920x1080 sample pair, `numDisparities: 272`, `process_scale: 0.5`): SGBM alone about
46 ms, `computeDisparity` including resize, padding and crop about 56 ms. The matcher sees an image `numDisparities`
columns wider, so the cost grows with `numDisparities`; measure on your own machine.

### What is left (not a new problem, a property of stereo)

- **The `d` leftmost columns are still not measured.** A point at disparity `d` lies outside the right camera's view for
  `x < d`. Padding does not create that data: SGBM fills those columns by extrapolating the replicated border. In the
  synthetic scene 37-61% of them carry a value and 4-6% of those are off by more than 2 px (part D of the script), so a
  depth taken from a box whose centre is within `d` columns of the left edge is the least trustworthy depth in the frame.
- **The tint means "a contiguous invalid strip touches the left edge", whatever the cause.** It no longer marks the SGBM
  artifact (that is gone). It still fires for real unmeasurable regions at the border: on the real sample pair it covers
  13% of the panel (157 columns, where the left part of the scene has no matches), and a near object placed close to the left
  edge occludes a background strip that gets tinted too, while the same strip elsewhere in the frame is not. That is the
  intended reading ("no depth here"), but do not read the tint width as the SGBM edge loss. Details: part E of the script.

## Summary of the original problem

OpenCV's SGBM leaves the leftmost `numDisparities` columns of the disparity map invalid. The disparity map is computed at
`process_scale` (960 px wide for a 1920 px frame at 0.5), so with the old config (`numDisparities: 320`) the **left 320 of
960 columns (33% of the image) never produced a depth**, whatever was standing there.

## Why it happens

For each pixel, SGBM searches `numDisparities` candidate matches to its left in the right image. Pixels closer than
`numDisparities` to the left edge don't have the full search range inside the image, so SGBM marks them invalid. The
measured band width equals `numDisparities` exactly and does **not** depend on how far away the object is (part A, raw
matcher, current config):

```
true d= 10: first valid column = 272  (28% of the width is dead)
true d= 40: first valid column = 272  (28% of the width is dead)
true d= 80: first valid column = 272  (28% of the width is dead)
```

(The physical minimum is only `d` columns. The extra width is an artifact of the search range, which is what padding removes.)

## Evidence

Two identical objects at the same true depth (750 mm), one inside the old band and one outside, through the real SGBM
parameters and the real `DepthEstimator`:

```
raw SGBM, numDisparities=272
   object at x 100-220 (inside old band): None (no depth)
   object at x 600-720 (outside it):      z=750 mm  reliable=True
raw SGBM, numDisparities=128
   object at x 100-220 (inside old band): z=750 mm  reliable=True
   object at x 600-720 (outside it):      z=750 mm  reliable=True
StereoProcessor.computeDisparity, numDisparities=272 (after the fix)
   first valid column = 4
   object at x 100-220: z=750 mm  reliable=True
   object at x 600-720: z=750 mm  reliable=True
```

## Effects (before the fix)

- Any detection whose sampled region lay in the left part of the frame showed **red "no depth"**, even for a large,
  well-textured object a metre away.
- A box straddling the band edge got a reduced `valid_frac` and was often flagged orange `?`.
- It was **silent**, and it coupled with range: to see closer objects you had to raise `numDisparities`, which widened the
  dead band further.

## Remaining advice

- Keep `numDisparities` as small as your nearest object allows (`DisparityTuner` prints the number for `Z_MIN_MM`): the
  padding cost scales with it, and a smaller range also lowers the chance of wrong matches.
- Treat depths for objects within `d` columns of the left edge as low confidence. If that matters, mark them in
  `DepthEstimator` (for example flag `reliable = False` when the sampled region starts left of the expected `d`).

## How to verify

`python3 docs/problems/evidence/p01_dead_band.py` (part C: first valid column near 0, both objects measured) and
`python3 -m pytest -q depth_estimator/tests/test_stereo_dead_band.py`. In `DisparityTuner`, raise `numDisp x16`: the black/tinted strip on
the left should no longer grow with it.
