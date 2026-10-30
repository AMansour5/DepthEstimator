"""P01: SGBM cannot produce disparity in the leftmost `numDisparities` columns.

Part A: how wide is the invalid band, with the numDisparities from config/stereo_processor.yaml?
Part B: what does DepthEstimator report for identical objects inside / outside the band?
Part C: does padding the images on the left before SGBM (then cropping) remove the band?
"""
from common import *
from src.services.DepthEstimator import DepthEstimator

cfg = load_stereo_processor_cfg()
mp = cfg["matcher_params"]
nd = mp["numDisparities"]
print(f"config: numDisparities={nd}, process_scale={cfg['process_scale']}, map width={W}px\n")

print("A) first column that is >50% valid, scene at constant true disparity")
for d in (10, 40, 80):
    left, right = make_scene([], bg_d=d)
    disp = disparity(build_matcher(mp), left, right)
    first = int(np.argmax((disp > 0).mean(axis=0) > 0.5))
    print(f"   true d={d:>3}: first valid column = {first}  ({first / W:.0%} of the width is dead)")

est = DepthEstimator(dict(roi_shrink=0.5), focal_length=1000.0, baseline=60.0, scale=0.5)  # illustrative f, B
left, right = make_scene([(100, 220, 150, 350, 40), (600, 720, 150, 350, 40)])
boxes = {"object at x 100-220 (inside band)": (200, 300, 440, 700),
         "object at x 600-720 (outside band)": (1200, 300, 1440, 700)}

def report(disp):
    for name, box in boxes.items():
        dep = est.computeObjectDepth(disp, box)
        print(f"   {name}: " + ("None (no depth)" if dep is None else
              f"z={dep['z_mm']:.0f} mm  reliable={dep['reliable']}"))

print("\nB) two identical objects, both truly at 750 mm (disparity 40)")
for n in (nd, 128):
    print(f" numDisparities={n}")
    report(disparity(build_matcher(mp, numDisparities=n), left, right))

print(f"\nC) numDisparities={nd}, both images padded on the left by {nd} columns, result cropped")
lp = cv2.copyMakeBorder(left, 0, 0, nd, 0, cv2.BORDER_REPLICATE)
rp = cv2.copyMakeBorder(right, 0, 0, nd, 0, cv2.BORDER_REPLICATE)
disp = disparity(build_matcher(mp), lp, rp)[:, nd:]
print(f"   first valid column = {int(np.argmax((disp > 0).mean(axis=0) > 0.5))}")
report(disp)
