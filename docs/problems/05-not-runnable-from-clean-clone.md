# P05: A fresh clone can't run, and paths depend on the working directory

| | |
|---|---|
| **Severity** | Medium |
| **Status** | Reproduced (`evidence/p05_not_runnable.py`) |
| **Where** | `.gitignore` (`*.pt`, `*.npz`, `*.json`, `*.png`); `config/stereo_processor.yaml:1` (`calibration_path`); `config/object_detector.yaml:1` (`model_path`); no `requirements.txt` |

## Summary

Everything the program needs at runtime (the calibration `.npz` and the YOLO weights) is
git-ignored, nothing in the repository creates the calibration file, and the repository does not
list its dependencies. On top of that, both file paths are *relative to the directory you launch
from*, while the rest of the project locates its config by project root.

## Why it happens

- `*.npz` and `*.pt` are in `.gitignore`, so `src/matrices/stereo_calib.npz` and
  `src/models/yolov8n.pt` exist only on your machine.
- The calibration is produced by capture/calibration scripts that are not in this repository, and the
  file format (keys `K1 D1 K2 D2 R T img_size rms_stereo`) isn't documented anywhere in the code.
- `Configurator` finds `config/` through `getProjectRoot()`, which works from any directory.
  `StereoProcessor` and `ObjectDetector` instead open `calibration_path` / `model_path` as plain
  relative paths, so they resolve against the **current working directory**.
- No `requirements.txt`, `pyproject.toml` or setup instructions. The imports show the needs:
  `opencv-python` (with GUI, for `imshow`), `numpy`, `pyyaml`, `ultralytics` (pulls in PyTorch),
  `zope.interface`, plus `pytest` for the tests.

## Evidence

```
A) fresh clone: is there a calibration file?
   .../src/matrices/stereo_calib.npz -> MISSING

B) same calibration file, same code, different working directory
   cwd = folder that contains rel/: OK
   cwd = anywhere else: FAILED -> No calibration file at rel/stereo_calib.npz.
```

## Effects

- First run on any other machine fails with `RuntimeError: No calibration file at ...`, and
  nobody can tell from the repository how to create one.
- Launching from an IDE run configuration, a script in another folder, or a service (anything whose
  working directory isn't the repo root) fails even when the files are in place.
- For `model_path`, a wrong path is reported as the silent no-detections symptom in
  [P04](04-silent-detector-failure.md).
- Version drift: without pinned dependencies, behaviour such as the `device` string
  ([P07](07-hardcoded-cuda-device.md)) can change between machines.

## Suggested fixes

1. Resolve relative paths against the project root in one place, for example in
   `Configurator.fetchData`: if a value for `calibration_path` or `model_path` is relative, join it with
   `Configurator.getProjectRoot()`.
2. Add a `requirements.txt` and put the install and first-run steps in the README (see
   [`docs/setup.md`](../setup.md)).
3. Commit the calibration tooling (or link to it) and document the `.npz` schema (done in
   [`docs/setup.md`](../setup.md)). Keep the data ignored, but add `src/matrices/.gitkeep` and
   `src/models/.gitkeep` so the folders exist.
4. Be aware that `*.png` and `*.json` in `.gitignore` also hide any documentation images or JSON files
   you add later, so prefer Mermaid/ASCII diagrams in `docs/`.

## How to verify a fix

Clone to a new folder, follow the README only, and run the orchestrator from a different working directory.
