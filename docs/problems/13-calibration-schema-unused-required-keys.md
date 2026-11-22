# P13: Calibration metadata broke compatibility with legacy files

| | |
|---|---|
| **Severity** | Low |
| **Status** | **Fixed**. The loader accepts old files without optional metadata, warns when the unit marker is absent, and rejects unsupported explicit units (`evidence/p13_calibration_schema.py` prints `VERDICT FIXED`). |
| **Where** | `depth_estimator/services/StereoProcessor.py` (`__loadCalibration`) |

## Summary

Older calibration files omitted `square_size_mm` and `checkerboard`, but the loader required both keys even though they
were only descriptive metadata. The current schema makes them optional and adds an explicit `translation_unit="mm"`
contract for new calibration files. Legacy files lacking that marker continue to load with a warning that assumes `T`
is already in millimetres.

## Evidence

The regression evidence verifies that:

- files from the original schema load and emit the assumed-mm warning;
- files marked with `translation_unit="mm"` load, with optional metadata;
- explicit unsupported units fail clearly; and
- changing `square_size_mm` alone does not rescale `T` (see [P08](08-implicit-units.md)).

## How to verify

Run `python3 docs/problems/evidence/p13_calibration_schema.py`; it should end with `VERDICT FIXED`.
