# Setup and running

## Requirements

- **Hardware:** a side-by-side stereo camera that appears as a single video device (the default config expects
  `/dev/video2`, i.e. Linux/V4L2, delivering 3840x1080 MJPG). An NVIDIA GPU is recommended for YOLO; see
  [P07](problems/07-hardcoded-cuda-device.md).
- **Python:** 3.8 or newer (the floor set by ultralytics; use whatever your PyTorch install supports).
- **Packages** (the repository has no `requirements.txt`; this list comes from the imports):

  ```bash
  pip install numpy opencv-python pyyaml ultralytics zope.interface pytest
  ```

  Use `opencv-python`, not `opencv-python-headless`: the program opens windows with `cv2.imshow`.
  `ultralytics` installs PyTorch. `pytest` is only for the tests.

## The two files you must provide

Both are git-ignored (`*.npz`, `*.pt`), so a fresh clone does not contain them
([P05](problems/05-not-runnable-from-clean-clone.md)).

### 1. Stereo calibration: `src/matrices/stereo_calib.npz`

Produced by your capture and calibration scripts (they are not part of this repository). `StereoProcessor`
expects a NumPy `.npz` with exactly these keys:

| Key | Meaning |
|---|---|
| `K1`, `K2` | 3x3 camera matrices (left, right) |
| `D1`, `D2` | distortion coefficients (left, right) |
| `R`, `T` | rotation and translation from the left to the right camera |
| `img_size` | `(width, height)` of **one** eye's image, e.g. `(1920, 1080)` |
| `rms_stereo` | stereo calibration RMS reprojection error (float; only read, not used in calculations) |

Two things that are easy to get wrong:

- **`img_size` must equal the size of each half of the camera frame** at runtime, or rectification silently produces
  a mostly-black image ([P02](problems/02-frame-size-vs-calibration.md)).
- **Units.** Depth comes out in the unit you used for the checkerboard square size when calibrating. The code
  assumes **millimetres**. If you entered centimetres, every depth is wrong by a constant factor and nothing warns
  you ([P08](problems/08-implicit-units.md)).

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
(the folder that contains `config/` and `src/`):

```bash
python -m src.services.Orchestrator        # the live demo; press q in the window to quit
python -m src.tests.DisparityTunerTest     # interactive SGBM tuning (see tuning-guide.md)
python -m pytest -q                        # the automated tests (see testing.md)
```

## What you should see

The demo window has two panels:

- **Left:** the rectified left image with each detection, its class, confidence and distance in metres. A thin inner
  rectangle shows the region actually sampled for depth.
- **Right:** the disparity map with the same boxes, so a missing depth shows up as a black hole under the box.
- A green status line: `YOLO <ms> | SGBM <ms> | <fps> FPS`.

Box colours: **green** = depth looks reliable, **orange** (with `?`) = computed but suspicious, **red** = no usable
disparity in the sampled region.

## First-run checklist

1. The console prints no `WARNING: camera did not accept the requested resolution...` line. If it does, fix
   `stereo_camera.yaml` first.
2. The left half of the disparity panel isn't solid black ([P01](problems/01-sgbm-dead-band.md)).
3. Boxes appear. If you get a normal FPS counter and *never* any boxes, the detector probably failed to load
   ([P04](problems/04-silent-detector-failure.md)); look for `Error: Failed to ...` lines in the console.
4. A known distance reads correctly: hold an object at a measured distance and compare. If it is off by a constant
   factor, check units ([P08](problems/08-implicit-units.md)).
