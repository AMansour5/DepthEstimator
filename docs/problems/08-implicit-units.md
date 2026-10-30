# P08: Units of depth are implicit and inconsistent (mm vs cm)

| | |
|---|---|
| **Severity** | Medium |
| **Status** | Source-read (code reading and arithmetic; needs your calibration to see real numbers) |
| **Where** | `src/services/StereoProcessor.py:77-92` (`getBaseline`, `getFocalLength`); `src/services/DepthEstimator.py` (result key `z_mm`); `src/services/Orchestrator.py:123` (`z_mm / 1000` shown as metres); `src/tuners/DisparityTuner.py:108` (prints `z_mm / 10` as cm); `src/tests/StereoProcessorTest.py:43` (prints the baseline as "cm") |

## Summary

The baseline, and therefore every depth, is in **whatever unit was used for the checkerboard square size
during calibration**. The calibration file doesn't record that unit, and the code assumes millimetres in some
places and centimetres in others.

## Why it happens

`getBaseline()` returns `abs(1 / Q[3, 2])`. `Q` comes from `cv2.stereoRectify` using the translation `T`, and `T` comes
out in the units of the calibration target's square size. The `.npz` schema has no unit field, and nothing in the
config tells the code which unit was used.

## Effects

If the squares were entered in millimetres, everything is consistent. If they were entered in centimetres
(or inches), **every depth is wrong by a constant factor with no error**. Illustration (made-up numbers):

| Square size entered | `getBaseline()` | `z_mm` computed | `Orchestrator` shows (`z_mm / 1000`) | Real distance |
|---|---|---|---|---|
| 25 (mm) | 60.0 | 750 | 0.75 m | 0.75 m |
| 2.5 (cm) | 6.0 | 75 | **0.075 m** (10x too small) | 0.75 m |

Also, the output key is named `z_mm` and the tuner prints centimetres, so a reader can't tell which unit the
number is in, and `StereoProcessorTest` labels the same baseline "cm".

## Suggested fixes

- Write the unit into the calibration file (for example `square_size_mm`, or a `units` string) and have
  `StereoProcessor` convert the baseline to millimetres once, so the rest of the code can rely on mm.
- Fix the mislabelled print in `StereoProcessorTest` and keep one display convention (metres in the
  overlay, millimetres in data).
- Document the requirement in [`docs/setup.md`](../setup.md) (done).
