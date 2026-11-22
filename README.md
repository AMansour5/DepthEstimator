# Depth Estimator

Detects objects with **YOLO** and measures how far away each one is using a **stereo camera**.

A side-by-side stereo camera produces a left and a right image. The program rectifies them, runs YOLO on the left
image, computes a disparity map with OpenCV's SGBM matcher, and converts the disparity inside each detected box into a
distance (`Z = f * B / d`). A live window shows the boxes, their distances and the disparity map.

> **Status: work in progress.** The pipeline runs end to end and the worst silent failures (a broken detector, the
> unmeasurable left third of the frame, a wrong frame size) are fixed. Some problems can still give a plausible but wrong
> distance **without any error**: the unit of depth is assumed to be millimetres, for example. Read
> [Known problems](#known-problems) before trusting the numbers on your own setup.

## How it works

```mermaid
flowchart LR
    CAM["StereoCamera"] --> RECT["StereoProcessor<br/>rectify"]
    RECT --> DET["ObjectDetector<br/>(YOLO, left image)"]
    RECT --> DISP["StereoProcessor<br/>disparity (SGBM)"]
    DET --> DEP["DepthEstimator"]
    DISP --> DEP
    DEP --> OUT["Orchestrator<br/>draw + show"]
```

- YOLO and SGBM run **concurrently** on every frame and are joined before depth is computed, so a box and a disparity
  map always belong to the same frame.
- One distance is reported per box: the **median** of the valid disparities in the **central part** of the box, which
  keeps background pixels from dragging the estimate backwards.
- Each distance carries a `reliable` flag (green / orange `?` / red) so a doubtful value is visible.
- Failures are loud: a missing model, a detector error or a frame of the wrong size stops the program with a message.

Details: [Architecture](docs/architecture.md), [Depth estimation](docs/depth-estimation.md).

## Quick start

```bash
# 1. install from the repository root (an editable install: it needs config/ next to src/)
pip install -e .
pip install ultralytics                  # YOLO and PyTorch; not declared in pyproject.toml yet (P12)

# 2. provide the two git-ignored files (see docs/setup.md for how)
#      src/matrices/stereo_calib.npz    your stereo calibration
#      src/models/yolov8n.pt            YOLO weights

# 3. check config/*.yaml (camera device and resolution; device stays null so YOLO uses a GPU only if there is one)

# 4. run from the repository root
python -m src.services.Orchestrator      # press q in the window to quit (or: estimate-depth)
```

Full instructions, the calibration file format, and a first-run checklist: [docs/setup.md](docs/setup.md).

## Project layout

```
DepthEstimator/
├── config/                    YAML settings: camera, stereo processor, detector, depth estimator
├── docs/                      documentation
│   └── problems/              one file per audited problem, plus evidence/ scripts that check each one
├── pyproject.toml             dependencies and the estimate-depth / tune-disparity commands
└── src/
    ├── exceptions/            YoloModelNotFound, DetectionError, DifferentImageSizeError
    ├── interfaces/ICamera.py  camera interface
    ├── services/              StereoCamera, StereoProcessor, ObjectDetector, DepthEstimator, Orchestrator
    ├── tuners/DisparityTuner.py   interactive SGBM tuning
    ├── utils/                 Configurator (reads and updates config/*.yaml), DisparityVisualizer
    └── tests/
```

Not tracked by git (you provide them): `src/matrices/stereo_calib.npz`, `src/models/*.pt`, the sample images the tests use.

## Configuration at a glance

| File | Controls | Most important keys |
|---|---|---|
| `config/stereo_camera.yaml` | the camera | `camera_index`, `combined_width`, `combined_height` |
| `config/stereo_processor.yaml` | rectification and SGBM | `calibration_path`, `process_scale`, `matcher_params.numDisparities` |
| `config/object_detector.yaml` | YOLO | `model_path`, `conf_threshold`, `device` |
| `config/depth_estimator.yaml` | how a box becomes one distance | `roi_shrink`, `min_valid_frac`, `max_rel_spread` |

Every key is explained in [docs/configuration.md](docs/configuration.md). To tune the stereo matcher interactively
use the [tuning guide](docs/tuning-guide.md) (`python -m src.tuners.DisparityTuner`).

## Documentation

| | |
|---|---|
| [Setup and running](docs/setup.md) | install, provide the calibration and model files, first-run checklist |
| [Architecture](docs/architecture.md) | pipeline, components, data contracts, coordinate spaces, threading, error model |
| [Configuration reference](docs/configuration.md) | every config key |
| [Depth estimation](docs/depth-estimation.md) | the maths, accuracy, working range, limitations |
| [Disparity tuning guide](docs/tuning-guide.md) | using `DisparityTuner` |
| [API reference](docs/api-reference.md) | classes, methods and exceptions |
| [Testing](docs/testing.md) | which tests exist, which ones run without hardware |
| [Known problems](docs/problems/README.md) | 13 audited problems with evidence, effects and fixes |

## Known problems

All problems were checked against the current code (audit at commit `c39cf63`, with P03 re-verified since). **5 are fixed**
(P01 the unmeasurable left band, P03 invalid disparity sentinels, P04 silent detector failure, P07 hard-coded CUDA, P10
duplicated disparity code), **5 are partly fixed**, **1 is
mitigated** and **2 are new**. The ones most likely to affect your numbers or your first run:

| | Problem | Effect |
|---|---|---|
| [P08](docs/problems/08-implicit-units.md) | The unit of depth is assumed to be mm; `square_size_mm` is recorded but unused | a constant-factor error if the calibration used another unit |
| [P02](docs/problems/02-frame-size-vs-calibration.md) | Only the left image's size is checked against the calibration | a wrong right image is rectified silently |
| [P12](docs/problems/12-non-editable-install-broken.md) | `pip install .` ships no `config/`, and `ultralytics` is not declared | the console scripts only work from an editable install |
| [P05](docs/problems/05-not-runnable-from-clean-clone.md) / [P13](docs/problems/13-calibration-schema-unused-required-keys.md) | Paths depend on the working directory; calibration files need two unused keys | a clean clone, or an older calibration, fails to start |

The full index, with severity and verification status, is [docs/problems/README.md](docs/problems/README.md). Each reproducible
problem has a script in [docs/problems/evidence/](docs/problems/evidence/README.md) that prints a `VERDICT` line.

## Testing

```bash
python -m pytest -q src/tests/test_depth_estimator.py src/tests/test_stereo_dead_band.py src/tests/test_configurator.py \
  src/tests/test_stereo_camera.py::test_slow_consumer_gets_latest_frame \
  src/tests/test_stereo_camera.py::test_frames_are_not_returned_twice \
  src/tests/test_stereo_camera.py::test_release_stops_reader_thread        # 20 tests, no hardware needed
```

A plain `python -m pytest` collects 31 tests; 11 need a camera, a display, the model or the author's files. See
[docs/testing.md](docs/testing.md).
