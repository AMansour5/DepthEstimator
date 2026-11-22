# P12: Regular installs could not find configuration or used a generic package name

| | |
|---|---|
| **Severity** | Medium |
| **Status** | **Fixed**. The project uses the `depth_estimator` package, configuration is packaged inside it, and relative artifacts resolve from the package location. `evidence/p12_packaging.py` prints `VERDICT FIXED` |
| **Where** | `pyproject.toml` (dependencies, package discovery, package data, and console scripts); `depth_estimator/config/`; `depth_estimator/utils/Configurator.py`; `depth_estimator/services/StereoProcessor.py`; `depth_estimator/services/ObjectDetector.py` |

## What was wrong

The original top-level package was named `src`, so it could collide with another project. Setuptools also did not package the
repository-level `config/` directory, and `Configurator.getProjectRoot()` required that checkout layout. A regular wheel
install therefore could not find YAML configuration, while the editable install appeared to work only because it found the
repository folders.

`ultralytics` was imported but was also missing from the declared dependencies in the original package metadata.

## Fix

- Renamed `src/` to `depth_estimator/` and updated internal imports and both console entry points.
- Moved all four YAML files into `depth_estimator/config/`; the repository no longer keeps a duplicate top-level `config/`
  directory.
- Declared `depth_estimator.config` package data in `pyproject.toml`, so wheels contain `depth_estimator/config/*.yaml`.
- Updated `Configurator` to read packaged resources, honor `DEPTH_ESTIMATOR_CONFIG_DIR`, and copy packaged defaults to a
  writable per-user or overridden configuration directory for `setConfig`.
- Updated calibration and model path resolution so relative paths point into the package rather than the process working
  directory.
- Kept `ultralytics` declared in `pyproject.toml`.

## Verification

The P12 evidence script verifies package discovery, package data, package-resource loading, the absence of a duplicate
top-level config directory, and dependency declarations. A wheel build also contains:

```
depth_estimator/config/depth_estimator.yaml
depth_estimator/config/object_detector.yaml
depth_estimator/config/stereo_camera.yaml
depth_estimator/config/stereo_processor.yaml
```

Run:

```bash
python3 docs/problems/evidence/p12_packaging.py
python3 -m pip wheel --no-deps --wheel-dir /tmp/depth-estimator-wheel .
```
