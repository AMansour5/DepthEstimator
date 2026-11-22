# Depth estimation

How a pair of images becomes a distance, how much to trust it, and what range to expect. All numbers marked
*illustrative* use `f = 1000 px` and `B = 60 mm`, which are **not** your camera's values. Your real values are printed by
`DisparityTuner` at start-up.

## 1. From disparity to distance

After rectification, a point appears on the same row in both images but shifted horizontally. That shift is the
**disparity** `d`. For a rectified pair:

```
Z = f * B / d
```

`Z` distance, `f` focal length in pixels, `B` baseline (distance between the cameras), `d` disparity in pixels.
Nearer objects have larger disparity.

Because SGBM runs on images shrunk by `process_scale` (`s`), the measured disparity is `s` times the full-resolution
disparity, so the formula the code uses is

```
Z = f_full * s * B / d_scaled
```

`f_full` and `B` come from the calibration through the `Q` matrix: `f_full = |Q[2,3]|`, `B = |1 / Q[3,2]|`.

## 2. One distance per box

A bounding box is a rectangle, but objects are not. Taking the whole box would mix in background (far away, small
disparity), which pulls the estimate backwards. `DepthEstimator.computeObjectDepth` therefore:

1. **Scales** the box to disparity-map pixels (`box * process_scale`).
2. **Crops to the centre.** Keeps the middle `roi_shrink` of the box's width and height (default `0.5`).
   *Example:* box `(400, 200, 800, 600)` at scale 0.5 becomes columns `250..350`, rows `150..250`.
3. **Drops invalid pixels** (those with `disparity <= 0`).
4. **Takes the median** of the rest. The median ignores outliers as long as more than half the pixels are good.
   A plain mean would be dragged by invalid values, background, and speckle.
5. Returns `Z = f_full * s * B / median`.

It returns `None` when the crop is empty or fewer than `MIN_VALID_PIXELS` (5) pixels are valid.

### The `reliable` flag

A heuristic, **not a measured accuracy**. A depth is flagged reliable when both hold:

- `valid_frac >= min_valid_frac` (default 0.2): enough of the sampled region had a valid disparity;
- `rel_spread <= max_rel_spread` (default 0.15): the disparities agree, where
  `rel_spread = (75th percentile - 25th percentile) / median`.

On screen: green = reliable, orange `?` = computed but failed a check, red = `None`.

## 3. How accurate is it?

The error in `Z` grows with the *square* of the distance:

```
dZ  ~  Z^2 * dd / (f_full * s * B)         (dd = disparity error in pixels)
```

*Illustrative*, with `dd = 0.5 px` (a plausible order of magnitude, not a measured figure):

| Distance | Disparity at `s=0.5` | Error at `s=0.5` | Disparity at `s=1.0` | Error at `s=1.0` |
|---|---|---|---|---|
| 1 m | 30 px | 17 mm (1.7%) | 60 px | 8 mm (0.8%) |
| 2 m | 15 px | 67 mm (3.3%) | 30 px | 33 mm (1.7%) |
| 5 m | 6 px | 417 mm (8.3%) | 12 px | 208 mm (4.2%) |
| 10 m | 3 px | 1667 mm (16.7%) | 6 px | 833 mm (8.3%) |

Take-aways:

- **Halving the resolution doubles the error** for the same sub-pixel accuracy. `process_scale` trades accuracy for speed.
- Far objects are inherently imprecise. Accuracy improves with a larger baseline `B` or a longer focal length `f`.
- Don't trust a depth when the disparity is only a few pixels.

## 4. Working range

**Nearest distance** is limited by `numDisparities`: an object whose disparity exceeds the search range can't be matched.

```
Z_min  ~  f_full * s * B / numDisparities
needed numDisparities for a given Z_min = ceil(f_full * s * B / Z_min / 16) * 16
```

*Illustrative* (`s = 0.5`):

| `numDisparities` | `Z_min` | Padded image width fed to SGBM (960 px map) |
|---|---|---|
| 64 | about 470 mm | 1024 px |
| 128 | about 230 mm | 1088 px |
| 192 | about 160 mm | 1152 px |
| 272 | about 110 mm | 1232 px |
| 320 | about 94 mm | 1280 px |

Earlier versions lost the leftmost `numDisparities` columns of the map (a third of the frame at 320), so every extra unit of range
also widened a strip that could never produce a depth. That is fixed ([P01](problems/01-sgbm-dead-band.md)): `computeDisparity`
pads the images on the left by `numDisparities` and crops the result. The price is the last column: SGBM now processes
`width + numDisparities` columns, so the cost of the range is paid in compute time instead (about 46 ms to 56 ms on a
1920x1080 pair at 272 and scale 0.5; measure on your machine). Choose the smallest value that covers your nearest object.

What padding cannot do: a point with disparity `d` is outside the right camera's view for `x < d`, so the leftmost `d` columns
hold **extrapolated, not measured** values (in the synthetic test 37-61% of them carry a value, and 4-6% of those are off by
more than 2 px). Treat a depth taken near the left edge of the frame as the least certain one.

An object nearer than `Z_min` is not measured: in a synthetic test with `numDisparities: 272` (`Z_min` about 110 mm at the
illustrative `f` and `B`), an object at disparity 272 was still measured (111 mm), while objects at disparity 300 and 340 came
back 93-94% invalid and their boxes returned `None`; the few valid pixels sat at the object's edges and held the background's
disparity. Real, slanted or poorly textured objects can behave differently (a partly matched region can yield a wrong number),
so treat anything closer than `Z_min` as unmeasurable.

**Farthest distance** is limited by precision, not by a hard cut-off: see the table above.

## 5. Limitations of the approach

- **One number per box.** There is no segmentation mask. Thin, concave or partially occluded objects can include
  background in the sampled centre.
- **The `reliable` flag penalises slanted surfaces.** A wall or table seen at an angle spans many disparities, so its
  `rel_spread` is large even when the measurement is fine.
- **Textureless surfaces** (blank walls, uniform floors) give no matches and therefore holes; so do reflective or
  repetitive surfaces.
- **Occlusion.** A point visible to the left camera but hidden from the right has no match, and a near object hides a strip
  of background just to its left in the left image. The disparity panel tints an invalid strip that touches the left edge
  ([P01](problems/01-sgbm-dead-band.md)); occlusions elsewhere are simply black.
- **Units.** Baseline and depth are in millimetres when the calibration's `T` is written in millimetres and marked with
  `translation_unit="mm"`. Legacy files without the marker warn and assume mm. The marker describes `T`; it does not
  convert it, and `square_size_mm` is descriptive metadata only ([P08](problems/08-implicit-units.md)).
- **Calibration quality bounds everything.** The reported `rms_stereo` of the calibration is a good first check; a
  poor calibration produces systematic distance errors that no tuning can remove.
