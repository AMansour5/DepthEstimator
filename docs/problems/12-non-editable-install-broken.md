# P12: A non-editable install (`pip install .`) cannot run: `config/` is not shipped and `ultralytics` is not declared

| | |
|---|---|
| **Severity** | Medium |
| **Status** | **New**, reproduced (`evidence/p12_packaging.py` prints `VERDICT STILL PRESENT`). An editable install (`pip install -e .`) works and is the supported path |
| **Where** | `pyproject.toml` (`[project].dependencies`, `[tool.setuptools.packages.find]`, `[project.scripts]`); `src/utils/Configurator.py:14-20` (`getProjectRoot`); `src/services/ObjectDetector.py:1` (`from ultralytics import YOLO`) |

## Summary

`pyproject.toml` defines two console scripts, `estimate-depth` and `tune-disparity`, which are the natural way to run the
program. Two things stop them working from a regular (non-editable) install:

1. **`config/` is not part of the package.** `[tool.setuptools.packages.find]` includes only `src*`, and there is no
   `package-data`/`data-files`/`MANIFEST.in`. A built wheel contains `src/` and nothing else. `Configurator.getProjectRoot()`
   walks up from its own file looking for a folder that has *both* `config/` and `src/`; in `site-packages` there is only
   `src/`, so it raises:

   ```
   FileNotFoundError: Could not find project root with /config and /src directories
   ```

2. **`ultralytics` is imported but not declared.** `ObjectDetector` imports it at module level, and `Orchestrator` imports
   `ObjectDetector`, so `estimate-depth` fails with `ModuleNotFoundError: No module named 'ultralytics'` on an environment
   that was set up only from `pyproject.toml`. (It is also what pulls in PyTorch, so it is the heaviest dependency, not an
   afterthought.) The script's part C lists it as the only import missing from `[project].dependencies`.

Also noteworthy: the package that gets installed is named **`src`**, a generic top-level name that can collide with another
project's `src` in the same environment.

## What was checked

- Part A: the setuptools configuration ships no data and no `config/`.
- Part B: a copy of `src/` without `config/` next to it (the `site-packages` layout) makes `getProjectRoot()` raise.
- Part C: a scan of the imports in `src/` (excluding tests) against `[project].dependencies`.
- Verified separately: building a wheel from the tracked files succeeds and contains only `src/` (24 files, tests excluded); an
  editable install into a fresh virtual environment finds the repository's `config/` from any directory and creates both
  console scripts.

Not checked: running `estimate-depth` itself on a machine without `ultralytics` (the dependency scan is static).

## Effects

- Anyone who installs the project the usual way gets scripts that fail immediately, with an error that doesn't mention
  packaging.
- Even once `config/` is found, the relative `calibration_path` and `model_path` still depend on the working directory
  ([P05](05-not-runnable-from-clean-clone.md)), so the console scripts only work from the repository root today.

## Suggested fixes

1. Add `ultralytics` to `[project].dependencies` (or to an extra, `pip install .[detect]`, and make `ObjectDetector` fail with a
   message that names the extra).
2. Pick one of: (a) state clearly in the README that the project is run from a checkout (`pip install -e .`) and drop the
   claim that console scripts work otherwise (done in the docs); (b) make `Configurator` find its config through an environment
   variable or a per-user directory when no `config/` sits next to `src/`, and ship defaults as package data; (c) move
   `config/` into the package.
3. Consider renaming the top-level package from `src` to something unique (for example `depth_estimator`); it is a mechanical but
   wide change, so do it separately.

## How to verify

`python3 docs/problems/evidence/p12_packaging.py` ends with `VERDICT FIXED` once `ultralytics` is declared and `config/` is
reachable from an installed copy.
