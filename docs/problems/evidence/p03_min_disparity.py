"""P03: DepthEstimator treats `disparity > 0` as valid, which is only right when minDisparity == 0."""
from common import *
from src.services.DepthEstimator import DepthEstimator

mp = load_stereo_processor_cfg()["matcher_params"]
left, right = make_scene([], bg_d=40)            # flat scene, true disparity 40 everywhere
est = DepthEstimator(dict(roi_shrink=0.5), focal_length=1000.0, baseline=60.0, scale=0.5)
in_band = (100, 300, 300, 700)       # x 50..150: inside the unmatched left band
normal = (1200, 300, 1440, 700)      # x 600..720: measurable

print("flat scene, true disparity 40 -> correct depth 750 mm wherever it can be measured\n")
for mind in (0, 3, 8):
    disp = disparity(build_matcher(mp, numDisparities=128, minDisparity=mind), left, right)
    print(f"minDisparity={mind}: SGBM writes {np.unique(disp[:, :20])} for 'no match'")
    for name, box in (("box in unmatched band", in_band), ("box in valid area   ", normal)):
        dep = est.computeObjectDepth(disp, box)
        print(f"   {name}: " + ("None (no depth)" if dep is None else
              f"z={dep['z_mm']:.0f} mm  d={dep['disparity']:.1f}  reliable={dep['reliable']}"))
