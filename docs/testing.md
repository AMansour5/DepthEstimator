# Testing

## Run

From the repository root. A plain `python -m pytest` collects **34 tests in 7 files**, but 11 of them need a camera, a display,
the YOLO weights, or files that exist only on the author's machine (and two of them open windows and wait for `q`). To run
only the tests that work anywhere (**23 tests, no hardware**):

```bash
python -m pytest -q depth_estimator/tests/test_depth_estimator.py depth_estimator/tests/test_stereo_dead_band.py depth_estimator/tests/test_configurator.py \
  depth_estimator/tests/test_stereo_camera.py::test_slow_consumer_gets_latest_frame \
  depth_estimator/tests/test_stereo_camera.py::test_frames_are_not_returned_twice \
  depth_estimator/tests/test_stereo_camera.py::test_release_stops_reader_thread \
  depth_estimator/tests/test_stereo_camera.py::test_camera_rejects_negotiated_resolution_mismatch
```

The two mismatch regression tests are included via `test_stereo_dead_band.py` and the fake-camera case above. The portable
subset is 23 tests; the other 11 are marked in the table below. The reasons, and a proposal to mark them so that `pytest`
skips them by default, are in
[P06](problems/06-tests-cannot-fail.md).

## What each test file does

| File | Tests | Needs | What it checks |
|---|---|---|---|
| `test_depth_estimator.py` | 10 | nothing | the depth maths on synthetic disparity maps (below) |
| `test_stereo_dead_band.py` | 5 | nothing | `computeDisparity` recovers the left edge and keeps the input's shape, pads **after** resizing and honours an overridden `numDisparities`; `rectifyImages` rejects a wrong-sized right image ([P01](problems/01-sgbm-dead-band.md), [P02](problems/02-frame-size-vs-calibration.md)); the left-edge tint follows the map's validity and is skipped when no column is valid |
| `test_configurator.py` | 4 | nothing (`test_load_camera_config` asserts **this machine's** camera config) | `setConfig` creates a missing file, merges untouched keys, and resolves absolute/package-relative artifact paths |
| `test_stereo_camera.py` | 7 | 3 need a camera and a display (`test_camera_open`, `test_frame_capture`, `test_view_feed`, which loops until `q`); 4 use a fake capture | a reported resolution mismatch is rejected; a slow consumer gets the **latest** frame, no frame is returned twice, and `release()` stops the reader thread ([P02](problems/02-frame-size-vs-calibration.md), [P11](problems/11-possible-camera-latency.md)) |
| `test_stereo_processor.py` | 5 | the real calibration and sample images at absolute `/home/mansour/...` paths | construction, rectification, focal length, baseline and disparity, each only asserting `is not None` |
| `test_object_detector.py` | 2 | the YOLO weights, a sample image at an absolute path, and a window (`test_detect_objects` waits for `q` if anything is detected) | the model loads and detection returns something (`is not None`) |
| `test_disparity_tuner.py` | 1 | a camera and a display | launches the interactive tuner; it has no assertion |

So the real regression value is in the first four rows. **Not covered by a pytest regression test**: the P03 sentinel clamp
(for the configured value or an override), the P04 exceptions, the P08 unit,
`Orchestrator.processFrame`, and the failure paths of `Configurator` ([P06](problems/06-tests-cannot-fail.md)). P03 is
demonstrated by [`p03_min_disparity.py`](problems/evidence/p03_min_disparity.py), which exercises real SGBM on synthetic
stereo pairs and verifies both configured and overridden values. `depth_estimator/tests` is excluded from the installed package.

## What `test_depth_estimator.py` covers

It builds disparity maps with `numpy` (full-resolution 1920x1080 frame, disparity at scale 0.5) and checks:

- a known depth (`Z = f * s * B / d` gives exactly 750 mm for the chosen numbers) and the returned sampling region;
- background around an object is ignored (the central crop plus the median beat a whole-box average);
- invalid pixels (`-1`) are ignored;
- no valid disparity, or a box outside the map, returns `None`;
- sparse valid pixels and widely spread disparities are flagged `reliable = False`;
- a full-resolution (`scale = 1.0`) map, using the default config values;
- `estimateDepths` keeps the order of the detections;
- invalid constructor arguments raise `ValueError`.

It deliberately does **not** run SGBM, so it cannot catch problems that come from SGBM's real output (for example
[P03](problems/03-invalid-disparity-assumes-min-disparity-zero.md)). Those are demonstrated by the scripts in
[`problems/evidence/`](problems/evidence/README.md), which use real SGBM on synthetic stereo pairs and end with a
`VERDICT` line. `test_stereo_dead_band.py` is the one test file that runs real SGBM.

## Testing the orchestrator without hardware

`Orchestrator` accepts its components in the constructor, so it can be driven with fakes:

```python
orch = Orchestrator(camera=FakeCamera(), processor=FakeProcessor(), detector=FakeDetector())
result = orch.processFrame(left, right)       # no camera, no GPU, no window
```

A fake processor needs `getFocalLength()`, `getBaseline()`, `process_scale`, `matcher_params`, `rectifyImages()` and
`computeDisparity(left, right)`. `evidence/p04_detector_failure.py` contains a working example, including a stand-in for
`ultralytics` so no weights are needed.

## Writing a test that needs a calibration

The real calibration is git-ignored. `docs/problems/evidence/common.py` has `synthetic_calibration(path, ...)`, which writes a
file in the current format (including the required `square_size_mm` and `checkerboard`), and `make_processor(matcher_params)`,
which builds a real `StereoProcessor` for disparity-only tests without any file. Use them (or copy them into `depth_estimator/tests`)
instead of the author's files.
