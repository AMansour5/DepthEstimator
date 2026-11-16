# P01: With `numDisparities: 320`, a third of the frame can never get a depth

| | |
|---|---|
| **Severity** | High |
| **Status** | Fixed; original issue reproduced in `evidence/p01_dead_band.py` |
| **Where** | `config/stereo_processor.yaml:8` (`numDisparities: 320`) and `:2` (`process_scale: 0.5`); `src/services/StereoProcessor.py` (`computeDisparity`) |

## Summary

Without padding, OpenCV's SGBM leaves the leftmost `numDisparities` columns of the disparity map
invalid. At `process_scale` 0.5, the old configuration therefore made the left 320 of 960 columns
(33% of the image) unmeasurable.

`StereoProcessor.computeDisparity` now pads both scaled grayscale images on the left by
`numDisparities`, computes SGBM, and crops the padding from the result. The output remains aligned
to the original left image and retains its original dimensions. The runtime disparity panel and
`DisparityTuner` tint the contiguous invalid strip at the map's left edge so any residual is visible.

## Why it happens

For each pixel, SGBM searches `numDisparities` candidate matches to its left in the right image.
Pixels closer than `numDisparities` to the left edge don't have the full search range inside the
image, so SGBM marks them invalid. The measured band width equals `numDisparities` exactly and does
**not** depend on how far away the object is:

```
true d= 10: first valid column = 320  (33% of the width is dead)
true d= 40: first valid column = 320  (33% of the width is dead)
true d= 80: first valid column = 320  (33% of the width is dead)
```

(The physical minimum is only `d` columns, because a point at disparity `d` is simply outside the
right camera's view for `x < d`. The extra width is an artifact of the search range.)

## Evidence

Two identical objects at the same true depth (750 mm), one inside the band and one outside, run
through the real SGBM parameters and the real `DepthEstimator`:

```
numDisparities=320
   object at x 100-220 (inside band):  None (no depth)
   object at x 600-720 (outside band): z=750 mm  reliable=True
numDisparities=128
   object at x 100-220 (inside band):  z=750 mm  reliable=True
   object at x 600-720 (outside band): z=750 mm  reliable=True
```

## Effects

- Any detection whose sampled region lies in the left third of the frame shows **red "no depth"**,
  even for a large, well-textured object a metre away.
- A box that straddles the band edge gets a reduced `valid_frac` and is often flagged orange `?`.
- It is **silent**. The pipeline does not say "this region is unmeasurable"; the user just sees
  inconsistent results depending on where an object stands.
- **It couples with range.** To see *closer* objects you must raise `numDisparities`, which widens
  the dead band further. The dead band is `numDisparities / process_scale` pixels at full
  resolution (640 px of 1920 with the current values).
- Together with [P03](03-invalid-disparity-assumes-min-disparity-zero.md), the invalid pixels in this band
  can become a confidently wrong depth when `minDisparity > 0`.

## Implemented fix

Padding and cropping preserve the configured close-range search. On the synthetic scene, the first
valid column moved from 320 to 4, and the object inside the former band recovered its correct depth:

The trade-off is that SGBM processes images wider by `numDisparities` pixels at the selected
processing scale, so runtime may increase. If that cost is unacceptable, reduce `numDisparities` to
the minimum needed for the desired range; this trades close-range coverage for compute time.

The edge highlight uses the first column with more than 50% valid disparities as the boundary. If
there is no such column, no edge band is inferred. Other invalid pixels (for example, textureless or
occluded areas) are not classified as part of this left-edge band.

## How to verify a fix

Run `python3 docs/problems/evidence/p01_dead_band.py` (part C should report a first valid column near
0 and recover both objects), and run `pytest -q src/tests/test_stereo_dead_band.py`. In the runtime
disparity view and `DisparityTuner`, the highlighted left-edge strip should shrink to the residual
invalid columns.
