# Setup and running

## Requirements

- **Hardware:** a side-by-side stereo camera that appears as a single video device (the default config expects
  `/dev/video2`, i.e. Linux/V4L2, delivering 3840x1080 MJPG). A GPU is recommended for YOLO but not required: with
  `device: null` ultralytics falls back to the CPU ([P07](problems/07-hardcoded-cuda-device.md)).
- **Python:** 3.9 or newer (`requires-python` in `pyproject.toml`; use whatever your PyTorch install supports).
- **Packages:** `pyproject.toml` declares `opencv-python`, `numpy`, `PyYAML` and `zope.interface`, but **not `ultralytics`**
  ([P12](problems/12-non-editable-install-broken.md)). From the repository root:

  ```bash
  pip install -e .                 # the project and its declared dependencies, plus the estimate-depth / tune-disparity commands
  pip install ultralytics          # YOLO (installs PyTorch); not declared yet
  pip install -e ".[dev]"          # optional: pytest
  ```

  Use an **editable** install (`-e`): a regular `pip install .` does not ship `config/`, and the program can't find its
  settings ([P12](problems/12-non-editable-install-broken.md)). Use `opencv-python`, not `opencv-python-headless`: the
  program opens windows with `cv2.imshow`. There is no `requirements.txt`; `pyproject.toml` is the list.

## The two files you must provide

Both are git-ignored (`*.npz`, `*.pt`), so a fresh clone does not contain them
([P05](problems/05-not-runnable-from-clean-clone.md)). The folders `src/matrices/` and `src/models/` exist (a tracked
`.gitkeep` each).

### 1. Stereo calibration: `src/matrices/stereo_calib.npz`

Produced by your capture and calibration scripts (they are not part of this repository). `StereoProcessor`
expects a NumPy `.npz` with these keys, **all required** (extra keys such as `E`, `F`, `rms_left`, `rms_right` are ignored):

| Key | Meaning |
|---|---|
| `K1`, `K2` | 3x3 camera matrices (left, right) |
| `D1`, `D2` | distortion coefficients (left, right) |
| `R`, `T` | rotation and translation from the left to the right camera |
| `img_size` | `(width, height)` of **one** eye's image, e.g. `(1920, 1080)` |
| `rms_stereo` | stereo calibration RMS reprojection error (float; only read, not used in calculations) |
| `square_size_mm` | the checkerboard square size you entered (float). Required, **but only recorded**: nothing uses it ([P13](problems/13-calibration-schema-unused-required-keys.md)) |
| `checkerboard` | inner-corner counts `(columns, rows)` of the board (two ints). Required, only recorded |

A calibration file from before `square_size_mm` and `checkerboard` were added fails to load with
`RuntimeError: Failed to load calibration file: 'square_size_mm is not a file in the archive'`
([P13](problems/13-calibration-schema-unused-required-keys.md)); add the two keys with `numpy.savez`.

Two things that are easy to get wrong:

- **`img_size` must equal the size of each half of the camera frame** at runtime. A mismatch in either eye raises
  `DifferentImageSizeError`; if the camera reports a different resolution than requested, `StereoCamera.open()` raises
  `RuntimeError` ([P02](problems/02-frame-size-vs-calibration.md)).
- **Units.** Depth comes out in the unit you used for the checkerboard square size when calibrating. The code
  assumes **millimetres**, and `square_size_mm` does not convert anything. If you entered centimetres, every depth is wrong by
  a constant factor and nothing warns you ([P08](problems/08-implicit-units.md)).

The calibration is read at start-up and the rectification maps are built once.

### 2. YOLO weights: `src/models/yolov8n.pt`

The `model_path` in `config/object_detector.yaml`. Any ultralytics detection model works (`yolov8s.pt` is more
accurate and slower). One way to obtain the nano model:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"   # downloads yolov8n.pt into the current folder
mkdir -p src/models && mv yolov8n.pt src/models/
```

## Run from the project root

Both `calibration_path` and `model_path` are **relative paths**, so start every command from the repository root
(the folder that contains `config/` and `src/`) ([P05](problems/05-not-runnable-from-clean-clone.md)):

```bash
python -m src.services.Orchestrator       # the live demo; press q in the window to quit   (or: estimate-depth)
python -m src.tuners.DisparityTuner       # interactive SGBM tuning (see tuning-guide.md)  (or: tune-disparity)
python -m pytest -q                       # the tests (see testing.md: some need a camera, a display or the author's files)
```

The two console commands exist after `pip install -e .` and also need the repository root as the working directory.

## What you should see

The demo window has two panels:

- **Left:** the rectified left image with each detection, its class, confidence and distance in metres. A thin inner
  rectangle shows the region actually sampled for depth.
- **Right:** the disparity map with the same boxes, so a missing depth shows up as a black hole under the box. A dark-red
  strip with a red edge line along the left side marks an invalid region that touches the left edge
  ([P01](problems/01-sgbm-dead-band.md)).
- A green status line: `YOLO <ms> | SGBM <ms> | <fps> FPS`.

Box colours: **green** = depth looks reliable, **orange** (with `?`) = computed but suspicious, **red** = no usable
disparity in the sampled region.

If a component fails (missing model, a detector error, a wrong frame size), the demo prints the error with a traceback and
exits with status 1 instead of showing a window without boxes ([P04](problems/04-silent-detector-failure.md)).

## First-run checklist

1. Make sure `combined_width` / `combined_height` in `stereo_camera.yaml` match the size the camera reports, and that each
   half matches the calibration's `img_size`. A reported/requested mismatch fails at `open()`; a calibration mismatch fails
   at rectification ([P02](problems/02-frame-size-vs-calibration.md)).
2. The tinted strip on the left of the disparity panel is narrow. A wide one means that part of the scene has no matches
   (texture, occlusion); the strip is no longer caused by `numDisparities` ([P01](problems/01-sgbm-dead-band.md)).
3. Boxes appear. A missing model or a failing detector now stops the program with an error
   ([P04](problems/04-silent-detector-failure.md)); no boxes with a healthy console means nothing was detected.
4. A known distance reads correctly: hold an object at a measured distance and compare. If it is off by a constant
   factor, check units ([P08](problems/08-implicit-units.md)).
