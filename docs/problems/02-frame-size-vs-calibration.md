# P02: A wrong frame size is rectified silently into a mostly-black image

| | |
|---|---|
| **Severity** | High (before the fix) |
| **Status** | **Partly fixed**. The left image is now checked; the right image and the camera are not. `evidence/p02_frame_size.py` prints `VERDICT PARTLY FIXED` |
| **Where** | `src/services/StereoProcessor.py:41-53` (`rectifyImages`, check at `:44-46`); `src/exceptions/DifferentImageSizeError.py`; `src/services/StereoCamera.py:8-11` (defaults `1280x480`), `:56-76` (`__setupCamera`, warning only), `:23-32` (`open`, swallows errors) |

## Resolution so far (`e645de6`)

`StereoProcessor` now stores the calibration's `img_size` as `calib_img_size`, and `rectifyImages` raises
`DifferentImageSizeError` when the **left** image has another size, so the original failure (a 640x480 or 640x720 frame
becoming a 1920x1080 image that is 78-85% black) can no longer happen silently:

```
both 640x480 (StereoCamera's default 1280x480 combined)    -> DifferentImageSizeError
both 640x720 (camera negotiated 1280x720 combined)         -> DifferentImageSizeError
```

## What is still open

1. **The right image is never compared.** `rectifyImages` reads the size from `left_img` only. A right frame of the wrong
   size is rectified without an error (output 1920x1080, 15% content in the check):

   ```
   left 1920x1080, RIGHT 640x480   -> no exception, right output 1920x1080, 15% of it has image content
   ```

   With the current `StereoCamera` both halves come from one frame, so they cannot differ today; it matters for any other
   `ICamera` implementation and for anyone calling `rectifyImages` directly.
2. **`StereoCamera` still only prints** `WARNING: camera did not accept the requested resolution...` and keeps running
   (`open()` also catches every exception and leaves the capture as `None`). The first sign of a negotiated size is now an
   exception on the first frame instead of a bad picture, which is better, but the message points at the processor, not at the
   camera setting that caused it.
3. **The `1280x480` fallbacks** in `StereoCamera.__init__` (used if `stereo_camera.yaml` lacks a key) still disagree with a
   Full-HD calibration.

## Why it happened (original analysis)

- `cv2.remap` takes its output size from the maps, not from the input image, and fills out-of-range samples with 0.
- Cameras commonly fall back to another mode when the requested one isn't available, and `StereoCamera` only printed.
- Nothing compared the frame size with `img_size`.

## Suggested fix for what remains

```python
# StereoProcessor.rectifyImages
for name, img in (("left", left_img), ("right", right_img)):
    if (img.shape[1], img.shape[0]) != self.calib_img_size:
        raise DifferentImageSizeError(f"{name} image is {img.shape[1]}x{img.shape[0]}, "
                                      f"calibration is {self.calib_img_size[0]}x{self.calib_img_size[1]}.")
```

and make `StereoCamera.__setupCamera` raise (not print) when the reported size differs from the requested one. Add the
two regression tests (right-size mismatch; negotiated-size mismatch with the fake capture already used in
`src/tests/test_stereo_camera.py`): today nothing tests this at all.

## How to verify

`python3 docs/problems/evidence/p02_frame_size.py` should end with `VERDICT FIXED` once the right image and the camera are
checked.
