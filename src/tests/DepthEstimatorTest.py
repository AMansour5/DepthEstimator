import numpy as np
from src.services.DepthEstimator import DepthEstimator

# Synthetic setup: full-res 1920x1080, disparity computed at scale 0.5 (960x540).
FOCAL = 1000.0      # px, full resolution
BASELINE = 60.0     # mm
SCALE = 0.5
CFG = dict(roi_shrink=0.5, min_valid_frac=0.2, max_rel_spread=0.15)

# This box (full-res px) maps to the sampled region disp[150:250, 250:350].
BOX = (400, 200, 800, 600)
ROI = (slice(150, 250), slice(250, 350))


def newEstimator(cfg=CFG, scale=SCALE):
    return DepthEstimator(cfg, FOCAL, BASELINE, scale)


def blankDisparity(fill=-1.0):
    return np.full((540, 960), fill, dtype=np.float32)


class DepthEstimatorTest:

    def testKnownDepth(self):
        disp = blankDisparity()
        disp[ROI] = 40.0
        dep = newEstimator().computeObjectDepth(disp, BOX)
        # Z = f * scale * B / d = 1000 * 0.5 * 60 / 40
        assert abs(dep["z_mm"] - 750.0) < 1e-6, dep
        assert dep["reliable"] is True
        assert dep["roi"] == (500.0, 300.0, 700.0, 500.0), dep["roi"]

    def testBackgroundIgnored(self):
        # Object (d=40) fills the middle of the box, background (d=10) the rest.
        disp = blankDisparity(10.0)
        disp[130:270, 230:370] = 40.0
        dep = newEstimator().computeObjectDepth(disp, BOX)
        assert abs(dep["z_mm"] - 750.0) < 1e-6, dep
        # Averaging the whole box would have pulled the object farther away.
        naive_d = float(disp[100:300, 200:400].mean())
        assert naive_d < 40.0
        assert FOCAL * SCALE * BASELINE / naive_d > dep["z_mm"]

    def testInvalidPixelsIgnored(self):
        # Half the sampled region failed matching (-1); the rest is d=40.
        disp = blankDisparity()
        disp[150:250, 250:300] = 40.0
        dep = newEstimator().computeObjectDepth(disp, BOX)
        assert abs(dep["z_mm"] - 750.0) < 1e-6, dep
        assert abs(dep["valid_frac"] - 0.5) < 1e-6

    def testNoValidDisparity(self):
        assert newEstimator().computeObjectDepth(blankDisparity(), BOX) is None

    def testBoxOutsideMap(self):
        disp = blankDisparity(40.0)
        assert newEstimator().computeObjectDepth(disp, (5000, 5000, 5200, 5200)) is None

    def testSparseDisparityFlaggedUnreliable(self):
        disp = blankDisparity()
        disp[150:155, 250:350] = 40.0          # 5% of the sampled region
        dep = newEstimator().computeObjectDepth(disp, BOX)
        assert dep is not None
        assert dep["reliable"] is False
        assert dep["valid_frac"] < 0.2

    def testWideSpreadFlaggedUnreliable(self):
        disp = blankDisparity()
        disp[150:250, 250:300] = 20.0
        disp[150:250, 300:350] = 40.0
        dep = newEstimator().computeObjectDepth(disp, BOX)
        assert dep is not None
        assert dep["reliable"] is False
        assert dep["rel_spread"] > 0.15

    def testFullResolutionScale(self):
        est = DepthEstimator({}, FOCAL, BASELINE, scale=1.0)   # cfg defaults
        disp = np.full((1080, 1920), 40.0, dtype=np.float32)
        dep = est.computeObjectDepth(disp, (100, 100, 300, 300))
        assert abs(dep["z_mm"] - 1500.0) < 1e-6, dep           # 1000 * 60 / 40

    def testEstimateDepthsKeepsOrder(self):
        disp = blankDisparity()
        disp[ROI] = 40.0
        dets = [dict(box=BOX), dict(box=(5000, 5000, 5200, 5200))]
        depths = newEstimator().estimateDepths(disp, dets)
        assert len(depths) == 2
        assert depths[0] is not None and depths[1] is None
        assert newEstimator().estimateDepths(disp, []) == []

    def testBadArgumentsRejected(self):
        for kwargs in (
            dict(depth_cfg=dict(roi_shrink=0.0), focal_length=FOCAL, baseline=BASELINE, scale=SCALE),
            dict(depth_cfg=dict(roi_shrink=1.5), focal_length=FOCAL, baseline=BASELINE, scale=SCALE),
            dict(depth_cfg=CFG, focal_length=0, baseline=BASELINE, scale=SCALE),
            dict(depth_cfg=CFG, focal_length=FOCAL, baseline=-1, scale=SCALE),
            dict(depth_cfg=CFG, focal_length=FOCAL, baseline=BASELINE, scale=0),
        ):
            try:
                DepthEstimator(**kwargs)
            except ValueError:
                continue
            raise AssertionError(f"expected ValueError for {kwargs}")

    def runAll(self):
        tests = [name for name in dir(self) if name.startswith("test")]
        for name in tests:
            getattr(self, name)()
            print(f"PASS {name}")
        print(f"{len(tests)} tests passed")


if __name__ == "__main__":
    DepthEstimatorTest().runAll()