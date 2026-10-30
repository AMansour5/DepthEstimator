# P02: A wrong frame size is rectified silently into a mostly-black image

| | |
|---|---|
| **Severity** | High |
| **Status** | Reproduced (`evidence/p02_frame_size.py`) |
| **Where** | `src/services/StereoProcessor.py:40-50` (`rectifyImages`); `src/services/StereoCamera.py:9-10` (defaults `1280x480`) and `:35-38` (warning only) |

## Summary

The rectification maps are built for the calibration's `img_size` (e.g. 1920x1080 per eye).
If the camera delivers a different size, `cv2.remap` does **not** fail: it returns an image of the
*map's* size, sampling coordinates that mostly fall outside the smaller input, so most of the output
is black border.

## Why it happens

- `cv2.remap` takes its output size from the maps, not from the input image, and fills out-of-range
  samples with 0 (default `BORDER_CONSTANT`).
- `StereoCamera.__setupCamera` only **prints** `WARNING: camera did not accept the requested
  resolution...` and carries on. Cameras commonly fall back to another mode when the requested one
  isn't available.
- `StereoCamera`'s constructor defaults are `1280x480`, which would give `640x480` halves. If
  `stereo_camera.yaml` is missing those keys, this is what you get.
- Nothing in `StereoProcessor` or `Orchestrator` compares the frame size to `img_size`.

## Evidence

Synthetic calibration for 1920x1080, three kinds of input:

```
matches calibration                         input 1920x1080 -> output 1920x1080, no exception, 100% content
StereoCamera default 1280x480 -> 640x480    input 640x480   -> output 1920x1080, no exception,  15% content
camera negotiated 1280x720 -> 640x720       input 640x720   -> output 1920x1080, no exception,  22% content
```

## Effects

- The wrong frame looks like a valid 1920x1080 frame, so everything downstream keeps running.
  YOLO sees a small image in a black frame, SGBM matches a small region, and the depth numbers that
  come out look plausible but are wrong.
- The calibrated focal length and baseline no longer describe the image, so even the depths that
  *are* computed are scaled wrongly.
- The only trace is one console line at startup, which is easy to miss when the window opens.

## Suggested fixes

```python
# StereoProcessor.rectifyImages
h, w = left_img.shape[:2]
if (w, h) != self.img_size or right_img.shape[:2] != (h, w):
    raise ValueError(f"Frames are {w}x{h} but the calibration is for {self.img_size[0]}x{self.img_size[1]}. "
                     "Capture at the calibrated resolution or re-calibrate.")
```

and make `StereoCamera` raise (not print) when the camera reports a size other than the one
requested. Also remove the `1280x480` fallbacks, or make them match the calibration.

## How to verify a fix

`evidence/p02_frame_size.py` should raise for the two mismatched cases instead of printing a result.
