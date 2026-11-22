# P06: The tests are real now, but some can't run on another machine, and several fixes have no tests

| | |
|---|---|
| **Severity** | Medium |
| **Status** | **Partly fixed**. `evidence/p06_tests_cannot_fail.py` prints `VERDICT PARTLY FIXED` |
| **Where** | `depth_estimator/tests/*.py`: `test_object_detector.py:16` and `test_stereo_processor.py:16-17,43-44` (absolute `/home/mansour/...` paths); `test_stereo_camera.py:29-50` (`test_view_feed`), `test_disparity_tuner.py` and `test_object_detector.py:11-40` (GUI loops); `test_configurator.py:4-9` (asserts this machine's camera config); `pyproject.toml` (no pytest configuration) |

## Resolved (`87b2af6`, then `d403a39` and `c39cf63`)

The original complaint was that the tests could not fail and pytest found 2 of them. That is fixed:

- Files are named `test_*.py` with `def test_...` functions, so `python -m pytest` collects **34 tests in 7 files**.
- The `try/except` that swallowed assertion failures is gone (the scan finds no `except` in any test file).
- The depth math has 10 synthetic-disparity tests (`test_depth_estimator.py`); P01 has 4 tests and P02 has 1
  (`test_stereo_dead_band.py`); the camera has 4 fake-capture tests (`test_stereo_camera.py`); and `Configurator.setConfig` has 2.

## Still open

1. **Only 23 of the 34 tests run in a clean clone** (copy of the tracked files, no camera, no display, no model, no
   calibration). The result of running them that way (part D of the script):

   ```
   no camera, display, model or calibration needed : 23 passed
   test_stereo_processor.py (needs calibration+images): 5 failed
   ```

   | Group | Tests | Why it can't run elsewhere |
   |---|---|---|
   | portable | 23 | `test_depth_estimator`, `test_stereo_dead_band`, `test_configurator`, 4 fake-capture camera tests |
   | needs the author's files | 5 | `test_stereo_processor.py`: `depth_estimator/matrices/stereo_calib.npz` and `depth_estimator/images/*.png` are git-ignored and referenced by `/home/mansour/...` |
   | needs model + image + window | 2 | `test_object_detector.py`: weights, absolute path, and `test_detect_objects` blocks on `cv2.imshow` until `q` |
   | needs the camera / a display | 4 | `test_camera_open`, `test_frame_capture`, `test_view_feed` (loops until `q`), `test_run` (launches the tuner) |

   A plain `pytest` therefore hangs or fails on a machine without the hardware, and opens windows on one with it.
2. **One test asserts this machine's configuration.** `test_load_camera_config` expects `camera_index == "/dev/video2"` and
   3840x1080; with any other valid config it raises `AssertionError` (it can fail, but for the wrong reason).
3. **No pytest configuration or markers**, so nothing says which tests are hardware tests or lets CI skip them.
4. **No pytest regression test for several fixes**: the P03 sentinel (configured or override), the P04 exceptions, and the
   P08 unit. P03 does have a standalone synthetic evidence script, but it is not part of the pytest suite. This is how P03
   got "fixed" for the config path and still broke for the override path.

## Suggested fixes

1. Register a marker (`[tool.pytest.ini_options] markers = ["hardware: needs a camera, display, model or the author's files"]`)
   and deselect it by default with `addopts = "-m 'not hardware'"`; run them with `pytest -m hardware`.
2. Replace `/home/mansour/...` with paths relative to the test file, and build a synthetic calibration with
   `tmp_path` (the writer in `evidence/common.py` is a ready-made example) so `StereoProcessor` is testable anywhere.
3. Make `test_load_camera_config` check the keys' types and plausibility, not this machine's values.
4. Add the missing regression tests listed above.

## How to verify

`python3 docs/problems/evidence/p06_tests_cannot_fail.py` and then, after the fixes, `python -m pytest -q` on a clean clone
with no hardware should pass without opening a window.
