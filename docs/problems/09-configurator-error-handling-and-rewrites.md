# P09: `Configurator` turns errors into `None` and rewrites YAML files destructively

| | |
|---|---|
| **Severity** | Low |
| **Status** | Reproduced (`evidence/p09_configurator.py`); the non-atomic write is reasoned from the code, not tested |
| **Where** | `src/utils/Configurator.py:42-53` (`fetchData`), `:55-85` (`setConfig`, `safe_dump` at `:79`); callers such as `src/tuners/DisparityTuner.py:19` |

## Summary

`fetchData` prints an error and returns `None` instead of raising. Callers that don't check for `None`
fail later with an unrelated `TypeError`. `setConfig` (used by the tuner's `d` key) re-serialises the entire
file with `yaml.safe_dump`, which discards comments and re-sorts keys.

## Evidence

```
A) object_detector.yaml before setConfig(conf_threshold=0.6):
   | model_path: "src/models/yolov8n.pt"
   | conf_threshold: 0.5
   | classes: null              # e.g. [0, 39, 41] = person, bottle, cup; None = all COCO classes
   | device: CUDA               # None = ultralytics default (CUDA if available, else CPU)
   after (comments gone, keys re-sorted, quotes dropped):
   | classes: null
   | conf_threshold: 0.6
   | device: CUDA
   | model_path: src/models/yolov8n.pt

B) errors become None
   unknown type          -> None
   malformed yaml        -> None
   missing file          -> None
```

Passing that `None` onward: `StereoProcessor(None)` fails with
`TypeError: 'NoneType' object is not subscriptable`, far from the real cause (a bad config file).
`Orchestrator` guards against it (`__fetch`); `DisparityTuner.__init__` does not.

## Effects

- A typo in a YAML file produces a confusing `TypeError` somewhere else.
- Tuning with the `d` key silently deletes the explanatory comments in whichever file it rewrites (the
  tuner rewrites `stereo_processor.yaml`; `setConfig` is generic and would do the same to
  `object_detector.yaml`, which is where your comments currently live).
- `setConfig` opens the file for writing before serialising, so a crash in between can leave it empty
  (reasoned from the code; not tested).

## Suggested fixes

- Raise on failure (`FileNotFoundError`, `yaml.YAMLError`) and let callers decide.
- Preserve comments with `ruamel.yaml`, or accept losing them and move the explanations into
  [`docs/configuration.md`](../configuration.md) (done).
- Write to a temporary file and `os.replace` it over the original.
