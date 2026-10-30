# P11: Camera frames may be stale because the capture buffer is never limited

| | |
|---|---|
| **Severity** | Low |
| **Status** | **Unverified**: needs your camera. I could not reproduce it here. |
| **Where** | `src/services/StereoCamera.py:27-30` (`__setupCamera`) and `getFrames` |

## Summary

`StereoCamera` sets width, height, codec and FPS, but not the capture buffer size. Capture backends such as
V4L2 queue several frames. When the processing loop is slower than the camera (YOLO plus SGBM is, at 30 FPS),
`read()` hands you the *oldest queued* frame, so what you see and measure can be noticeably older than
"now".

This is a general property of OpenCV capture rather than something I observed in your setup. Whether it
happens depends on the backend and OpenCV build, which is why I am marking it unverified.

## How to check on your hardware

Simulate a slow consumer and time the reads:

```python
import time, cv2
cap = cv2.VideoCapture("/dev/video2")      # same settings as StereoCamera
for _ in range(10):
    time.sleep(0.2)                         # pretend the pipeline took 200 ms
    t = time.perf_counter(); cap.read()
    print(f"read took {(time.perf_counter() - t) * 1000:.1f} ms")
```

A camera with no stale frames makes `read()` wait for the next fresh frame (a few ms up to one frame period, about
33 ms at 30 FPS). If several reads in a row return almost instantly, frames were sitting in a queue and
you are looking at the past.

## Effects (if confirmed)

- Lag between a real movement and the overlay.
- Depth measured on a frame that is older than the one shown, and older than any decision based on it.
  It matters little for a demo and a lot for anything that reacts to the result.

## Suggested fixes

- `cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)` (support depends on the backend; check the return value), or
- run `getFrames` in a small reader thread that always keeps only the latest frame, or
- call `cap.grab()` a few times before `retrieve()` to discard queued frames.
