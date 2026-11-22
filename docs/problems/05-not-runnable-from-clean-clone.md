# P05: A fresh clone still needs ignored artifacts

| | |
|---|---|
| **Severity** | Medium |
| **Status** | **Partly fixed**. `evidence/p05_not_runnable.py` prints `VERDICT PARTLY FIXED` |
| **Where** | `.gitignore` (`*.pt`, `*.npz`, `*.png`, `*.jpg`, `*.json`); `depth_estimator/config/stereo_processor.yaml:1` (`calibration_path`); `depth_estimator/config/object_detector.yaml:1` (`model_path`); `depth_estimator/utils/Configurator.py:resolvePath`; `pyproject.toml` |

## Resolved

- **Dependencies are declared** (`e645de6`): `pyproject.toml` lists `opencv-python`, `numpy`, `PyYAML`, `zope.interface`, a `dev`
  extra with `pytest`, and two console scripts (`estimate-depth`, `tune-disparity`). The repository has no `requirements.txt`,
  by choice. Use `pip install -e .` (see [`docs/setup.md`](../setup.md)); an editable install works from any directory.
- **Relative artifact paths are cwd-independent.** `Configurator.resolvePath()` joins package-relative `calibration_path` and
  `model_path` values to the `depth_estimator` package directory.
- **The artifact folders exist on a clean clone** (`a7ec39a`): `depth_estimator/matrices/.gitkeep`, `depth_estimator/models/.gitkeep`,
  `disparity_tuning_results/.gitkeep` are tracked.
- **The calibration `.npz` schema is documented** in [`docs/setup.md`](../setup.md).

## Still open

1. **Relative artifact paths are now resolved in one place.** `Configurator.resolvePath()` joins package-relative
   `calibration_path` and `model_path` values to the `depth_estimator` package directory, so `StereoProcessor` and
   `ObjectDetector` no longer depend on the process working directory. Launching from another directory now finds the package
   location correctly.
2. **The calibration and model files are still git-ignored and there is no tooling in the repository to create the
   calibration.** A clean clone fails with `RuntimeError: No calibration file at ...` until you supply it. The expected keys
   changed recently and two are now required but unused ([P13](13-calibration-schema-unused-required-keys.md)).
3. **`.gitignore` also ignores `*.png`, `*.jpg` and `*.json`.** The sample images the tests read
   (`depth_estimator/images/left/000.png`, `porsche.png`, ...) are therefore not in the repository ([P06](06-tests-cannot-fail.md)), and any
   image or JSON you add to `docs/` will be ignored too. Prefer Mermaid/ASCII diagrams, or add `!docs/**` exceptions.

## Suggested fix for what remains

Link to (or commit) the calibration script and keep calibration/model data ignored. Document exact setup for downloading or
generating the artifacts, and consider adding synthetic calibration/model tests that do not depend on the author's files.

## How to verify

Clone to a new folder, follow [`docs/setup.md`](../setup.md) only, and run `estimate-depth` from a different working directory.
`evidence/p05_not_runnable.py` should end with `VERDICT FIXED`.
