# P07: `device: CUDA` breaks detection on machines without a GPU

| | |
|---|---|
| **Severity** | Medium |
| **Status** | Source-read (ultralytics 8.4.191). **Not run** with PyTorch/a GPU in my environment. |
| **Where** | `config/object_detector.yaml:4`; `src/services/ObjectDetector.py` (passes `device=self.device` to the model call inside `detect`) |

## Summary

The most recent commit changed the value from `null` to `CUDA` while leaving the comment beside it
(`None = ultralytics default (CUDA if available, else CPU)`) unchanged. `null` was the portable setting;
`CUDA` makes a GPU mandatory.

## What I verified, and how

I downloaded the ultralytics wheel (8.4.191) and read `parse_device` / `select_device`
in `ultralytics/utils/torch_utils.py`:

- The string is lower-cased and `"cuda"` is mapped to GPU `"0"`, so `CUDA` **works on a machine with a
  working NVIDIA GPU**. The capitalisation is not the problem.
- When a GPU is requested and `torch.cuda.is_available()` is false, `select_device` raises
  `ValueError: Invalid CUDA 'device=0' requested. Use 'device=cpu' or pass valid CUDA device(s)...`.
- That call happens inside `self.model(...)` in `ObjectDetector.detect`, which is inside the broad
  `try/except` described in [P04](04-silent-detector-failure.md).

I did not execute this path, so the exact message and timing are from the source, not observed. To
check on a CPU-only machine:

```bash
python -c "from ultralytics.utils.torch_utils import select_device; select_device('CUDA')"
```

## Effects

- On a laptop without an NVIDIA GPU (a typical demo machine), every frame logs an error and
  returns no detections ([P04](04-silent-detector-failure.md)); disparity keeps working, so the failure looks like
  "YOLO doesn't detect anything".
- Other accelerators (Apple MPS, AMD) can't use it either.
- The comment and the value now contradict each other, which hides the cause.
- How `"CUDA"` is parsed is an implementation detail of one ultralytics version; the forms the library
  documents are `0`, `cuda:0`, `cpu`.

## Suggested fix

```yaml
device: null      # ultralytics chooses: GPU if available, else CPU
```

Use `0` or `"cuda:0"` only on a machine you know has a GPU, ideally from a per-machine override rather
than the committed default. Optionally log the chosen device at startup.
