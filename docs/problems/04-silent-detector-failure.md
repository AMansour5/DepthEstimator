# P04: A broken detector was indistinguishable from an empty scene

| | |
|---|---|
| **Severity** | High (before the fix) |
| **Status** | **Fixed** in `ffade17`. Re-checked: `evidence/p04_detector_failure.py` prints `VERDICT FIXED` |
| **Where** | `depth_estimator/services/ObjectDetector.py:6-15` (constructor raises `YoloModelNotFound`), `:17-41` (`detect` raises `DetectionError`); `depth_estimator/exceptions/`; `depth_estimator/services/Orchestrator.py:72` (no more `or []`) |

## Resolution

- The constructor wraps `YOLO(...)` and raises `YoloModelNotFound` with the path and the original error.
- `detect()` raises `DetectionError` on any failure, and returns `[]` only for "nothing found", so the two cases can no longer
  be confused.
- `Orchestrator.processFrame` no longer has `or []`; the exception propagates out of `processFrame`, `run()` lets it reach
  `main()`, which prints it with a traceback and exits with status 1.

```
A) ObjectDetector with a model that fails to load  -> raised YoloModelNotFound
B) detect() when the model raises on every frame   -> raised DetectionError: ... CUDA out of memory (simulated)
C) Orchestrator.processFrame                       -> DetectionError propagates
```

This also removes the masking effect on [P05](05-not-runnable-from-clean-clone.md) (wrong `model_path`) and
[P07](07-hardcoded-cuda-device.md) (unavailable GPU): they now fail on the first frame with a clear message.

## Notes (behaviour to know about, not defects)

- **The demo is fail-fast.** One failed detection ends the run, including a transient one (CUDA out of memory on a single
  frame, for instance). If a long-running demo should survive that, catch `DetectionError` in `Orchestrator.run`, show a
  "DETECTOR ERROR" banner and stop after N consecutive failures. Do not turn it back into `[]`.
- The comment on `Orchestrator.processFrame`'s `detect` call used to describe the old behaviour (`None on error -> []`); it was
  corrected together with this audit, and `docs/api-reference.md` describes the new contract.
- `YoloModelNotFound` is raised for *any* exception while loading (corrupt weights, wrong ultralytics version), not only a
  missing file; its message carries the original error.
- Failures in the **SGBM worker** already propagated (`future.result()` re-raises), so only the detector needed fixing.

## Original problem (kept for context)

Every failure inside `ObjectDetector` was caught, printed, and turned into `None`; the orchestrator then converted `None`
into `[]`. A detector that failed to load, or raised on every frame, produced exactly what a working detector produces for an
empty room: no boxes, no depths, no error. The only clue was an error line repeated on every frame in the console.

## Remaining gap

There is no regression test for the new behaviour (nothing in `depth_estimator/tests/` references `DetectionError` or
`YoloModelNotFound`). A test with a stub `ultralytics` module, like `evidence/p04_detector_failure.py`, would pin it down
without weights or a GPU.

## How to verify

`python3 docs/problems/evidence/p04_detector_failure.py` ends with `VERDICT FIXED`.
