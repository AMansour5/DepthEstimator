# API reference

Signatures are as in the repository (`main`). Methods named `__like_this` are private and not listed.
Unless noted otherwise, images are OpenCV BGR `numpy` arrays.

## `StereoCamera`: `src/services/StereoCamera.py`

Implements `ICamera` through `zope.interface`.

`StereoCamera(camera_cfg: dict)`: keys `camera_index` (default `0`), `combined_width` (`1280`), `combined_height` (`480`),
`preview_width` (`640`). Nothing is opened until `open()`.

| Method | Returns / does |
|---|---|
| `open()` | Opens the device, requests the width/height, MJPG and 30 FPS, prints a `WARNING` if the camera reports another size. On failure it prints the error and leaves the capture as `None` (it does **not** raise); check `getCapture()` |
| `getFrames()` | `(left, right)` halves of one combined frame (split at `width // 2`), or `(None, None)` if the camera isn't open or the read failed |
| `getCapture()` | the underlying `cv2.VideoCapture`, or `None` |
| `release()` | releases the capture |
| `resize_for_preview(img)` | `img` resized to `preview_width`, keeping the aspect ratio |

## `StereoProcessor`: `src/services/StereoProcessor.py`

`StereoProcessor(processor_cfg: dict)`: needs `calibration_path`, `process_scale`, `matcher_params`. The constructor
builds the SGBM matcher, loads the calibration and computes the rectification maps once. Raises `RuntimeError` if the
calibration file is missing/invalid, the matcher settings are wrong, or rectification fails.

Public attributes: `process_scale`, `matcher_params`, `matcher`, the calibration (`K1 D1 K2 D2 R T img_size rms_stereo`),
the rectification maps (`map1x map1y map2x map2y`) and `Q`.

| Method | Returns / does |
|---|---|
| `rectifyImages(left_img, right_img)` | `(rectified_left, rectified_right)`, each of size `img_size`. Raises `ValueError` for `None` input and `RuntimeError` on failure. **Does not check the input size** ([P02](problems/02-frame-size-vs-calibration.md)) |
| `computeDisparity(left_img, right_img)` | `float32` disparity map in pixels at `process_scale` (input is **BGR rectified**; it converts to grey and downscales internally). Unmatched pixels are `minDisparity - 1` ([P03](problems/03-invalid-disparity-assumes-min-disparity-zero.md)) |
| `getFocalLength()` | focal length in pixels at **full resolution**: `abs(Q[2,3])` |
| `getBaseline()` | baseline: `abs(1 / Q[3,2])`, in the unit of the calibration square size ([P08](problems/08-implicit-units.md)) |

Class attribute `_SGBM_MODES` maps `"SGBM"`, `"HH"`, `"SGBM_3WAY"`, `"HH4"` to the OpenCV constants.

## `ObjectDetector`: `src/services/ObjectDetector.py`

`ObjectDetector(detector_cfg: dict)`: keys `model_path`, `conf_threshold` (0.5), `classes` (`None`), `device` (`None`),
`yolo_imgsz` (640). Loads the model. **If loading fails it prints and returns normally** with no `model`
([P04](problems/04-silent-detector-failure.md)).

`detect(image)` returns a list of dictionaries `{"box": [x1, y1, x2, y2], "conf": float, "cls": int, "name": str}`.
`[]` means nothing was found; **`None` means an error occurred** (it was printed). The two are easy to confuse.

## `DepthEstimator`: `src/services/DepthEstimator.py`

`DepthEstimator(depth_cfg: dict, focal_length: float, baseline: float, scale: float = 1.0)`

| Argument | Meaning |
|---|---|
| `depth_cfg` | `roi_shrink` (0.5), `min_valid_frac` (0.2), `max_rel_spread` (0.15) |
| `focal_length` | pixels at full resolution (`StereoProcessor.getFocalLength()`) |
| `baseline` | in calibration units, mm assumed (`StereoProcessor.getBaseline()`) |
| `scale` | the `process_scale` the disparity map was computed at |

Raises `ValueError` for `roi_shrink` outside `(0, 1]` or non-positive `focal_length`, `baseline`, `scale`.

| Method | Returns |
|---|---|
| `computeObjectDepth(disparity, box)` | a depth dict for one box, or `None`. `box` is `(x1, y1, x2, y2)` in full-resolution rectified-left pixels |
| `estimateDepths(disparity, detections)` | a list with one entry (dict or `None`) per detection, in order. `detections` must be a list of dicts with a `"box"` key |

The depth dict keys are listed in [Architecture](architecture.md#data-that-moves-between-components); the method is
explained in [Depth estimation](depth-estimation.md).

## `Orchestrator`: `src/services/Orchestrator.py`

`Orchestrator(camera=None, processor=None, detector=None, depth_estimator=None)`: any component you omit is built from
`config/*.yaml`; passing your own (or fakes) makes the class testable without hardware. Raises `RuntimeError` if a
needed config file can't be loaded.

Class constants: `WINDOW_NAME`, `DISPLAY_WIDTH = 720` (width of each display panel).

| Method | Does |
|---|---|
| `processFrame(left_frame, right_frame)` | One fork-join step (no drawing, no GUI). Returns `{rect_left, disparity, detections, depths, yolo_ms, sgbm_ms}`. Treats a `None` from the detector as "no detections" |
| `run()` | Opens the camera (raises `RuntimeError` if it can't), loops until `q`, Ctrl+C, or a failed read, then calls `close()` |
| `close()` | shuts down the worker, releases the camera, closes windows |

Run it with `python -m src.services.Orchestrator`.

## `Configurator`: `src/utils/Configurator.py`

Constants: `STEREO_CAMERA`, `OBJECT_DETECTOR`, `STEREO_PROCESSOR`, `DEPTH_ESTIMATOR`.

| Method | Returns / does |
|---|---|
| `getProjectRoot()` (static) | path of the folder that contains both `config/` and `src/`; raises `FileNotFoundError` if not found |
| `fetchData(data_type)` | the parsed YAML as a `dict`; **returns `None` (after printing) on any error** ([P09](problems/09-configurator-error-handling-and-rewrites.md)) |
| `setConfig(data_type, new_data)` | merges `new_data` into the file's **top-level keys** and rewrites the file (comments are lost) |

## `DisparityTuner`: `src/tuners/DisparityTuner.py`

`DisparityTuner()`: builds its own `StereoProcessor` and `StereoCamera` from config. `tuneDisparity()` runs the
interactive loop (see the [tuning guide](tuning-guide.md)). Class constant `Z_MIN_MM = 500.0`. `colorizeDisparity(disparity, num_disp)`
is public.

## `ICamera`: `src/interfaces/ICamera.py`

`zope.interface` interface describing `open()`, `getFrames()`, `getCapture()` and `release()`.
