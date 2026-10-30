# P10: Disparity code is copied in three places (and has already drifted)

| | |
|---|---|
| **Severity** | Low |
| **Status** | Reproduced (`evidence/p10_interpolation.py`), **with no measurable effect today** |
| **Where** | `src/services/StereoProcessor.py:115-123` (downscale with `INTER_LINEAR`); `src/tuners/DisparityTuner.py:70-85` (own matcher), `:58-65` (own colorizer) and `:186-187` (downscale with `INTER_AREA`); `src/services/Orchestrator.py:90-96` (second copy of the colorizer) |

## Summary

You tune SGBM parameters in `DisparityTuner`, but the tuner has its own copy of the matcher construction and
image preparation, and the runtime path (`StereoProcessor`) has another. They have already diverged:
the tuner shrinks images with `INTER_AREA`, the runtime with `INTER_LINEAR`.

## Evidence

Same images, downscaled both ways, then identical SGBM parameters:

```
scale | mean |pixel diff| | median disp AREA  LINEAR | valid% AREA  LINEAR
  0.5 |              0.00 |            40.00   40.00 |        91.6    91.6
  0.4 |              2.05 |            32.00   32.00 |        91.5    91.6
  0.3 |              3.84 |            24.00   24.00 |        88.7    88.7
  0.7 |              0.84 |            56.00   56.00 |        92.8    92.8
```

At your configured scale (0.5) the two methods give **identical** images, because averaging 2x2 blocks is what bilinear
sampling does at exactly half size. At other scales the images differ slightly, but on this synthetic
(clean, uniform texture) pair the disparity results did not. Noisy or finely textured real images may behave
differently; I did not test that.

> Correction to something I said earlier: I suggested the interpolation difference "may change your SGBM results slightly".
> At `process_scale: 0.5` it does not.

## Effects

- **None measurable today.** The risk is future drift: any change to one copy (a new filter, a different
  `mode`, a tweak to the downscale) makes "what I tuned" differ from "what runs", with no error to tell you.
- Fixing a bug in one copy ([P01](01-sgbm-dead-band.md), [P03](03-invalid-disparity-assumes-min-disparity-zero.md))
  means remembering to fix the others.

## Suggested fix

Give `StereoProcessor.computeDisparity` optional `params`/`scale` overrides (or a `buildMatcher(params)` helper) and
have the tuner call it. Put `colorizeDisparity` in one shared utility used by both the tuner and the orchestrator,
and use `INTER_AREA` for downscaling everywhere.
