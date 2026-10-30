# Disparity tuning guide

`DisparityTuner` shows the live camera with an adjustable SGBM matcher so you can pick settings by eye and write
them to `config/stereo_processor.yaml`.

## Start it

From the repository root:

```bash
python -m src.tests.DisparityTunerTest
```

(`DisparityTuner` has no `__main__` of its own; that test file is the launcher. It catches and prints any exception.)
At start-up it prints the focal length, the baseline, and the `numDisparities` needed to see objects at
`Z_MIN_MM = 500` (50 cm; change the class constant for a different nearest distance). That start-up number is for
**full resolution**; the green on-screen line gives the number for the *current* process scale, which is the one to use.

## The window

Top row: rectified left | rectified right. Bottom row: grey left | **disparity** (blue/green = far, red = near; black = no
match). Green text shows the process scale, compute FPS, current `numDisparities` and the value needed for `Z_MIN_MM`.

| Control | Effect |
|---|---|
| Click on the rectified left image, the grey image, or the disparity panel | prints the distance at that point (median of a 5x5 patch) and draws a crosshair on those three views. Clicks on the top-right (rectified right) panel are ignored |
| `s` | saves the rectified pair, the disparity image and a `params_*.json` into `disparity_tuning_results/` |
| `d` | **writes the current values into `config/stereo_processor.yaml`** (see the cautions below) |
| `q` | quit |

## Sliders

| Slider | Range / mapping | Notes |
|---|---|---|
| `minDisparity` | 0-10 | **Leave at 0** ([P03](problems/03-invalid-disparity-assumes-min-disparity-zero.md)) |
| `process scale x10` | 0-10, minimum effective scale 0.2 | Main speed control. 5 = half resolution |
| `numDisp x16` | value x 16, minimum 16, capped to the image width | Start from the value the overlay says you need |
| `blockSize idx` | `2*idx + 3`, minimum 3 (3-23, odd) | Matching window |
| `uniquenessRatio` | 0-30 | |
| `speckleWindowSize` | 0-200 | |
| `speckleRange` | 0-5 | |
| `disp12MaxDiff` | 0-25 | |
| `preFilterCap` | 1-63 | |

## Suggested workflow

1. Make sure the calibration is good (low `rms_stereo`) and the camera frame size matches it
   ([P02](problems/02-frame-size-vs-calibration.md)).
2. Choose `process scale` for the frame rate you need. Half resolution doubles the depth error
   ([Depth estimation](depth-estimation.md#3-how-accurate-is-it)).
3. Set `numDisparities` to **just** what the overlay asks for. Larger values add a wider black band on the left of the
   disparity panel ([P01](problems/01-sgbm-dead-band.md)).
4. Put a textured object at your nearest working distance and check that it is filled in, with no holes.
5. Increase `blockSize` to fill holes (at the cost of blurry edges). Raise `uniquenessRatio` and the speckle settings to
   remove noise (at the cost of more holes).
6. Click on an object at a **measured** distance and compare. A constant-factor error points to units
   ([P08](problems/08-implicit-units.md)), not to the matcher.
7. Press `d`.

## Cautions

- `d` rewrites the whole YAML file: **comments are dropped and keys are re-sorted**
  ([P09](problems/09-configurator-error-handling-and-rewrites.md)). Commit the file first so you can diff.
- The tuner has its own copy of the matcher code. Today it behaves the same as the runtime at `process_scale: 0.5`, but
  it can drift ([P10](problems/10-duplicated-disparity-code.md)), so re-check the result in the orchestrator.
- The tuner calls `StereoProcessor(None)` if the YAML can't be loaded, which fails with a confusing `TypeError`
  ([P09](problems/09-configurator-error-handling-and-rewrites.md)).
