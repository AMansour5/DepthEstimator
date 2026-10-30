# P01: With `numDisparities: 320`, a third of the frame can never get a depth

| | |
|---|---|
| **Severity** | High |
| **Status** | Reproduced (`evidence/p01_dead_band.py`) |
| **Where** | `config/stereo_processor.yaml:8` (`numDisparities: 320`) and `:2` (`process_scale: 0.5`); `src/services/StereoProcessor.py:115-123` (`computeDisparity`) |

## Summary

OpenCV's SGBM leaves the leftmost `numDisparities` columns of the disparity map invalid. The
disparity map is computed at `process_scale` (960 px wide for a 1920 px frame at 0.5), so with the
current config the **left 320 of 960 columns (33% of the image) never produce a depth**, whatever is
standing there.

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

## Suggested fixes

1. **Use only the range you need.** `DisparityTuner` already prints
   `numDisparities >= N` for your `Z_MIN_MM`. Check that 320 is really required: the scene above
   recovers fully at 128.
2. **Pad before matching, crop after.** Verified on the synthetic scene (first valid column goes
   from 320 to 4):

   ```python
   pad = self.matcher_params["numDisparities"]
   gray_l = cv2.copyMakeBorder(gray_l, 0, 0, pad, 0, cv2.BORDER_REPLICATE)
   gray_r = cv2.copyMakeBorder(gray_r, 0, 0, pad, 0, cv2.BORDER_REPLICATE)
   raw = self.matcher.compute(gray_l, gray_r)[:, pad:]
   ```

   Cost: SGBM works on a wider image. In my sandbox compute time went from about 189 ms to 299 ms
   (single noisy measurement; measure on your own machine). Verified with `minDisparity: 0` only.
3. Whichever you choose, **draw the unmeasurable band** on the disparity panel so users can see it.

## How to verify a fix

Re-run `evidence/p01_dead_band.py` (part A should report a first valid column near 0), and watch
the black band on the left of the disparity panel in `DisparityTuner` shrink.
