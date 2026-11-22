# API reference

Signatures are as in the repository (`main`). Methods named `__like_this` are private and not listed.
Unless noted otherwise, images are OpenCV BGR `numpy` arrays.

## `StereoCamera`: `src/services/StereoCamera.py`

Implements `ICamera` through `zope.interface`.

`StereoCamera(camera_cfg: dict)`: keys `camera_index` (default `0`), `combined_width` (`1280`), `combined_height` (`480`),
`preview_width` (`640`), `frame_timeout` (`2.0`, seconds). Nothing is opened until `open()`. The defaults are not the
project's values: set them in `config/stereo_camera.yaml` ([P02](problems/02-frame-size-vs-calibration.md)).

| Method | Returns / does |
|---|---|
| `open()` | Opens the device, requests the width/height, MJPG and 30 FPS, checks whether `CAP_PROP_BUFFERSIZE=1` was honoured (prints a `WARNING` if not), and raises `RuntimeError` if opening/setup fails or the camera reports a different resolution. On success, **starts a daemon reader thread** that keeps only the newest frame ([P02](problems/02-frame-size-vs-calibration.md)) |
| `getFrames()` | `(left, right)` halves of the **newest** combined frame (split at `width // 2`). It waits up to `frame_timeout` seconds for a frame newer than the last one returned, so no frame is returned twice. Returns `(None, None)` if a read failed or the wait timed out; raises `RuntimeError` if the camera isn't open ([P11](problems/11-possible-camera-latency.md)) |
| `getCapture()` | the underlying `cv2.VideoCapture`, or `None` |
| `release()` | stops the reader thread (waits up to 2 s), then releases the capture |
| `resize_for_preview(img)` | `img` resized to `preview_width`, keeping the aspect ratio |

## `StereoProcessor`: `src/services/StereoProcessor.py`

`StereoProcessor(processor_cfg: dict)`: needs `calibration_path`, `process_scale`, `matcher_params`. The constructor
builds the SGBM matcher, loads the calibration and computes the rectification maps once. Raises `RuntimeError` if the
calibration file is missing or invalid (including a file without `square_size_mm` / `checkerboard`,
[P13](problems/13-calibration-schema-unused-required-keys.md)), the matcher settings are wrong, or rectification fails.

Public attributes: `process_scale`, `matcher_params`, `matcher`, the calibration (`K1 D1 K2 D2 R T`, `calib_img_size`,
`rms_stereo`, `square_size_mm`, `checkerboard_dims`), the rectification maps (`map1x map1y map2x map2y`) and `Q`.

| Method | Returns / does |
|---|---|
| `rectifyImages(left_img, right_img)` | `(rectified_left, rectified_right)`, each of size `calib_img_size`. Raises `ValueError` for `None` input, `DifferentImageSizeError` if **either** image's size differs from the calibration's ([P02](problems/02-frame-size-vs-calibration.md)), and `RuntimeError` on remapping failure |
| `computeDisparity(left_img, right_img, overrides=None)` | `float32` disparity map in pixels at the process scale (input is **BGR rectified**; it converts to grey, downscales with `INTER_AREA`, pads both images on the left by `numDisparities`, matches, and crops the padding, so the map has the size of the downscaled left image with **no artificial dead band**, [P01](problems/01-sgbm-dead-band.md)). Unmatched pixels are `-1`, including when `minDisparity` is overridden. `overrides` may hold any `matcher_params` key and/or `"process_scale"` to use instead of the configured ones (the tuner uses this; see [P03](problems/03-invalid-disparity-assumes-min-disparity-zero.md)) |
| `buildMatcher(overrides=None)` | a `cv2.StereoSGBM` built from `matcher_params` with `overrides` taking precedence. `mode` is one of `SGBM`, `HH`, `SGBM_3WAY` (default if omitted), `HH4`; `P1 = 8*blockSize^2`, `P2 = 32*blockSize^2`. Raises `RuntimeError` on an invalid mode or missing key |
| `getFocalLength()` | focal length in pixels at **full resolution**: `abs(Q[2,3])` |
| `getBaseline()` | baseline: `abs(1 / Q[3,2])`, in the unit of the calibration square size; `square_size_mm` is not used to convert it ([P08](problems/08-implicit-units.md)) |

Class attribute `_SGBM_MODES` maps the four mode names to the OpenCV constants.

## `ObjectDetector`: `src/services/ObjectDetector.py`

`ObjectDetector(detector_cfg: dict)`: keys `model_path`, `conf_threshold` (0.5), `classes` (`None`), `device` (`None`),
`yolo_imgsz` (640). Loads the model; **raises `YoloModelNotFound`** (with the path and the original error) if loading fails.

