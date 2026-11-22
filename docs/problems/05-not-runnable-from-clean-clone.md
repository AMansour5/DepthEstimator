# P05: The package can run outside the checkout and from a clean clone layout

| | |
|---|---|
| **Severity** | Medium |
| **Status** | **Fixed**. `evidence/p05_not_runnable.py` prints `VERDICT FIXED` |
| **Where** | `pyproject.toml`; `depth_estimator/utils/Configurator.py:resolvePath`; `depth_estimator/config/stereo_processor.yaml`; `depth_estimator/config/object_detector.yaml`; `.gitignore`; `depth_estimator/matrices/.gitkeep`; `depth_estimator/models/.gitkeep` |

## Original problem

The application depended on the process working directory for relative `calibration_path` and `model_path` values. A launch
from the IDE, a service, or any directory other than the repository root could leave the package unable to locate its
calibration or YOLO weights.

The original checkout also lacked a clear clean-clone layout for generated artifact folders and did not have complete
dependency declarations.

## Fixed behavior

- The package was renamed to `depth_estimator`, and configuration now lives inside the package.
- `Configurator.resolvePath()` turns package-relative calibration and model paths into absolute paths based on the installed
  package location.
- `StereoProcessor` and `ObjectDetector` use the resolved paths, so neither depends on the caller's working directory.
- `pyproject.toml` declares all runtime imports, including `ultralytics`, and defines both console entry points.
- `depth_estimator/matrices/.gitkeep` and `depth_estimator/models/.gitkeep` preserve the clean-clone artifact directories.

## External setup remains intentional

The git-ignored `.npz` stereo calibration and `.pt` YOLO weights are hardware-specific or downloaded artifacts, so they are
not expected in the repository. A fresh clone must follow [`docs/setup.md`](../setup.md) to provide those two files. Their
absence produces an explicit startup error, not an ambiguous cwd-dependent failure.

## Verification

`python3 docs/problems/evidence/p05_not_runnable.py` verifies:

- the package-relative artifact paths are resolved in different working directories;
- artifact folders and dependencies are present in a clean clone layout;
- all third-party imports are declared.

It ends with:

```
VERDICT FIXED: paths are cwd-independent and dependencies are complete
```
