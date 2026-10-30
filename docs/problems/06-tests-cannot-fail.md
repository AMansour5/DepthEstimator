# P06: Most tests can't fail, and `pytest` collects only 2 tests

| | |
|---|---|
| **Severity** | Medium |
| **Status** | Reproduced (`evidence/p06_tests_cannot_fail.py`) |
| **Where** | `src/tests/*.py` (all of them) |

## Summary

Of the test files, only `test_configurator_set_config.py` is a real, discoverable, hardware-free test.
The others either swallow their own failures, depend on files only present on the author's computer,
need hardware, or aren't discovered by `pytest` at all.

> **Part of this is my doing.** `src/tests/DepthEstimatorTest.py` (the file with 10 synthetic-disparity
> tests that I wrote earlier in this conversation) is *not collected by pytest* because of its file and class
> names. It does run with `python -m src.tests.DepthEstimatorTest`, but never as part of a normal test run.

## Why it happens

1. **Assertions inside `try/except Exception`.** `ConfiguratorTest.py:15`, `StereoProcessorTest.py:15,27,...`
   and `ObjectDetectorTest.py` catch the `AssertionError`, print a message, and carry on. The script
   still ends with "All tests completed." and exit code 0.
2. **Hard-coded absolute paths** such as `/home/mansour/Desktop/DepthEstimator/src/images/left/000.png`
   (`ObjectDetectorTest.py:22`, `StereoProcessorTest.py:22-23, 51-52`). On any other machine
   `cv2.imread` returns `None`, which the same `try/except` then swallows.
3. **Discovery.** pytest collects `test_*.py` / `*_test.py` files and `Test*` classes. `DepthEstimatorTest.py` and the
   `*Test.py` files don't match; `ConfiguratorTest.py`'s class is named `TestConfigurator` but the file name still doesn't match.
4. `StereoCameraTest.py` and `DisparityTunerTest.py` need a camera and a display, and so can't run in CI.

## Evidence

```
A) what pytest collects from src/tests
   src/tests/test_configurator_set_config.py::test_set_config_creates_missing_file
   src/tests/test_configurator_set_config.py::test_set_config_merges_and_preserves_untouched_keys
   2 tests collected

B) ConfiguratorTest with a deliberately WRONG config value
Error loading camera config:
   -> returned normally: the test run would still end with 'All tests completed.' and exit code 0
```

## Effects

- A green run proves almost nothing. Regressions such as [P03](03-invalid-disparity-assumes-min-disparity-zero.md) would not be caught.
- The most valuable tests (the depth math) are exactly the ones nobody would run by accident.
- New contributors can't tell which tests are meaningful.

## Suggested fixes

1. Rename `DepthEstimatorTest.py` to `test_depth_estimator.py` and the class to `TestDepthEstimator` (or use plain
   `def test_...` functions).
2. Remove the `try/except` from tests; let assertions fail.
3. Replace hard-coded paths with `tmp_path` fixtures and synthetic data (see `evidence/common.py` for a
   synthetic calibration and a synthetic stereo pair).
4. Mark the camera/GUI tests (`@pytest.mark.hardware`) and skip them unless asked for.
5. Add the commands to the README and run `python -m pytest -q` in CI.

## How to verify a fix

`python -m pytest -q` should list the depth-estimator tests, and deliberately breaking one expectation should turn the run red.
