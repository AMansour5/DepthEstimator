# P03: With `minDisparity ≥ 1`, "no match" pixels become a confident wrong depth

| | |
|---|---|
| **Severity** | High (latent: the default config uses `minDisparity: 0`) |
| **Status** | Reproduced (`evidence/p03_min_disparity.py`) |
| **Where** | `src/services/DepthEstimator.py:72` (`valid = roi[roi > 0]`); `src/services/Orchestrator.py:90-96`; `src/tuners/DisparityTuner.py:58-65` and the 5x5 probe in `__measureAt`; the tuner's `minDisparity` slider at `:31` (range 0-10) |

## Summary

SGBM writes `minDisparity - 1` into pixels it could not match. With `minDisparity = 0` that is
`-1`, so the codebase's "valid means `> 0`" test works. With any `minDisparity ≥ 1` the sentinel is
`0, 1, 2, ...`, a small *positive* number that the code treats as a real measurement of a very distant
surface.

## Evidence

A flat scene whose true disparity is 40 (correct depth 750 mm), with a box placed in the unmatched
left band ([P01](01-sgbm-dead-band.md)):

```
minDisparity=0: SGBM writes [-1.] for 'no match'
   box in unmatched band: None (no depth)
   box in valid area   : z=750 mm  d=40.0  reliable=True
minDisparity=3: SGBM writes [2.] for 'no match'
   box in unmatched band: z=15000 mm  d=2.0  reliable=True      <-- wrong, and flagged reliable
   box in valid area   : z=750 mm  d=40.0  reliable=True
minDisparity=8: SGBM writes [7.] for 'no match'
   box in unmatched band: z=4286 mm  d=7.0  reliable=True       <-- wrong, and flagged reliable
```

The sentinel region is perfectly uniform, so `valid_frac = 1.0` and the spread is 0, which is
exactly what the `reliable` heuristic rewards.

## Effects

- Unmatched regions are reported as **valid, reliable, far-away** depths, instead of "no depth".
- It stays invisible while the config says `minDisparity: 0`. But `DisparityTuner` exposes
  `minDisparity` (0-10) and its `d` key writes the slider value into `config/stereo_processor.yaml`
  (`__writeParams`), so one tuning session can switch it on without anyone noticing.
- The disparity visualisations (`colorizeDisparity` in both the tuner and `Orchestrator`) have the
  same `> 0` assumption, so the invalid pixels would also be drawn as real, very distant surfaces.

## Suggested fix

Normalise the sentinel **at the source**, so every downstream `> 0` check stays correct.
Verified with `minDisparity` 0, 3 and 8:

```python
# StereoProcessor.computeDisparity
disp = raw.astype(np.float32) / 16.0
disp[disp < self.matcher_params["minDisparity"]] = -1.0   # SGBM's 'no match' is minDisparity - 1
return disp
```

(`DisparityTuner.__computeDisparity` needs the same line.)

## How to verify a fix

With the line above, `evidence/p03_min_disparity.py` shows `None` for the unmatched box at every
`minDisparity`.
