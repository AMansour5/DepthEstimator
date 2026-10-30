# P04: A broken detector is indistinguishable from an empty scene

| | |
|---|---|
| **Severity** | High |
| **Status** | Reproduced (`evidence/p04_detector_failure.py`) |
| **Where** | `src/services/ObjectDetector.py:10-14` (constructor), `:38-40` (`detect`), `:29` (`return []`); `src/services/Orchestrator.py:71` (`... or []`) |

## Summary

Every failure inside `ObjectDetector` is caught, printed, and turned into `None`; the orchestrator
then converts `None` into `[]`. A detector that failed to load, or that raises on every frame,
produces exactly what a working detector produces for an empty room: no boxes, no depths, no error.

## Why it happens

1. The constructor wraps `YOLO(...)` in `try/except Exception`, prints, and **returns normally** with
   no `self.model` attribute.
2. `detect()` then fails on `self.model` with `AttributeError`, which its own broad `except Exception`
   catches, prints, and converts to `return None`.
3. A genuine "nothing found" also returns `[]`, so the two cases look alike to a caller, and the
   orchestrator's `or []` removes even the `None`/`[]` distinction.

## Evidence

A model that fails to load, followed by three frames through `Orchestrator.processFrame`:

```
Error: Failed to load YOLO model from 'src/models/yolov8n.pt'. Details: ... not found
   constructor returned normally; has .model? False
Error: Failed to perform object detection. Details: 'ObjectDetector' object has no attribute 'model'
   returned: None   (an empty scene returns [] - callers can't tell them apart)
   frame 0: detections=[] depths=[]
   frame 1: detections=[] depths=[]
   frame 2: detections=[] depths=[]
```

## Effects

- A wrong `model_path` (see [P05](05-not-runnable-from-clean-clone.md)), a missing model file, or an
  unavailable GPU ([P07](07-hardcoded-cuda-device.md)) all end the same way: **a window with a working
  disparity panel, a normal FPS counter, and no boxes ever.** It looks like "YOLO can't see anything",
  not "YOLO isn't running".
- The only clue is an error line repeated on every frame in the console, which scrolls away.
- Runtime failures such as CUDA out-of-memory or a bad frame are swallowed the same way.
- It makes debugging the *other* problems harder, because their symptoms are masked here.

## Suggested fixes

```python
# ObjectDetector.__init__: let it fail loudly
self.model = YOLO(self.model_path)          # no try/except

# ObjectDetector.detect: don't catch Exception. Let real errors propagate
results = self.model(image, imgsz=..., conf=..., classes=..., device=..., verbose=False)[0]

# Orchestrator.processFrame: drop "or []" so a None can never be mistaken for "no objects"
detections = self.detector.detect(rect_left)
```

If you do want the demo to survive transient errors, catch them in `Orchestrator.run`, show an
on-screen "DETECTOR ERROR" banner, and count consecutive failures before stopping.

## How to verify a fix

`evidence/p04_detector_failure.py` should stop with the `FileNotFoundError` at step 1.
