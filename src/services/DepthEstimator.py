import math
import numpy as np

class DepthEstimator:
    """Per-object depth from a disparity map: Z = f * B / d.

    This class only does the depth math. It knows nothing about cameras,
    calibration files or YOLO: everything it needs arrives through the
    constructor, so it can be tested with a synthetic disparity map.
    """

    # Fewer valid disparities than this in the sampled region -> no depth at all.
    MIN_VALID_PIXELS = 5

    def __init__(self, depth_cfg: dict, focal_length: float, baseline: float, scale: float = 1.0):
        """
        :param depth_cfg: roi_shrink, min_valid_frac, max_rel_spread
                          (see config/depth_estimator.yaml).
        :param focal_length: focal length in pixels at FULL resolution
                             (StereoProcessor.getFocalLength()).
        :param baseline: distance between the two cameras, in the units of the
                         calibration target square size, mm in this project
                         (StereoProcessor.getBaseline()). Depth comes out in the
                         same unit.
        :param scale: process scale the disparity map was computed at
                      (StereoProcessor.process_scale).
        """
        self.roi_shrink = depth_cfg.get("roi_shrink", 0.5)
        self.min_valid_frac = depth_cfg.get("min_valid_frac", 0.2)
        self.max_rel_spread = depth_cfg.get("max_rel_spread", 0.15)
        self.focal_length = focal_length
        self.baseline = baseline
        self.scale = scale
        self.__validate()

    def __validate(self):
        if not 0 < self.roi_shrink <= 1:
            raise ValueError(f"roi_shrink must be in (0, 1], got {self.roi_shrink}.")
        if self.focal_length <= 0:
            raise ValueError(f"focal_length must be positive, got {self.focal_length}.")
        if self.baseline <= 0:
            raise ValueError(f"baseline must be positive, got {self.baseline}.")
        if self.scale <= 0:
            raise ValueError(f"scale must be positive, got {self.scale}.")

    def computeObjectDepth(self, disparity, box):
        """Depth of one detection from the disparity map: Z = f*B/d.

        disparity : map at process scale (downscaled pixels)
        box       : (x1, y1, x2, y2) in FULL-resolution rectified-left pixels

        Samples only the central `roi_shrink` fraction of the box (0.5 -> the
        middle half of its width and height). Box edges contain background,
        whose small disparity would drag the estimate far away. The median of
        the valid pixels (disparity > 0) is used so speckle outliers don't
        decide it.

        'reliable' is a heuristic flag, not a measured accuracy: enough valid
        pixels, and a tight spread (IQR / median) inside the sampled region.
        Returns None when there is essentially no valid disparity there.
        """
        x1, y1, x2, y2 = [v * self.scale for v in box]
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        hw, hh = (x2 - x1) * self.roi_shrink / 2.0, (y2 - y1) * self.roi_shrink / 2.0
        h, w = disparity.shape
        c0, c1 = max(0, int(cx - hw)), min(w, int(math.ceil(cx + hw)))
        r0, r1 = max(0, int(cy - hh)), min(h, int(math.ceil(cy + hh)))
        if c1 <= c0 or r1 <= r0:
            return None

        roi = disparity[r0:r1, c0:c1]
        valid = roi[roi > 0]
        if valid.size < self.MIN_VALID_PIXELS:
            return None

        d = float(np.median(valid))
        p25, p75 = np.percentile(valid, [25, 75])
        rel_spread = float((p75 - p25) / d)
        valid_frac = valid.size / roi.size
        return dict(
            z_mm=self.focal_length * self.scale * self.baseline / d,
            disparity=d,
            valid_frac=float(valid_frac),
            rel_spread=rel_spread,
            reliable=bool(valid_frac >= self.min_valid_frac and rel_spread <= self.max_rel_spread),
            roi=(c0 / self.scale, r0 / self.scale, c1 / self.scale, r1 / self.scale),  # full-res px, for drawing
        )

    def estimateDepths(self, disparity, detections):
        """One depth dict (or None) per detection, in the same order.

        detections : list of dicts with a "box" key, as returned by
                     ObjectDetector.detect()
        """
        return [self.computeObjectDepth(disparity, det["box"]) for det in detections]