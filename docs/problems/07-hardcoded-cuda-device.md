# P07: `device: CUDA` broke detection on machines without a GPU

| | |
|---|---|
| **Severity** | Medium (before the fix) |
| **Status** | **Fixed** in `db60e9b`. The analysis of the failing path remains **source-read**: it was not executed on a machine without a GPU |
| **Where** | `config/object_detector.yaml:4` (`device: null`); `src/services/ObjectDetector.py:10,27` (passes `device=self.device` to the model call) |

## Resolution

The default is `device: null` again, with a comment that matches it (`null = ultralytics default (CUDA if available, else CPU)`).
Checked on this machine (PyTorch 2.11.0+cu130, ultralytics 8.3.242, a CUDA GPU present):

```
select_device('')     -> cuda:0
select_device('cpu')  -> cpu
select_device('CUDA') -> cuda:0
```

so `null` selects the GPU when there is one and the CPU otherwise. And since [P04](04-silent-detector-failure.md) is fixed, an
explicit device that cannot be used (for example `0` or `CUDA` on a laptop) now raises `DetectionError` on the first frame
instead of producing a window that never shows a box.

## Source-read analysis (unchanged, still not executed without a GPU)

From `parse_device` / `select_device` in `ultralytics/utils/torch_utils.py` (read on version 8.4.191):

- The string is lower-cased and `"cuda"` is mapped to GPU `"0"`, so `CUDA` **works on a machine with a working NVIDIA GPU**.
  The capitalisation was never the problem.
- When a GPU is requested and `torch.cuda.is_available()` is false, `select_device` raises
  `ValueError: Invalid CUDA 'device=0' requested. Use 'device=cpu' or pass valid CUDA device(s)...`.
- The forms the library documents are `0`, `cuda:0`, `cpu`; the accepted spelling of `"CUDA"` is an implementation detail.

To check the failing path on a CPU-only machine:

```bash
python -c "from ultralytics.utils.torch_utils import select_device; select_device('CUDA')"
```

## Remaining advice

- Keep `device: null` in the committed config; use `0` / `cuda:0` only on a machine you know has a GPU, ideally from a per-machine
  override rather than the committed default. Apple MPS and AMD are only reachable with an explicit value.
- Optionally log the device ultralytics chose at start-up, so "why is it slow" has an answer.
- `device` appears in the list of "values that must agree with the hardware" in [`docs/configuration.md`](../configuration.md).
