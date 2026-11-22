# P03: "No match" pixels must stay invalid for every `minDisparity`

| | |
|---|---|
| **Severity** | High when present: unmatched pixels could look like confident, very distant surfaces |
| **Status** | **Fixed**. `computeDisparity` clamps against the effective `minDisparity`, including overrides; `evidence/p03_min_disparity.py` prints `VERDICT FIXED` |
| **Where** | `depth_estimator/services/StereoProcessor.py:144` (clamp); `depth_estimator/tuners/DisparityTuner.py:32,51,153` (slider overrides); `depth_estimator/services/DepthEstimator.py:72` and `depth_estimator/utils/DisparityVisualizer.py:13` (`> 0` means valid) |

## What happened

SGBM writes `minDisparity - 1` into pixels it could not match. For `minDisparity >= 2`, that sentinel is positive, while the
rest of the code treats every positive disparity as valid. Such pixels could therefore become plausible, very distant depths.

The earlier fix (`9483759`) normalized the configured value but compared against `self.matcher_params["minDisparity"]`. The
tuner passes its slider value as an override, so a configured value of 0 with an override of 3 left SGBM's sentinel value 2
untouched.

## Fix and verification

`computeDisparity` already merges configured values and overrides into `params`. The clamp now compares against
`params["minDisparity"]`, the same effective value used to build the matcher. This covers both the configured and tuner
paths.

Ran `python3 docs/problems/evidence/p03_min_disparity.py` on a synthetic flat scene with true disparity 40 (750 mm). For
configured and overridden values 0, 3 and 8, the script reported zero positive sentinel pixels. The edge-box estimate
remained about 750 mm for each value, and the script ended with:

```
VERDICT FIXED: no 'no match' pixel is ever reported as a positive disparity
```

The script exercises real SGBM on synthetic images; a dedicated pytest regression test is still absent (see
[P06](06-tests-cannot-fail.md)).
