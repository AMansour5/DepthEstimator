# P13: The calibration loader requires two keys that nothing uses, and old calibration files no longer load

| | |
|---|---|
| **Severity** | Low |
| **Status** | **New**, reproduced (`evidence/p13_calibration_schema.py` prints `VERDICT STILL PRESENT`) |
| **Where** | `depth_estimator/services/StereoProcessor.py:55-71` (`__loadCalibration`; the two reads are at `:66-67`); introduced in `db60e9b` |

## Summary

`db60e9b` added `square_size_mm` and `checkerboard` to what `StereoProcessor.__loadCalibration` reads. Both are read with
`data[...]`, so both are **required**, but the values are only stored on the object (`self.square_size_mm`,
`self.checkerboard_dims`) and never read again anywhere in `depth_estimator/`.

## Evidence

```
A) loading calibration files
   with square_size_mm + checkerboard    : loads
   original schema (without them)        : RuntimeError: Failed to load calibration file: 'square_size_mm is not a file in the archive'

B) does the stored unit change the baseline? (same translation T, different square_size_mm)
   square_size_mm= 30.0: getBaseline() = 60.0
   square_size_mm=  3.0: getBaseline() = 60.0

C) uses of the two attributes in depth_estimator/ (outside tests)
   depth_estimator/services/StereoProcessor.py:66: self.square_size_mm = float(data["square_size_mm"])
   depth_estimator/services/StereoProcessor.py:67: self.checkerboard_dims = tuple(int(x) for x in data["checkerboard"])
```

The first run of the older evidence scripts against the current code failed in exactly this way: their synthetic calibration had the
original keys.

## Effects

- **Backward incompatibility with no benefit.** A calibration produced before the change (or by any other tool that writes
  `K1 D1 K2 D2 R T img_size rms_stereo`) fails to load, and the message names a key that nothing needs.
- **It looks like a unit fix but is not one.** The stored size changes nothing in the maths, so the unit ambiguity of
  [P08](08-implicit-units.md) is unchanged.
- **The documentation drifted.** The calibration format in [`docs/setup.md`](../setup.md) listed only the original keys; it is
  updated with this change.
- The error text says "is not a file in the archive", which is NumPy's wording for a missing key and is easy to misread.

## Suggested fixes

Choose one and make the loader match:

1. **Use them.** Apply `square_size_mm` as the unit contract (see [P08](08-implicit-units.md)) and keep the keys required, with a
   clear message: `calibration file is missing 'square_size_mm'; recalibrate or add it`.
2. **Make them optional** (`data["square_size_mm"] if "square_size_mm" in data else None`) and warn that the unit is assumed.

Either way, add a test with a calibration lacking the key (`evidence/common.synthetic_calibration` is a ready-made writer) and
keep [`docs/setup.md`](../setup.md) in sync with the loader.

## How to verify

`python3 docs/problems/evidence/p13_calibration_schema.py` ends with `VERDICT FIXED` once old files load (or fail with a clear
message) and the unit is applied.
