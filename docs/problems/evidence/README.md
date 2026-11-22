# Evidence scripts

Each script checks one documented problem against **the current code**, on **synthetic data**, using your real classes
from `depth_estimator/` and your real values from `depth_estimator/config/*.yaml`. No camera, real calibration file or YOLO weights are needed.
Every script ends with a line `VERDICT FIXED | PARTLY FIXED | STILL PRESENT`, so you can re-run them after a change and see
what moved.

```bash
pip install numpy opencv-python pyyaml zope.interface pytest
python3 docs/problems/evidence/p01_dead_band.py        # run from anywhere
for f in docs/problems/evidence/p*.py; do python3 "$f" | tail -2; done     # all of them, verdicts only
```

| Script | Problem | What it shows | Current verdict |
|---|---|---|---|
| `p01_dead_band.py` | [P01](../01-sgbm-dead-band.md) | the raw SGBM dead band, then `computeDisparity` with padding; residual extrapolated edge | FIXED |
| `p02_frame_size.py` | [P02](../02-frame-size-vs-calibration.md) | both eye-size mismatches raise; camera rejects a different negotiated resolution | FIXED |
| `p03_min_disparity.py` | [P03](../03-invalid-disparity-assumes-min-disparity-zero.md) | configured and overridden `minDisparity` values leave no positive SGBM sentinel pixels | FIXED |
| `p04_detector_failure.py` | [P04](../04-silent-detector-failure.md) | load and runtime detector failures now raise | FIXED |
| `p05_not_runnable.py` | [P05](../05-not-runnable-from-clean-clone.md) | what git tracks, cwd-relative paths, declared dependencies | PARTLY FIXED |
| `p06_tests_cannot_fail.py` | [P06](../06-tests-cannot-fail.md) | what pytest collects, which tests need hardware or this machine, which problems have a regression test, a clean-clone run | PARTLY FIXED |
| `p09_configurator.py` | [P09](../09-configurator-error-handling-and-rewrites.md) | `fetchData` raises; `setConfig` still drops comments and a failed write empties the file | PARTLY FIXED |
| `p10_interpolation.py` | [P10](../10-duplicated-disparity-code.md) | source scan for duplicated disparity code; the old `INTER_AREA` vs `INTER_LINEAR` measurement | FIXED |
| `p12_packaging.py` | [P12](../12-non-editable-install-broken.md) | the renamed package ships all YAML config resources and declares third-party imports | FIXED |
| `p13_calibration_schema.py` | [P13](../13-calibration-schema-unused-required-keys.md) | old calibration files are rejected; the stored unit is ignored | STILL PRESENT |

P07 (needs ultralytics/PyTorch), P08 (needs your calibration; partly covered by `p13`) and P11 (needs your camera) have no
dedicated script; their files say how to check. P11's reader-thread behaviour is covered by tests in
`depth_estimator/tests/test_stereo_camera.py`.

`common.py` holds the shared helpers: a synthetic stereo-scene generator with known disparities, an SGBM builder that mirrors
`StereoProcessor`, `make_processor` (a real `StereoProcessor` without a calibration file), a synthetic calibration writer
(with the now-required `square_size_mm` and `checkerboard` keys) and `verdict()`.

**Illustrative numbers.** Where a script uses a focal length or baseline (`1000 px`, `60 mm`), they are made-up values, not your
camera's.

**Verdicts are for the code at the time of writing.** They are computed from behaviour (or, where noted, from a source scan), not
hard-coded, so a script flips to `FIXED` when the code is fixed.
