# P05: A fresh clone still can't run on its own, and artifact paths depend on the working directory

| | |
|---|---|
| **Severity** | Medium |
| **Status** | **Partly fixed**. `evidence/p05_not_runnable.py` prints `VERDICT PARTLY FIXED` |
| **Where** | `.gitignore` (`*.pt`, `*.npz`, `*.png`, `*.jpg`, `*.json`); `config/stereo_processor.yaml:1` (`calibration_path`); `config/object_detector.yaml:1` (`model_path`); `src/services/StereoProcessor.py:55-58` and `src/services/ObjectDetector.py:13` (paths opened as given); `pyproject.toml` |

## Resolved

- **Dependencies are declared** (`e645de6`): `pyproject.toml` lists `opencv-python`, `numpy`, `PyYAML`, `zope.interface`, a `dev`
  extra with `pytest`, and two console scripts (`estimate-depth`, `tune-disparity`). The repository has no `requirements.txt`,
  by choice. Use `pip install -e .` (see [`docs/setup.md`](../setup.md)); an editable install works from any directory.
- **The artifact folders exist on a clean clone** (`a7ec39a`): `src/matrices/.gitkeep`, `src/models/.gitkeep`,
  `disparity_tuning_results/.gitkeep` are tracked.
- **The calibration `.npz` schema is documented** in [`docs/setup.md`](../setup.md).

## Still open

1. **`calibration_path` and `model_path` are relative to the current working directory.** `Configurator` finds `config/` from
   the project root, but `StereoProcessor` and `ObjectDetector` open the two paths as plain relative paths. The same calibration
   file that loads when you start in the repo root fails from any other directory:

   ```
   cwd = folder that contains rel/: OK
   cwd = anywhere else: FAILED -> No calibration file at rel/stereo_calib.npz.
   ```

   Launching from an IDE run configuration, another folder or a service fails even when the files are in place. A wrong
   `model_path` is no longer silent ([P04](04-silent-detector-failure.md) is fixed); it fails with `YoloModelNotFound`.
2. **`ultralytics` is imported by `ObjectDetector` but is not in `pyproject.toml`.** Details and the packaging side
   effects are in [P12](12-non-editable-install-broken.md).
3. **The calibration and model files are still git-ignored and there is no tooling in the repository to create the
   calibration.** A clean clone fails with `RuntimeError: No calibration file at ...` until you supply it. The expected keys
   changed recently and two are now required but unused ([P13](13-calibration-schema-unused-required-keys.md)).
4. **`.gitignore` also ignores `*.png`, `*.jpg` and `*.json`.** The sample images the tests read
   (`src/images/left/000.png`, `porsche.png`, ...) are therefore not in the repository ([P06](06-tests-cannot-fail.md)), and any
   image or JSON you add to `docs/` will be ignored too. Prefer Mermaid/ASCII diagrams, or add `!docs/**` exceptions.

## Suggested fix for what remains

Resolve relative paths against the project root in one place, for example in `Configurator.fetchData`: if a value for
`calibration_path` or `model_path` is relative, join it with `Configurator.getProjectRoot()`. Add `ultralytics` to the
dependencies. Link to (or commit) the calibration script and keep the data itself ignored.

## How to verify

Clone to a new folder, follow [`docs/setup.md`](../setup.md) only, and run `estimate-depth` from a different working directory.
`evidence/p05_not_runnable.py` should end with `VERDICT FIXED`.
