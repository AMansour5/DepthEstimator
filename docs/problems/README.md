# Known problems

Problems found by reading every file in the repository and then **testing each suspicion** before writing it down. Each problem has
its own file with the same layout: where it is, why it happens, the evidence, its effects, and a suggested fix.

The first version of this list described commit `90dda91`. It was audited again at commit `c39cf63` (the P01 fix): every
problem was re-checked against the current code, and two new ones were found (P12, P13). P03 was reopened in that audit and
has since been fixed for both configured and overridden `minDisparity` values.

**Summary of the 13: 9 fixed (P01, P02, P03, P04, P05, P07, P10, P12, P13), 3 partly fixed (P06, P08, P09), and 1 mitigated
(P11).** The original list had 11 entries.

## How sure am I? (the *Status* of each problem)

| Status | Meaning |
|---|---|
| **Fixed** | The code no longer has the problem. The evidence script (or a test) shows it, and prints `VERDICT FIXED`. |
| **Partly fixed** | The main symptom is gone but a verified residual remains. The problem file lists exactly what is left. |
| **Mitigated** | A workaround is in place and tested, but the root cause cannot be checked without your hardware. |
| **Open / New** | Reproduced by a script in [`evidence/`](evidence/) on synthetic data, with your real code and `depth_estimator/config/*.yaml`, and not fixed yet. |
| **Source-read** | Established by reading code or a library's source, not executed (the file says what was not run). |

Each evidence script ends with a line `VERDICT FIXED | PARTLY FIXED | STILL PRESENT` computed from the code, so a re-run tells
you whether a change moved anything.

## Severity

| Severity | Meaning |
|---|---|
| **High** | Can produce a missing or wrong depth with no error message, in the default configuration or one click away from it. |
| **Medium** | Blocks or confuses setup, hides failures, or breaks on another machine. |
| **Low** | Maintainability or polish, with no measurable effect on results today. |

## Open or partly fixed

| # | Problem | Severity | Status |
|---|---|---|---|
| [P08](08-implicit-units.md) | New files mark `T` in mm; legacy or mislabeled calibrations may still have the wrong scale | Medium | Partly fixed |
| [P06](06-tests-cannot-fail.md) | 27 of 38 tests can run without hardware; the other 11 need hardware or this machine; P03/P04 lack pytest regression tests | Medium | Partly fixed |
| [P09](09-configurator-error-handling-and-rewrites.md) | `setConfig` drops comments, re-sorts keys, and a failed write empties the file | Low | Partly fixed |
| [P11](11-possible-camera-latency.md) | Backend queues can make frames stale; reader thread reduces queue lag but cannot guarantee frame age | Low | Mitigated (fake tests and available-camera probe; other backends unverified) |

## Resolved

| # | Problem | Severity | Fixed in |
|---|---|---|---|
| [P01](01-sgbm-dead-band.md) | SGBM left the leftmost `numDisparities` columns without a depth (a third of the frame at 320) | High | `c39cf63` (pad, match, crop) |
| [P02](02-frame-size-vs-calibration.md) | A wrong-sized eye image or negotiated camera mode could be rectified silently | High | Check both rectification inputs and reject negotiated camera dimensions that differ from the request |
| [P03](03-invalid-disparity-assumes-min-disparity-zero.md) | SGBM's positive "no match" sentinel could become a valid depth when `minDisparity` was overridden | High | Clamp against the effective matcher parameters (configured and override paths verified) |
| [P04](04-silent-detector-failure.md) | A broken detector was indistinguishable from an empty scene | High | `ffade17` (it raises) |
| [P05](05-not-runnable-from-clean-clone.md) | Relative artifact paths depended on cwd and clean-clone folders/dependencies were unclear | Medium | Package-relative path resolution, package layout, `.gitkeep` folders, and complete dependencies |
| [P07](07-hardcoded-cuda-device.md) | `device: CUDA` broke detection on machines without a GPU | Medium | `db60e9b` (`device: null`) |
| [P10](10-duplicated-disparity-code.md) | Disparity code was copied in three places | Low | `084b056` (one `computeDisparity`, one visualizer) |
| [P12](12-non-editable-install-broken.md) | A regular install lacked packaged config and used a generic top-level package name | Medium | Renamed to `depth_estimator`, moved config inside the package, added package data, and declared dependencies |
| [P13](13-calibration-schema-unused-required-keys.md) | Legacy calibration metadata was required but unused | Low | Optional descriptive metadata, legacy assumed-mm warning, and explicit mm unit contract |

## How the problems combine

- [P01](01-sgbm-dead-band.md) used to create unmatched pixels; [P03](03-invalid-disparity-assumes-min-disparity-zero.md) now
  ensures they remain invalid for both configured and overridden `minDisparity` values.
- [P02](02-frame-size-vs-calibration.md), [P04](04-silent-detector-failure.md) and [P07](07-hardcoded-cuda-device.md), which
  could silently accept wrong inputs or hide failures, are fixed. A wrong legacy calibration scale can still produce
  plausible depths ([P08](08-implicit-units.md)); new files now declare the unit, but calibration accuracy must still be checked.
- [P06](06-tests-cannot-fail.md) is about running the project anywhere but the author's machine. P13's legacy compatibility
  issue is fixed; its schema and unit behavior are covered by hardware-free tests and evidence.

**Suggested order for what remains:** P08 (verify the external calibration producer and known-distance scale), then P06.

## Investigated and not recorded as problems

- **The left-edge tint** added for [P01](01-sgbm-dead-band.md) (`highlightLeftInvalidBand`) follows *any* contiguous invalid strip
  that touches the left edge, including an occlusion behind a near object. That is what it says it does, so it is described in
  P01 rather than recorded as a defect.
- **Padding cost** for P01 (about 46 ms to 56 ms on the real 1920x1080 sample pair at `numDisparities: 272`) is a trade-off,
  documented in P01.
- **Extrapolated disparities** in the `d` leftmost columns are a property of stereo (those pixels are outside the right camera's
  view), documented as P01's residual.

## Reproducing the evidence

```bash
pip install numpy opencv-python pyyaml zope.interface pytest
python3 docs/problems/evidence/p01_dead_band.py        # likewise p02 ... p13 (there is no p07, p08 or p11)
```

Evidence scripts use synthetic inputs where runtime behavior needs them; other scripts inspect tests, source, or packaging.
They do not require a camera, real calibration, or YOLO weights. The P12 script needs Python 3.11+ for `tomllib`. Numbers
that depend on your camera (focal length, baseline) are marked *illustrative* wherever they appear. See
[`evidence/README.md`](evidence/README.md).
