# Configuration reference

All configuration lives in `config/*.yaml`. `Configurator` locates the folder from the project root, so it is
found regardless of the working directory (file paths *inside* the YAML are a different matter; see
[P05](problems/05-not-runnable-from-clean-clone.md)).

> The YAML files themselves can't carry these explanations for long: `Configurator.setConfig` (used by the tuner's
> `d` key) rewrites a file and drops its comments ([P09](problems/09-configurator-error-handling-and-rewrites.md)).
> Treat this page as the source of truth.

## `stereo_camera.yaml`

| Key | Default in code | Current | Meaning |
|---|---|---|---|
| `camera_index` | `0` | `/dev/video2` | Device index or path passed to `cv2.VideoCapture` |
| `combined_width` | `1280` | `3840` | Width of the **combined** left+right frame, requested from the camera |
| `combined_height` | `480` | `1080` | Height of the combined frame |
| `preview_width` | `640` | `640` | Only used by `StereoCamera.resize_for_preview` (the camera test) |

Each eye is `combined_width / 2` wide. It **must match** the calibration's `img_size`
([P02](problems/02-frame-size-vs-calibration.md)). The camera is opened with MJPG at 30 FPS.

## `stereo_processor.yaml`

| Key | Meaning |
|---|---|
| `calibration_path` | Path to the calibration `.npz` (relative paths resolve against the **working directory**) |
| `process_scale` | Scale applied to the rectified images **before** SGBM. `0.5` means SGBM runs on 960x540. Smaller is faster and less precise; `1.0` disables downscaling |
| `matcher_params` | The SGBM settings below |

`matcher_params`:

| Key | Current | Valid / typical | Effect |
|---|---|---|---|
| `blockSize` | `9` | odd; 3-11 is typical | Matching window. Larger = smoother, fewer holes, blurrier edges. `P1 = 8*blockSize^2` and `P2 = 32*blockSize^2` are derived from it |
| `numDisparities` | `320` | positive **multiple of 16** | Search range in pixels (of the downscaled image). Sets the nearest measurable distance **and** the width of the unmeasurable left band ([P01](problems/01-sgbm-dead-band.md)) |
| `minDisparity` | `0` | keep at `0` | Start of the search range. Values above 0 break the validity check ([P03](problems/03-invalid-disparity-assumes-min-disparity-zero.md)) |
| `uniquenessRatio` | `10` | about 5-15 | How much better the best match must be than the runner-up. Higher = fewer wrong matches, more holes |
| `speckleWindowSize` | `100` | 0 disables; about 50-200 | Smallest blob size kept; smaller blobs are removed as noise |
| `speckleRange` | `2` | 1-2 is typical | Disparity variation allowed within one blob |
| `disp12MaxDiff` | `5` | `-1` disables | Maximum allowed left-right consistency difference |
| `preFilterCap` | `31` | 1-63 | Clip level for the pre-filtered image |
| `mode` | `SGBM_3WAY` | `SGBM`, `HH`, `SGBM_3WAY`, `HH4` | Algorithm variant. `SGBM_3WAY` is the one chosen here for speed; the others trade speed for different matching behaviour (see OpenCV's `StereoSGBM` documentation) |

The tuner's `d` key writes `process_scale` and the SGBM values back into this file.

## `object_detector.yaml`

| Key | Current | Meaning |
|---|---|---|
| `model_path` | `src/models/yolov8n.pt` | YOLO weights (relative to the working directory) |
| `conf_threshold` | `0.5` | Minimum confidence to keep a detection |
| `classes` | `null` | List of COCO class ids to keep (e.g. `[0, 39, 41]` = person, bottle, cup); `null` = all |
| `device` | `CUDA` | Where YOLO runs. **`null` lets ultralytics choose (GPU if available, else CPU).** `CUDA` fails without a GPU ([P07](problems/07-hardcoded-cuda-device.md)) |
| `yolo_imgsz` | `640` | Size YOLO resizes its input to. Larger = more accurate on small objects, slower |

## `depth_estimator.yaml`

| Key | Current | Meaning |
|---|---|---|
| `roi_shrink` | `0.5` | Fraction of the box (per side) that is sampled, centred. `0.5` = the middle half of the width and height. Must be in `(0, 1]` |
| `min_valid_frac` | `0.2` | A depth is "reliable" only if at least this share of the sampled pixels have a valid disparity |
| `max_rel_spread` | `0.15` | ...and only if (75th - 25th percentile) / median of those disparities is at most this |

There is also a constant, `DepthEstimator.MIN_VALID_PIXELS = 5`: with fewer valid pixels the result is `None`.
See [Depth estimation](depth-estimation.md) for how these interact.

## Values that must agree with each other

| Setting | Must match |
|---|---|
| `combined_width / 2`, `combined_height` | `img_size` stored in the calibration file |
| `process_scale` | the scale the disparity was tuned at (the tuner writes both together) |
| `numDisparities` | the nearest distance you need: `needed = ceil(f_full * process_scale * baseline / Z_min / 16) * 16`; the tuner prints this for `Z_MIN_MM = 500` |
| `device` | the hardware you are actually running on |
