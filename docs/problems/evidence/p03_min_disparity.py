"""P03: "no match" pixels must be -1, whatever minDisparity is. The configured path does that; the tuner's override path does not.

StereoProcessor.computeDisparity writes `disparity[disparity < minDisparity] = -1`. SGBM's 'no match' value is
minDisparity - 1, which is a small POSITIVE number when minDisparity >= 2 (and 0 when it is 1), so the rest of the code
(`disparity > 0` means valid) would take it for a real, very distant surface.

Part A: minDisparity comes from the config (what the Orchestrator does).
Part B: minDisparity comes from `overrides` (what DisparityTuner does with its slider).
"""
from common import *
from depth_estimator.services.DepthEstimator import DepthEstimator

mp = load_stereo_processor_cfg()["matcher_params"]
TRUE_D = 40
left, right = make_scene([], bg_d=TRUE_D)           # flat scene, every measurable pixel has disparity 40
est = DepthEstimator(dict(roi_shrink=0.5), focal_length=1000.0, baseline=60.0, scale=0.5)
BAND_BOX = (0, 300, 50, 700)                         # x 0..25 of the map: the left edge, where the true match lies outside the right image


def sentinel_pixels(disp, mind):
    """Pixels that still hold SGBM's raw 'no match' value (minDisparity - 1) and count as valid (> 0)."""
    return int(((disp == mind - 1) & (disp > 0)).sum())


def box_depth(disp):
    dep = est.computeObjectDepth(disp, BAND_BOX)
    return "None (no depth)" if dep is None else f"z={dep['z_mm']:.0f} mm  d={dep['disparity']:.1f}  reliable={dep['reliable']}"


print(f"flat scene, true disparity {TRUE_D} -> correct depth 750 mm wherever it can be measured\n")
print("A) minDisparity from the config (the Orchestrator path)")
bad_config = 0
for mind in (0, 3, 8):
    disp = make_processor(mp | {"minDisparity": mind}).computeDisparity(bgr(left), bgr(right))
    n = sentinel_pixels(disp, mind) if mind else 0
    bad_config += n
    print(f"   minDisparity={mind}: raw sentinel pixels counted as valid = {n:>6}   box at the left edge, x 0..25: {box_depth(disp)}")

print("\nB) minDisparity from `overrides` (the DisparityTuner slider path)")
bad_override = 0
processor = make_processor(mp)                       # config minDisparity stays 0
for mind in (0, 3, 8):
    disp = processor.computeDisparity(bgr(left), bgr(right), {"minDisparity": mind})
    n = sentinel_pixels(disp, mind) if mind else 0
    bad_override += n
    print(f"   override minDisparity={mind}: raw sentinel pixels counted as valid = {n:>6}   box at the left edge, x 0..25: {box_depth(disp)}")

if bad_config == 0 and bad_override == 0:
    verdict("FIXED", "no 'no match' pixel is ever reported as a positive disparity")
elif bad_config == 0:
    verdict("PARTLY FIXED",
            "the configured minDisparity is normalised, but computeDisparity(overrides) compares against the CONFIGURED "
            "minDisparity, so the tuner's slider (0-10) still produces valid-looking 'no match' pixels")
else:
    verdict("STILL PRESENT", "even the configured path leaks the sentinel")
