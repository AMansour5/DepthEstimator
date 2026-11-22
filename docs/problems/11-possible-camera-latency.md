# P11: Camera frames may be stale when the backend queues captures

| | |
|---|---|
| **Severity** | Low |
| **Status** | **Mitigated**, not fully fixed. Fake-capture regressions pass, and the available `/dev/video2` device showed queued reads that the reader-thread path drained at a supported resolution. Frame age was not directly measured, so freshness on other cameras/backends remains unverified. |
| **Where** | `depth_estimator/services/StereoCamera.py:34-54` (`__startReader`, `__readLoop`), `:56-76` (`__setupCamera`), `:78-97` (`getFrames`), `:107-114` (`release`); `depth_estimator/tests/test_stereo_camera.py:95-142` |

## Summary

Capture backends such as V4L2 can queue frames, and `CAP_PROP_BUFFERSIZE=1` may be ignored. When the processing loop
is slower than the camera (YOLO plus SGBM can be at 30 FPS), a direct `read()` may hand you the *oldest queued* frame,
so what you see and measure can lag behind "now". Whether and how much this happens depends on the backend and OpenCV build.

## Fix applied

`StereoCamera` checks whether `CAP_PROP_BUFFERSIZE=1` was honoured (and warns if not) and runs a daemon reader thread that
continuously calls `read()` and retains only the last frame it obtained. `getFrames()` returns that latest-read frame,
waiting up to `frame_timeout` seconds (config key, default 2.0) for a frame newer than the last returned, so no frame is
processed twice. This reduces backend-queue lag when the reader can keep pace; it cannot guarantee sensor-to-application
frame age. `release()` stops the thread. Three fake-capture tests cover slow-consumer behavior, duplicate avoidance, and
thread shutdown.

On the available `/dev/video2` device, direct reads after a 200 ms idle period took 231.3 ms on the first read and
3.3-4.1 ms on the next four reads, consistent with frames queued in the backend. The `StereoCamera` reader, tested with
the camera's accepted 1280x720 mode, returned frames in 0-0.5 ms after five 200 ms consumer delays. This confirms that the
reader path operates on this backend and avoids waiting through the direct-read backlog in this probe; it does not measure
the true age of each frame. The repository's current camera config requests 3840x1080, which this device rejected, so the
reader was tested with an in-memory 1280x720 config override rather than the app's default config.

## Things to know about the fix (source-read, not hardware-tested)

- **The thread decodes every frame even if it is discarded.** With MJPG at 3840x1080 and 30 FPS that is a continuous decode on
  one core, whether or not the pipeline keeps up. That is the price of keeping the latest frame the reader has obtained.
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
30 FPS). If several reads in a row return almost instantly after an idle period, frames were likely sitting in a queue.
With the reader thread in place, `getFrames()` should return promptly because the background reader keeps consuming frames.
Timing alone cannot establish the age of the returned image; use a visible timestamp or other frame-age reference for that.

## Effects (if the backend queues)

- Lag between a real movement and the overlay, and depth measured on a frame older than any decision based on it. It matters little
  for a demo and a lot for anything that reacts to the result. The reader thread reduces queue-induced lag, but does not
  guarantee a maximum frame age.
