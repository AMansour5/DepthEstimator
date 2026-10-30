"""P10: DisparityTuner downscales with INTER_AREA, StereoProcessor with INTER_LINEAR. Does it matter?"""
from common import *

mp = load_stereo_processor_cfg()["matcher_params"]
rng = np.random.default_rng(3)
big = cv2.GaussianBlur((rng.random((1080, 1920 + 400)) * 255).astype(np.uint8), (0, 0), 1.2)
L, R = big[:, :1920].copy(), big[:, 80:80 + 1920].copy()      # full-res disparity 80

print(f"{'scale':>5} | {'mean |pixel diff|':>17} | {'median disp AREA':>16} {'LINEAR':>7} | {'valid% AREA':>11} {'LINEAR':>7}")
for s in (0.5, 0.4, 0.3, 0.7):
    res = {}
    for name, interp in (("AREA", cv2.INTER_AREA), ("LINEAR", cv2.INTER_LINEAR)):
        l = cv2.resize(L, None, fx=s, fy=s, interpolation=interp)
        r = cv2.resize(R, None, fx=s, fy=s, interpolation=interp)
        nd = max(16, int(np.ceil(80 * s / 16) * 16) + 32)
        res[name] = (l, disparity(build_matcher(mp, numDisparities=nd), l, r))
    diff = np.abs(res["AREA"][0].astype(float) - res["LINEAR"][0].astype(float)).mean()
    st = lambda d: (np.median(d[d > 0]), 100 * (d > 0).mean())
    (ma, va), (ml, vl) = st(res["AREA"][1]), st(res["LINEAR"][1])
    print(f"{s:>5} | {diff:>17.2f} | {ma:>16.2f} {ml:>7.2f} | {va:>11.1f} {vl:>7.1f}")
