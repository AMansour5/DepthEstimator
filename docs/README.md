# Depth Estimator: documentation

Start with the [project README](../README.md) for what the program does and how to run it. This folder has the details.

| Document | Read it to... |
|---|---|
| [Setup and running](setup.md) | install the project, create the two files it needs (calibration and YOLO weights), run it, and check that it works |
| [Architecture](architecture.md) | understand the pipeline, the components, the data they pass around, the threading model and the error model |
| [Configuration reference](configuration.md) | learn what every key in `config/*.yaml` does and which values are valid |
| [Depth estimation](depth-estimation.md) | see how a disparity map becomes a distance, how reliable that distance is, and what range you can expect |
| [Disparity tuning guide](tuning-guide.md) | tune the stereo matcher with `DisparityTuner` |
| [API reference](api-reference.md) | look up classes, methods, arguments, return values and exceptions |
| [Testing](testing.md) | run the tests, and know which ones work without hardware |
| [Known problems](problems/README.md) | read the 13 audited problems (4 fixed, 6 partly fixed, 1 mitigated, 2 new), each with evidence, effects and a fix |
| [Evidence scripts](problems/evidence/README.md) | re-run the synthetic checks that back each problem; each ends with a `VERDICT` line |

If you only read one thing before trusting the numbers on your own camera, read
[P08 (units)](problems/08-implicit-units.md), [P02 (frame size)](problems/02-frame-size-vs-calibration.md) and
[P03 (`minDisparity`)](problems/03-invalid-disparity-assumes-min-disparity-zero.md): they are the ones that can still give a
plausible but wrong distance without an error.
