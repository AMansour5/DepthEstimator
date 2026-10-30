# Testing

## Run

From the repository root:

```bash
python -m pytest -q                              # what pytest discovers (see below)
python -m src.tests.DepthEstimatorTest           # the depth-math tests (10 tests, no hardware)
```

## What each test file does

| File | Needs hardware? | Can it fail? | Run with |
|---|---|---|---|
| `test_configurator_set_config.py` | no | **yes**: real pytest tests of `Configurator.setConfig` | `pytest` |
| `DepthEstimatorTest.py` | no | **yes**: plain `assert`s on synthetic disparity maps | `python -m src.tests.DepthEstimatorTest` (not collected by pytest) |
| `ConfiguratorTest.py` | no | **no**: assertions are inside `try/except` | `python -m src.tests.ConfiguratorTest` |
| `StereoProcessorTest.py` | calibration + sample images at `/home/mansour/...` | **no** (same reason) | `python -m src.tests.StereoProcessorTest` |
| `ObjectDetectorTest.py` | model + a sample image at `/home/mansour/...` | **no** | `python -m src.tests.ObjectDetectorTest` |
| `StereoCameraTest.py` | camera + display | yes (asserts), manual | `python -m src.tests.StereoCameraTest` |
| `DisparityTunerTest.py` | camera + display | no; it is really the tuner's launcher | `python -m src.tests.DisparityTunerTest` |

So `pytest` reports **2 tests**, and a green run says little. Details and fixes in
[P06](problems/06-tests-cannot-fail.md).

## What `DepthEstimatorTest` covers

It builds disparity maps with `numpy` (full-resolution 1920x1080 frame, disparity at scale 0.5) and checks:

- a known depth (`Z = f * s * B / d` gives exactly 750 mm for the chosen numbers) and the returned sampling region;
- background around an object is ignored (the central crop plus the median beat a whole-box average);
- invalid pixels (`-1`) are ignored;
- no valid disparity, or a box outside the map, returns `None`;
- sparse valid pixels and widely spread disparities are flagged `reliable = False`;
- a full-resolution (`scale = 1.0`) map, using the default config values;
- `estimateDepths` keeps the order of the detections;
- invalid constructor arguments raise `ValueError`.

It deliberately does **not** run SGBM, so it cannot catch problems that come from SGBM's real output
(for example [P01](problems/01-sgbm-dead-band.md) and [P03](problems/03-invalid-disparity-assumes-min-disparity-zero.md)).
Those are demonstrated by the scripts in [`problems/evidence/`](problems/evidence/README.md), which use real SGBM on synthetic
stereo pairs.

## Testing the orchestrator without hardware

`Orchestrator` accepts its components in the constructor, so it can be driven with fakes:

```python
orch = Orchestrator(camera=FakeCamera(), processor=FakeProcessor(), detector=FakeDetector())
result = orch.processFrame(left, right)       # no camera, no GPU, no window
```

A fake processor needs `getFocalLength()`, `getBaseline()`, `process_scale`, `matcher_params`, `rectifyImages()` and
`computeDisparity()`. `evidence/p04_detector_failure.py` contains a working example.
