# Known problems

Problems found by reading every file in the repository (`main` at commit `90dda91`) and then
**testing each suspicion** before writing it down. Each problem has its own file with the same
layout: where it is, why it happens, the evidence, its effects, and a suggested fix.

## How sure am I? (the *Status* of each problem)

| Status | Meaning |
|---|---|
| **Reproduced** | A script in [`evidence/`](evidence/) demonstrates it on synthetic data using your real code and your real `config/*.yaml`. Re-run it yourself. |
| **Source-read** | Established by reading the code or a library's source, but not executed in my environment (the problem file says exactly what was not run). |
| **Unverified** | Plausible from the code, but needs your hardware to confirm. The file explains how to check. |

## Severity

| Severity | Meaning |
|---|---|
| **High** | Can produce a missing or wrong depth with no error message, in the default configuration or one click away from it. |
| **Medium** | Blocks or confuses setup, hides failures, or breaks on another machine. |
| **Low** | Maintainability or polish, with no measurable effect on results today. |

## Index

| # | Problem | Severity | Status |
|---|---|---|---|
| [P01](01-sgbm-dead-band.md) | With `numDisparities: 320`, a third of the frame can never get a depth | High | Reproduced |
| [P02](02-frame-size-vs-calibration.md) | A wrong frame size is rectified silently into a mostly-black image | High | Reproduced |
| [P03](03-invalid-disparity-assumes-min-disparity-zero.md) | With `minDisparity ≥ 1`, "no match" pixels become a confident wrong depth | High (latent) | Reproduced |
| [P04](04-silent-detector-failure.md) | A broken detector is indistinguishable from an empty scene | High | Reproduced |
| [P05](05-not-runnable-from-clean-clone.md) | A fresh clone can't run; paths depend on the working directory | Medium | Reproduced |
| [P06](06-tests-cannot-fail.md) | Most tests can't fail, and `pytest` collects only 2 tests | Medium | Reproduced |
| [P07](07-hardcoded-cuda-device.md) | `device: CUDA` breaks detection on machines without a GPU | Medium | Source-read |
| [P08](08-implicit-units.md) | Units of depth are implicit and inconsistent (mm vs cm) | Medium | Source-read |
| [P09](09-configurator-error-handling-and-rewrites.md) | `Configurator` turns errors into `None` and rewrites YAML files destructively | Low | Reproduced |
| [P10](10-duplicated-disparity-code.md) | Disparity code is copied in three places (and has already drifted) | Low | Reproduced (no effect today) |
| [P11](11-possible-camera-latency.md) | Camera frames may be stale because the capture buffer is never limited | Low | Unverified |

**How the problems combine.** P01 creates unmatched pixels, P03 turns them into wrong depths when
`minDisparity > 0`, and P04/P07/P09 make the resulting failures silent. Fixing P01 and P04 first
removes most of the practical risk.

## Reproducing the evidence

```bash
pip install numpy opencv-python pyyaml zope.interface pytest
python docs/problems/evidence/p01_dead_band.py        # likewise p02 ... p10
```

All scripts use **synthetic stereo pairs and a synthetic calibration file**, so they run without
a camera, a real calibration, or YOLO weights. Numbers that depend on your camera (focal length,
baseline) are marked *illustrative* wherever they appear.
