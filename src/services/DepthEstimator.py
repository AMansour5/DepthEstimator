import cv2 
import math
import numpy as np
from src.utils.Configurator import Configurator
from src.services.StereoCamera import StereoCamera
from src.services.ObjectDetector import ObjectDetector
from src.services.StereoProcessor import StereoProcessor

class DepthEstimator:
    def __init__(self):
        self.configurator = Configurator()
        self.camera_cfg = self.configurator.fetchData(self.configurator.STEREO_CAMERA)
        self.detect_cfg = self.configurator.fetchData(self.configurator.OBJECT_DETECTOR)
        self.processor_cfg = self.configurator.fetchData(self.configurator.STEREO_PROCESSOR)
        self.depth_estimator_cfg = self.configurator.fetchData(self.configurator.DEPTH_ESTIMATOR)
        self.roi_shrink = self.depth_estimator_cfg.get("roi_shrink", 0.5)
        self.min_valid_frac = self.depth_estimator_cfg.get("min_valid_frac", 0.2)
        self.max_rel_spread = self.depth_estimator_cfg.get("max_rel_spread", 0.15)
        self.camera = StereoCamera(self.camera_cfg)
        self.detector = ObjectDetector(self.detect_cfg)
        self.processor = StereoProcessor(self.processor_cfg)
        self.scale = self.processor_cfg.get("process_scale", 1.0)
        self.baseline = self.processor.getBaseline()
        self.focal_length = self.processor.getFocalLength()

        self.camera.open()

    def __computeObjectDepth(self, disparity, box):
        """Depth of one detection from the disparity map: Z = f*B/d.

        disparity : map at process scale (downscaled pixels)
        box       : (x1, y1, x2, y2) in FULL-resolution rectified-left pixels

        Samples only the central `shrink` fraction of the box (0.5 -> the middle
        half of its width and height). Box edges contain background, whose small
        disparity would drag the estimate far away. The median of the valid
        pixels (disparity > 0) is used so speckle outliers don't decide it.

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
        if valid.size < 5:
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

    def __estimateDepths(self, disparity, detections):
        return [self.__computeObjectDepth(disparity, det["box"])
        for det in detections]

    def estimateDepth(self):
        try:
            while True:
                left_frame, right_frame = self.camera.getFrames()
                rectified_left, rectified_right = self.processor.rectifyImages(left_frame, right_frame)
                disparity = self.processor.computeDisparity(rectified_left, rectified_right)
                detections = self.detector.detect(rectified_left)
                depths = self.__estimateDepths(disparity, detections)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

                print(f"Estimated depth: {depths}")
        except KeyboardInterrupt:
            print("Exiting depth estimation loop.")
        finally:
            self.camera.release()
            cv2.destroyAllWindows()



