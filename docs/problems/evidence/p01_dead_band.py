"""P01: SGBM cannot produce disparity in the leftmost `numDisparities` columns (fixed by padding).

Part A: the raw matcher, no padding: how wide is the invalid band with numDisparities from config?
Part B: what does DepthEstimator report for identical objects inside / outside that band?
Part C: StereoProcessor.computeDisparity (pads the images on the left, then crops): is the band gone?
Part D: what is left? Columns narrower than the true disparity are physically outside the right camera's view.
Part E: what the left-edge tint (DisparityVisualizer.highlightLeftInvalidBand) covers.
"""
from common import *
from src.services.DepthEstimator import DepthEstimator

cfg = load_stereo_processor_cfg()
mp = cfg["matcher_params"]
nd = mp["numDisparities"]
print(f"config: numDisparities={nd}, process_scale={cfg['process_scale']}, map width={W}px\n")


def first_valid(disp):
    return int(np.argmax((disp > 0).mean(axis=0) > 0.5))


print("A) raw SGBM, no padding: first column that is >50% valid, scene at constant true disparity")
for d in (10, 40, 80):
    left, right = make_scene([], bg_d=d)
    disp = disparity(build_matcher(mp), left, right)
    first = first_valid(disp)
    print(f"   true d={d:>3}: first valid column = {first}  ({first / W:.0%} of the width is dead)")

est = DepthEstimator(dict(roi_shrink=0.5), focal_length=1000.0, baseline=60.0, scale=0.5)  # illustrative f, B
left, right = make_scene([(100, 220, 150, 350, 40), (600, 720, 150, 350, 40)])
boxes = {"object at x 100-220 (inside old band)": (200, 300, 440, 700),
         "object at x 600-720 (outside it)": (1200, 300, 1440, 700)}


def report(disp):
    for name, box in boxes.items():
        dep = est.computeObjectDepth(disp, box)
        print(f"   {name}: " + ("None (no depth)" if dep is None else
              f"z={dep['z_mm']:.0f} mm  reliable={dep['reliable']}"))


print("\nB) two identical objects, both truly at 750 mm (disparity 40), raw SGBM")
for n in (nd, 128):
    print(f" numDisparities={n}")
    report(disparity(build_matcher(mp, numDisparities=n), left, right))

print(f"\nC) numDisparities={nd}, through StereoProcessor.computeDisparity (pad, match, crop)")
processor = make_processor(mp)
disp = processor.computeDisparity(bgr(left), bgr(right))
first_c = first_valid(disp)
print(f"   output shape {disp.shape} (input {left.shape}); first valid column = {first_c}")
report(disp)

print("\nD) residual: columns whose true match lies outside the right image (x < true d)")
for d in (10, 40):
    l, r = make_scene([], bg_d=d)
    out = processor.computeDisparity(bgr(l), bgr(r))
    inside = out[100:440, 0:d]
    v = inside[inside > 0]
    wrong = float((np.abs(v - d) > 2).mean()) if v.size else float("nan")
    print(f"   true d={d:>2}: columns 0..{d - 1} are physically unmatchable, yet {v.size / inside.size:.0%} of them "
          f"carry a disparity ({wrong:.0%} of those off by more than 2 px): they are extrapolated from the replicated padding")

print("\nE) what the left-edge tint covers (DisparityVisualizer.highlightLeftInvalidBand), background d=10")
from src.utils.DisparityVisualizer import DisparityVisualizer


def tint_width(objects):
    l, r = make_scene(objects, bg_d=10)
    out = processor.computeDisparity(bgr(l), bgr(r))
    col = DisparityVisualizer.colorizeDisparity(out, nd)
    cols = np.flatnonzero(np.any(DisparityVisualizer.highlightLeftInvalidBand(col, out) != col, axis=2).any(axis=0))
    return (int(cols.max()) + 1 if cols.size else 0), float((out[:, :100] <= 0).mean()), float((out[:, 400:500] <= 0).mean())


for label, objs in (("no near object", []),
                    ("near object (d=80) at x 80-410, hides the strip at the edge", [(80, 410, 0, 540, 80)]),
                    ("same object at x 500-830, hides a strip at x 430-500", [(500, 830, 0, 540, 80)])):
    w, e, m = tint_width(objs)
    print(f"   {label:<62} tint {w:>3} px | invalid in cols 0-99: {e:.0%}, in cols 400-499: {m:.0%}")
print("   -> the tint follows any invalid strip that touches the left edge (here an occlusion), not only an SGBM edge loss")

ok = first_c < 16 and all(est.computeObjectDepth(disp, b) is not None for b in boxes.values())
verdict("FIXED" if ok else "STILL PRESENT",
        f"first valid column {first_c} (was {nd}); both objects measured. Residual: the d leftmost columns are "
        "extrapolated, not measured (see problems/01-sgbm-dead-band.md).")
