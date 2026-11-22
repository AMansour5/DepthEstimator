# P08: Calibration translation units can silently put depth on the wrong scale

| | |
|---|---|
| **Severity** | Medium |
| **Status** | **Partly fixed**. New calibration files declare `translation_unit="mm"` and unsupported explicit units fail. Legacy files still assume mm with a warning; verifying their actual scale requires the external calibration producer or a known-distance measurement. |
| **Where** | `depth_estimator/services/StereoProcessor.py` (calibration unit contract and `getBaseline`); `depth_estimator/services/DepthEstimator.py` (result key `z_mm`); `depth_estimator/services/Orchestrator.py:109` (`z_mm / 1000` shown as metres); `depth_estimator/tuners/DisparityTuner.py:75-77` (prints `z_mm / 10` as cm) |

## Summary

`getBaseline()` returns `abs(1 / Q[3, 2])`. Since `Q` is computed from calibration translation `T`, baseline and depth
inherit the unit of `T`. New calibration files now declare `translation_unit="mm"`; the calibration producer must form
checkerboard object points in millimetres so that `T` is in millimetres. The marker is validated but does not rescale `T`.

## What changed

- New files carry an explicit `translation_unit="mm"` declaration. Explicit unsupported units fail instead of silently
  producing depths labelled as millimetres.
- Old calibration files remain loadable. When `translation_unit` is missing, the loader warns and assumes legacy `T` is
  already in millimetres.
- `square_size_mm` and `checkerboard` are optional descriptive metadata. In particular, changing `square_size_mm` alone
  cannot convert an already-computed `T`.

## What remains

The calibration-producing scripts are not in this repository. A producer must write `T` in millimetres and include the
unit marker; the application only checks that the marker says `"mm"`, not that the numeric contents of `T` honor that
claim. A mislabeled new file can therefore still produce a plausible, incorrectly scaled distance. Legacy files also
have no unit metadata, so their scale must be checked against a measured distance before use.

Keep one display convention: metres in the overlay, millimetres in data. The producer's calibration process and a
known-distance check are required to establish that the real scale is correct. **P08 is not fully fixed** until the
external producer writes and marks `T` in millimetres and representative calibrations are checked against known distances.
P13 covers the related file-compatibility issue.

## How to verify

Run `python3 docs/problems/evidence/p13_calibration_schema.py` to check schema handling and unit-marker enforcement; its
`VERDICT FIXED` covers P13's compatibility contract, not the physical scale of an external calibration. Then hold an
object at a measured distance and compare ([`docs/setup.md`](../setup.md), first-run checklist); that real calibration
check cannot be replaced by synthetic data.
