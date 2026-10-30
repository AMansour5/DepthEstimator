# Evidence scripts

Each script reproduces one documented problem on **synthetic data**, using your real classes from `src/` and your real
values from `config/*.yaml`. No camera, calibration file or YOLO weights are needed.

```bash
pip install numpy opencv-python pyyaml zope.interface pytest
python docs/problems/evidence/p01_dead_band.py        # run from anywhere
```

| Script | Problem | What it shows |
|---|---|---|
| `p01_dead_band.py` | [P01](../01-sgbm-dead-band.md) | the invalid left band, identical objects inside/outside it, and the padding fix |
| `p02_frame_size.py` | [P02](../02-frame-size-vs-calibration.md) | a wrong frame size is rectified without error |
| `p03_min_disparity.py` | [P03](../03-invalid-disparity-assumes-min-disparity-zero.md) | the `minDisparity > 0` sentinel turning into a wrong "reliable" depth |
| `p04_detector_failure.py` | [P04](../04-silent-detector-failure.md) | a detector that failed to load looks like an empty scene |
| `p05_not_runnable.py` | [P05](../05-not-runnable-from-clean-clone.md) | missing artifacts and working-directory-dependent paths |
| `p06_tests_cannot_fail.py` | [P06](../06-tests-cannot-fail.md) | pytest collects 2 tests; a wrong expectation still "passes" |
| `p09_configurator.py` | [P09](../09-configurator-error-handling-and-rewrites.md) | comments lost on rewrite; errors returned as `None` |
| `p10_interpolation.py` | [P10](../10-duplicated-disparity-code.md) | `INTER_AREA` vs `INTER_LINEAR`: no measurable effect today |

P07 (needs ultralytics/PyTorch), P08 (needs your calibration) and P11 (needs your camera) have no script; their files say how to check.

`common.py` holds the shared helpers: a synthetic stereo-scene generator with known disparities, an SGBM builder that mirrors
`StereoProcessor`, and a synthetic calibration writer.

**Illustrative numbers.** Where a script uses a focal length or baseline (`1000 px`, `60 mm`), they are made-up values, not your
camera's.
