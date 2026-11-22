# P11: Camera frames may be stale because the capture buffer is never limited

| | |
|---|---|
| **Severity** | Low |
| **Status** | **Mitigated** in `d403a39` (reader thread, verified with fake-capture tests). Whether your backend queues frames is still **unverified without your camera** |
| **Where** | `depth_estimator/services/StereoCamera.py:34-54` (`__startReader`, `__readLoop`), `:56-76` (`__setupCamera`), `:78-97` (`getFrames`), `:108-115` (`release`); `depth_estimator/tests/test_stereo_camera.py:92-116` |

## Summary

Capture backends such as V4L2 queue several frames, and `CAP_PROP_BUFFERSIZE=1` may be ignored. When the processing loop
is slower than the camera (YOLO plus SGBM is, at 30 FPS), `read()` hands you the *oldest queued* frame, so what you see and
measure can be noticeably older than "now". This is a general property of OpenCV capture rather than something observed on your setup;
whether it happens depends on the backend and OpenCV build.

## Fix applied

`StereoCamera` checks whether `CAP_PROP_BUFFERSIZE=1` was honoured (and warns if not) and runs a daemon reader thread that
continuously calls `read()` and keeps only the newest frame. `getFrames()` returns that newest frame, waiting up to
`frame_timeout` seconds (config key, default 2.0) for one newer than the last returned, so no frame is processed twice.
`release()` stops the thread. Three fake-capture tests cover it (a slow consumer gets the latest frame, no frame is returned
twice, release stops the thread) and run on any machine.

## Things to know about the fix (source-read, not hardware-tested)

- **The thread decodes every frame even if it is discarded.** With MJPG at 3840x1080 and 30 FPS that is a continuous decode on
  one core, whether or not the pipeline keeps up. That is the price of always having the newest frame.
- **A 2 s stall ends the demo.** If no new frame arrives within `frame_timeout`, `getFrames()` prints `Failed to grab frame` and
  returns `(None, None)`, and `Orchestrator.run` treats that as end of stream (`No frame from the camera, stopping.`).
- **`release()` joins the reader for up to 2 s and then releases the capture.** If the backend's `read()` is blocked longer than
  that, the capture is released under a thread that is still inside `read()`.
- `open()` now raises `RuntimeError` when the camera cannot be opened or configured, including when its reported resolution
  differs from the request ([P02](02-frame-size-vs-calibration.md)).

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

A camera with no stale frames makes `read()` wait for the next fresh frame (a few ms up to one frame period, about 33 ms at
30 FPS). If several reads in a row return almost instantly, frames were sitting in a queue. With the reader thread in place,
the same check is `StereoCamera.getFrames()` timing: it should wait for the next frame, never return an old one.

## Effects (if the backend queues)

- Lag between a real movement and the overlay, and depth measured on a frame older than any decision based on it. It matters little
  for a demo and a lot for anything that reacts to the result. The reader thread removes this.
