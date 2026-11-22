# P02: Frame dimensions must match the stereo calibration

| | |
|---|---|
| **Severity** | High when present: remapping an incorrectly sized frame can produce a mostly-black image and invalid depths |
| **Status** | **Fixed**. The processor checks both eye images and the camera rejects a reported resolution mismatch; `evidence/p02_frame_size.py` prints `VERDICT FIXED` |
| **Where** | `src/services/StereoProcessor.py:41-48` (`rectifyImages`); `src/services/StereoCamera.py:57-76` (requested vs. reported size); `src/exceptions/DifferentImageSizeError.py` |

## What happened

Rectification maps are built for the calibration's `img_size`. OpenCV's `remap` uses the map dimensions for its output and
fills out-of-range samples with zero, so a frame with different dimensions could produce a mostly-black result without an
error. The prior check compared only the left image; `StereoCamera` also used to continue after the camera negotiated a
different resolution.

## Fix and verification

`StereoProcessor.rectifyImages` now checks both input images against `calib_img_size` before remapping and raises
`DifferentImageSizeError` for either mismatch. `StereoCamera.__setupCamera` compares the dimensions reported by the device
with the requested combined dimensions and aborts `open()` on a mismatch.

Ran `python3 docs/problems/evidence/p02_frame_size.py` using a synthetic 1920x1080 calibration and a fake camera. Matching
inputs rectified; left-size, right-size and both-eye mismatches raised `DifferentImageSizeError`; and `open()` rejected a
camera reporting 1280x720 when 3840x1080 was requested. The script ended with `VERDICT FIXED`.

The code defaults (`1280x480` combined) are not the project's configured dimensions (`3840x1080`). Keep
`config/stereo_camera.yaml` aligned with the calibration and device: if a device accepts the configured size but the
per-eye frame still differs from `img_size`, rectification now fails explicitly instead of producing a misleading image.
