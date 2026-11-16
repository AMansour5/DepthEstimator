# P08: The unit of depth is still an assumption (it is now recorded, but never applied)

| | |
|---|---|
| **Severity** | Medium |
| **Status** | **Partly fixed**. Labels are consistent now; the stored unit is read but ignored (reproduced by `evidence/p13_calibration_schema.py`, part B). The original arithmetic is **source-read** and needs your calibration to see real numbers |
| **Where** | `src/services/StereoProcessor.py:66` (`square_size_mm` loaded, never used), `:83-90` (`getBaseline`); `src/services/DepthEstimator.py` (result key `z_mm`); `src/services/Orchestrator.py:109` (`z_mm / 1000` shown as metres); `src/tuners/DisparityTuner.py:75-77` (prints `z_mm / 10` as cm) |

## Summary

The baseline, and therefore every depth, is in **whatever unit was used for the checkerboard square size during
calibration**. `getBaseline()` returns `abs(1 / Q[3, 2])`; `Q` comes from `cv2.stereoRectify` using the translation `T`, and `T`
comes out in the units of the calibration target's square size.

## What changed (`db60e9b`)

- The calibration file now carries `square_size_mm` and `checkerboard`, and `StereoProcessor` loads them
  (`self.square_size_mm`, `self.checkerboard_dims`).
- The mislabelled "cm" print for the baseline in the test was corrected to mm, and the tuner's output is consistent
  (`z_mm` in the data, centimetres in the tuner's probe text, metres in the overlay).

## What is still open

**The recorded unit is not used.** Nothing in `src/` reads `square_size_mm` after loading it, and `getBaseline()` ignores it. Two
calibrations with identical translation and `square_size_mm` = 30 and 3 return the same baseline:

```
square_size_mm= 30.0: getBaseline() = 60.0
square_size_mm=  3.0: getBaseline() = 60.0
```

So if the squares were entered in centimetres (or inches) in the calibration run, **every depth is still wrong by a constant
factor with no error**. Illustration (made-up numbers):

| Square size entered | `getBaseline()` | `z_mm` computed | `Orchestrator` shows (`z_mm / 1000`) | Real distance |
|---|---|---|---|---|
| 25 (mm) | 60.0 | 750 | 0.75 m | 0.75 m |
| 2.5 (cm) | 6.0 | 75 | **0.075 m** (10x too small) | 0.75 m |

The new key is a *name*, not a conversion: it says "mm" even when the number stored in it was typed in cm. On the author's
calibration (`square_size_mm: 30`) `getBaseline()` returns about 136 mm; a value ten times smaller (13.6) would reveal a unit
mix-up, but only a measurement of a known distance proves the scale.

## Suggested fix

Make the key meaningful. Either (a) have the calibration script store `T` in millimetres and fail if `square_size_mm` is not
what it used, or (b) validate in `StereoProcessor` that the baseline is plausible for the camera (for example 20-500 mm) and
raise otherwise. Keep one display convention: metres in the overlay, millimetres in data. Add a test with two calibrations that
differ only in `square_size_mm`. See also [P13](13-calibration-schema-unused-required-keys.md), which covers the same key from
the compatibility side.

## How to verify

`python3 docs/problems/evidence/p13_calibration_schema.py`, part B: the baselines should differ (or a bad unit should raise).
Then hold an object at a measured distance and compare ([`docs/setup.md`](../setup.md), first-run checklist).