`detect(image)` returns a list of dictionaries `{"box": [x1, y1, x2, y2], "conf": float, "cls": int, "name": str}`. `[]` means
nothing was found. **Any failure raises `DetectionError`**; it is never turned into `[]` or `None`
([P04](problems/04-silent-detector-failure.md)).

## Exceptions: `src/exceptions/`

| Exception | Raised by | Meaning |
|---|---|---|
| `YoloModelNotFound` | `ObjectDetector.__init__` | the YOLO model could not be loaded (missing or unreadable file, wrong ultralytics version) |
| `DetectionError` | `ObjectDetector.detect` | the model call failed (for example an unusable `device`, or out of memory) |
| `DifferentImageSizeError` | `StereoProcessor.rectifyImages` | either image's size differs from the calibration's |

All three take a message and expose it as `.message`.

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

A pixel counts as valid when its disparity is `> 0`. The depth dict keys are listed in
[Architecture](architecture.md#data-that-moves-between-components); the method is explained in
[Depth estimation](depth-estimation.md).

## `Orchestrator`: `src/services/Orchestrator.py`

`Orchestrator(camera=None, processor=None, detector=None, depth_estimator=None)`: any component you omit is built from
`config/*.yaml`; passing your own (or fakes) makes the class testable without hardware. A missing config file raises
`FileNotFoundError` and malformed YAML `RuntimeError` (both from `Configurator`); an empty file also raises `RuntimeError`.

Class constants: `WINDOW_NAME`, `DISPLAY_WIDTH = 720` (width of each display panel).

| Method | Does |
|---|---|
| `processFrame(left_frame, right_frame)` | One fork-join step (no drawing, no GUI). Returns `{rect_left, disparity, detections, depths, yolo_ms, sgbm_ms}`. Exceptions from the detector or from SGBM propagate (`DetectionError`, ...) |
| `run()` | Opens the camera (raises `RuntimeError` if it can't), loops until `q`, Ctrl+C, or a failed read, then calls `close()`. An exception from `processFrame` ends the loop, after `close()` |
| `close()` | shuts down the worker, releases the camera, closes windows |

Run it with `python -m src.services.Orchestrator` or, after `pip install -e .`, `estimate-depth`. `main()` prints an
error with its traceback and exits with status 1 on any exception.

## `Configurator`: `src/utils/Configurator.py`

Constants: `STEREO_CAMERA`, `OBJECT_DETECTOR`, `STEREO_PROCESSOR`, `DEPTH_ESTIMATOR`.

| Method | Returns / does |
|---|---|
| `getProjectRoot()` (static) | path of the folder that contains both `config/` and `src/`; raises `FileNotFoundError` if not found (which is what an installed, non-editable copy does, [P12](problems/12-non-editable-install-broken.md)) |
| `fetchData(data_type)` | the parsed YAML as a `dict` (`None` for an empty file). **Raises**: `TypeError` for an unknown type, `FileNotFoundError` for a missing file, `RuntimeError` for malformed YAML |
| `setConfig(data_type, new_data)` | merges `new_data` into the file's **top-level keys** and rewrites the file (comments are lost, and a failed write leaves it empty, [P09](problems/09-configurator-error-handling-and-rewrites.md)) |

## `DisparityVisualizer`: `src/utils/DisparityVisualizer.py`

Static helpers shared by the orchestrator and the tuner.

| Method | Does |
|---|---|
| `drawText(img, text, org, scale=0.5)` | white text with a black outline, drawn in place |
| `colorizeDisparity(disparity, num_disparities)` | `COLORMAP_TURBO` image; pixels with disparity `<= 0` are black |
| `highlightLeftInvalidBand(colored, disparity)` | a copy of `colored` with the contiguous invalid strip at the left edge tinted dark red and its right boundary drawn as a red line. The boundary is the first column with more than 50% valid pixels; if there is none, or the strip has zero width, `colored` is returned unchanged ([P01](problems/01-sgbm-dead-band.md)) |

## `DisparityTuner`: `src/tuners/DisparityTuner.py`

`DisparityTuner()`: builds its own `StereoProcessor` and `StereoCamera` from config. `tuneDisparity()` runs the
interactive loop (see the [tuning guide](tuning-guide.md)). Class constant `Z_MIN_MM = 500.0`. The module has a `main()`:
run it with `python -m src.tuners.DisparityTuner` or `tune-disparity`.

## `ICamera`: `src/interfaces/ICamera.py`

`zope.interface` interface describing `open()`, `getFrames()`, `getCapture()` and `release()`.
