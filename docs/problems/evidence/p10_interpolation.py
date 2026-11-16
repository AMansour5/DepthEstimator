"""P10: the disparity code used to be copied in three places (tuner, StereoProcessor, Orchestrator). Is it shared now?

Part A: a source scan for the duplicated pieces.
Part B: the original measurement (INTER_AREA vs INTER_LINEAR). It is historical: every path now uses INTER_AREA.
"""
import re
from common import *

read = lambda p: (ROOT / p).read_text()
tuner, proc, orch = read("src/tuners/DisparityTuner.py"), read("src/services/StereoProcessor.py"), read("src/services/Orchestrator.py")
checks = {
    "tuner builds its own StereoSGBM": "StereoSGBM_create" in tuner,
    "tuner defines its own colorizer": bool(re.search(r"def\s+\w*colori[sz]e", tuner, re.I)),
    "orchestrator defines its own colorizer": bool(re.search(r"def\s+\w*colori[sz]e", orch, re.I)),
    "StereoProcessor still downscales with INTER_LINEAR": bool(re.search(r"cv2\.resize\([^)]*INTER_LINEAR", proc)),
    "tuner calls StereoProcessor.computeDisparity": "computeDisparity(" in tuner,
    "both views use DisparityVisualizer": "DisparityVisualizer.colorizeDisparity" in tuner and "DisparityVisualizer.colorizeDisparity" in orch,
}
print("A) source scan")
for k, v in checks.items():
    print(f"   {k:<52}: {v}")
duplicated = any(checks[k] for k in list(checks)[:4]) or not (checks["tuner calls StereoProcessor.computeDisparity"] and checks["both views use DisparityVisualizer"])

print("\nB) historical measurement: same images, downscaled both ways, identical SGBM parameters")
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

verdict("STILL PRESENT" if duplicated else "FIXED",
        "the matcher, downscale and colorizer each exist once (StereoProcessor / DisparityVisualizer); "
        "the tuner and the orchestrator call them" if not duplicated else "duplicated disparity code remains")
