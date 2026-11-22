# P09: `Configurator.fetchData` raises now; `setConfig` still destroys comments and can empty a file

| | |
|---|---|
| **Severity** | Low |
| **Status** | **Partly fixed**. `evidence/p09_configurator.py` prints `VERDICT PARTLY FIXED` |
| **Where** | `depth_estimator/utils/Configurator.py:42-53` (`fetchData`), `:55-88` (`setConfig`, `open(..., 'w')` at `:78`, `safe_dump` at `:79`); caller `depth_estimator/tuners/DisparityTuner.py:107-117` (`__writeParams`, the `d` key) |

## Resolved (`e645de6`)

`fetchData` no longer prints and returns `None`. It raises, and callers that don't handle it stop at the real cause:

```
unknown type    -> TypeError
malformed yaml  -> RuntimeError
missing file    -> FileNotFoundError
```

That removes the confusing `TypeError: 'NoneType' object is not subscriptable` far away from a bad config file; `Orchestrator.__fetch`
and `DisparityTuner.__init__` both get the exception directly.

## Still open

1. **`setConfig` re-serialises the whole file with `yaml.safe_dump`**, dropping comments, quotes and re-sorting the keys. The
   tuner's `d` key uses it on `stereo_processor.yaml` (which has no comments today), but `setConfig` is generic and would do the
   same to `object_detector.yaml`, where the explanatory comments live:

   ```
   before: classes: null              # e.g. [0, 39, 41] = person, bottle, cup; null = all COCO classes
   after:  classes: null              (comment gone; keys now alphabetical; quotes dropped)
   ```

2. **The write is not atomic, and this one is now reproduced** (it was only reasoned before). `setConfig` opens the file for
   writing, truncating it, *then* serialises. When serialisation fails, the original content is gone:

   ```
   setConfig(..., {"conf_threshold": object()})  -> raised RuntimeError
   file afterwards: 0 bytes (was 97)  <-- the original content is gone
   ```

   (A crash or power loss between `open` and the end of `safe_dump` does the same.)
3. **The parse error loses its detail.** `fetchData` raises `RuntimeError("Error: Failed to parse the YAML file.")` without the
   line/column from the `yaml.YAMLError`, and without chaining it (`from e`).

## Suggested fixes

- Build the YAML text first, write it to a temporary file in the same folder, then `os.replace` it over the original.
- Preserve comments with `ruamel.yaml`, or accept losing them and keep the explanations in
  [`docs/configuration.md`](../configuration.md) (done; the page says it is the source of truth).
- Chain the parser error (`raise RuntimeError(...) from e`, or include `str(e)`).
- Add tests for the failure modes (`tests/test_configurator.py` only covers the success paths and creation of a missing file).

## How to verify

`python3 docs/problems/evidence/p09_configurator.py` ends with `VERDICT FIXED` once comments survive and a failed write leaves
the file intact.
