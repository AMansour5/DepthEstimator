# Depth Estimator: documentation

| Document | Read it to... |
|---|---|
| [Architecture](architecture.md) | understand the pipeline, the components, the data they pass around, and the threading model |
| [Setup and running](setup.md) | install dependencies, create the two files the program needs (calibration and YOLO weights), and run it |
| [Configuration reference](configuration.md) | learn what every key in `config/*.yaml` does and which values are valid |
| [Depth estimation](depth-estimation.md) | see how a disparity map becomes a distance, how reliable that distance is, and what range you can expect |
| [Disparity tuning guide](tuning-guide.md) | tune the stereo matcher with `DisparityTuner` |
| [API reference](api-reference.md) | look up classes, methods, arguments, and return values |
| [Testing](testing.md) | run the tests and know which ones are meaningful |
| [Known problems](problems/README.md) | read the 11 documented problems, each with evidence, effects, and a fix |

If you only read one thing before running the program on your camera, read
[P01](problems/01-sgbm-dead-band.md) and [P02](problems/02-frame-size-vs-calibration.md).
