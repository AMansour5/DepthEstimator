import os
import json
import math
import time
import cv2
import numpy as np
from src.utils.Configurator import Configurator
from src.services.StereoProcessor import StereoProcessor
from src.services.StereoCamera import StereoCamera

class DisparityTuner:
    # Nearest distance (mm) depth is needed at; only used to hint the numDisparities required.
    Z_MIN_MM = 500.0

    def __init__(self):
        self.TRACKBAR_WINDOW = "Disparity Tuner"
        self.DISPLAY_WINDOW = "rectified L|R (top) - gray L | disparity (bottom)"
        self.configurator = Configurator()
        self.stereo_processor = StereoProcessor(self.configurator.fetchData(self.configurator.STEREO_PROCESSOR))
        self.camera = StereoCamera(self.configurator.fetchData(self.configurator.STEREO_CAMERA))
        self.results_dir = os.path.join(Configurator.getProjectRoot(), "disparity_tuning_results")
        self.__probe = {"click": None, "disparity": None, "scale": 1.0, "panel": (0, 0)}

    def _nothing(self, _x):
        pass

    def __createTrackbars(self):
        cv2.namedWindow(self.TRACKBAR_WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.TRACKBAR_WINDOW, 500, 400)
        # process scale x10 -> 0.2 to 1.0; this is the main lag fix, start low
        cv2.createTrackbar("minDisparity", self.TRACKBAR_WINDOW, 0, 10, self._nothing)
        cv2.createTrackbar("process scale x10", self.TRACKBAR_WINDOW, 5, 10, self._nothing)
        # numDisparities must be a positive multiple of 16 -> slider is that multiple
        cv2.createTrackbar("numDisp x16", self.TRACKBAR_WINDOW, 4, 35, self._nothing)   # 16-320
        cv2.createTrackbar("blockSize idx", self.TRACKBAR_WINDOW, 3, 10, self._nothing)  # -> 3-23 odd
        cv2.createTrackbar("uniquenessRatio", self.TRACKBAR_WINDOW, 10, 30, self._nothing)
        cv2.createTrackbar("speckleWindowSize", self.TRACKBAR_WINDOW, 100, 200, self._nothing)
        cv2.createTrackbar("speckleRange", self.TRACKBAR_WINDOW, 2, 5, self._nothing)
        cv2.createTrackbar("disp12MaxDiff", self.TRACKBAR_WINDOW, 5, 25, self._nothing)
        cv2.createTrackbar("preFilterCap", self.TRACKBAR_WINDOW, 31, 63, self._nothing)

    def __readParams(self, max_num_disp):
        num_disp = max(16, cv2.getTrackbarPos("numDisp x16", self.TRACKBAR_WINDOW) * 16)
        num_disp = min(num_disp, max_num_disp)
        block_idx = cv2.getTrackbarPos("blockSize idx", self.TRACKBAR_WINDOW)
        block_size = max(3, 2 * block_idx + 3)  # keep odd, floor at 3
        return dict(
            numDisparities=num_disp,
            blockSize=block_size,
            minDisparity=cv2.getTrackbarPos("minDisparity", self.TRACKBAR_WINDOW),
            uniquenessRatio=cv2.getTrackbarPos("uniquenessRatio", self.TRACKBAR_WINDOW),
            speckleWindowSize=cv2.getTrackbarPos("speckleWindowSize", self.TRACKBAR_WINDOW),
            speckleRange=cv2.getTrackbarPos("speckleRange", self.TRACKBAR_WINDOW),
            disp12MaxDiff=cv2.getTrackbarPos("disp12MaxDiff", self.TRACKBAR_WINDOW),
            preFilterCap=max(1, cv2.getTrackbarPos("preFilterCap", self.TRACKBAR_WINDOW)),
        )

    def colorizeDisparity(self, disparity, num_disp):
        valid = disparity > 0
        vis = np.zeros_like(disparity, dtype=np.uint8)
        if np.any(valid):
            vis[valid] = np.clip(disparity[valid] * 255.0 / num_disp, 0, 255).astype(np.uint8)
        colored = cv2.applyColorMap(vis, cv2.COLORMAP_TURBO)
        colored[~valid] = (0, 0, 0)
        return colored

    def __readProcessScale(self):
        return max(0.2, cv2.getTrackbarPos("process scale x10", self.TRACKBAR_WINDOW) / 10.0)

    def __buildMatcher(self, params):
        base = self.stereo_processor.matcher_params
        block_size = params["blockSize"]
        mode = StereoProcessor._SGBM_MODES[base.get("mode", "SGBM_3WAY")]
        return cv2.StereoSGBM_create(
            minDisparity=params["minDisparity"],
            numDisparities=params["numDisparities"],
            blockSize=block_size,
            P1=8 * block_size ** 2,
            P2=32 * block_size ** 2,
            disp12MaxDiff=params["disp12MaxDiff"],
            uniquenessRatio=params["uniquenessRatio"],
            speckleWindowSize=params["speckleWindowSize"],
            speckleRange=params["speckleRange"],
            preFilterCap=params["preFilterCap"],
            mode=mode,
        )

    def __computeDisparity(self, gray_l, gray_r, params):
        """True disparity in pixels (float32); SGBM output is fixed-point x16."""
        raw = self.__buildMatcher(params).compute(gray_l, gray_r)
        return raw.astype(np.float32) / 16.0

    def __measureAt(self, u, v):
        """Depth at normalized left-image position (u, v): Z = f*B/d, using the median of a 5x5 patch."""
        disp = self.__probe["disparity"]
        if disp is None:
            return "no disparity yet"
        h, w = disp.shape
        col, row = min(int(u * w), w - 1), min(int(v * h), h - 1)
        patch = disp[max(0, row - 2):row + 3, max(0, col - 2):col + 3]
        valid = patch[patch > 0]
        if valid.size < 3:
            return "no valid disparity here (occluded, textureless, or filtered out)"
        d = float(np.median(valid))
        f = self.stereo_processor.getFocalLength() * self.__probe["scale"]
        z_mm = f * self.stereo_processor.getBaseline() / d
        spread = float(valid.max() - valid.min())
        return f"d={d:.1f}px  Z={z_mm / 10:.1f} cm  ({valid.size}/{patch.size} valid, spread {spread:.1f}px)"

    def __onMouse(self, event, x, y, _flags, _param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        pw, ph = self.__probe["panel"]
        if pw == 0:
            return
        if x < pw and y < ph:
            u, v = x / pw, y / ph
        elif ph <= y < 2 * ph and x < 2 * pw:
            u, v = (x % pw) / pw, (y - ph) / ph
        else:
            return
        self.__probe["click"] = (u, v)
        print(self.__measureAt(u, v))

    @staticmethod
    def __drawText(img, text, org, scale=0.6):
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 4)
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 2)

    def __saveSnapshot(self, rect_l, rect_r, colored, params, scale, full_res_equiv):
        os.makedirs(self.results_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        cv2.imwrite(os.path.join(self.results_dir, f"rect_l_{ts}.png"), rect_l)
        cv2.imwrite(os.path.join(self.results_dir, f"rect_r_{ts}.png"), rect_r)
        cv2.imwrite(os.path.join(self.results_dir, f"disparity_{ts}.png"), colored)
        params_out = dict(params)
        params_out["process_scale"] = scale
        params_out["numDisparities_full_res_equivalent"] = full_res_equiv
        with open(os.path.join(self.results_dir, f"params_{ts}.json"), "w") as f:
            json.dump(params_out, f, indent=2)
        print(f"Saved snapshot + params -> {self.results_dir} ({ts})")

    def __writeParams(self, params, scale):
        """Store the tuned params under matcher_params, keeping keys the tuner doesn't touch (minDisparity, mode)."""
        try:
            current = self.configurator.fetchData(self.configurator.STEREO_PROCESSOR) or {}
            matcher_params = dict(current.get("matcher_params", {}))
            matcher_params.update(params)
            # setConfig only merges top-level keys, so pass the full matcher_params block
            self.configurator.setConfig(self.configurator.STEREO_PROCESSOR, {"process_scale": round(float(scale), 2), "matcher_params": matcher_params})
            print("Parameters successfully written.")
        except Exception as e:
            print(f"Error writing parameters: {e}")


    def tuneDisparity(self):
        """Live SGBM tuning. Click a panel to measure depth, 's' saves params + snapshot, 'q' quits."""
        f_full = self.stereo_processor.getFocalLength()
        baseline = self.stereo_processor.getBaseline()
        d_max = f_full * baseline / self.Z_MIN_MM
        print(f"Focal length (full res): {f_full:.1f} px, baseline: {baseline:.2f} mm")
        print(f"Z_min {self.Z_MIN_MM / 10:.0f} cm -> disparity {d_max:.0f} px at full res "
              f"-> numDisparities >= {math.ceil(d_max / 16) * 16} at full res")

        self.camera.open()
        if self.camera.getCapture() is None:
            raise RuntimeError("Could not open camera")

        cv2.namedWindow(self.DISPLAY_WINDOW)
        cv2.setMouseCallback(self.DISPLAY_WINDOW, self.__onMouse)
        self.__createTrackbars()
        print("Press 's' to save snapshot, 'd' to write params to config, 'q' to quit.")

        fps_smoothed = 0.0
        try:
            while True:
                left, right = self.camera.getFrames()
                if left is None:
                    break
                rect_l, rect_r = self.stereo_processor.rectifyImages(left, right)
                gray_l_full = cv2.cvtColor(rect_l, cv2.COLOR_BGR2GRAY)
                gray_r_full = cv2.cvtColor(rect_r, cv2.COLOR_BGR2GRAY)

                scale = self.__readProcessScale()
                if scale < 0.999:
                    gray_l = cv2.resize(gray_l_full, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                    gray_r = cv2.resize(gray_r_full, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                else:
                    gray_l, gray_r = gray_l_full, gray_r_full

                max_num_disp = max(16, ((gray_l.shape[1] - 32) // 16) * 16)
                params = self.__readParams(max_num_disp)

                t0 = time.time()
                disparity = self.__computeDisparity(gray_l, gray_r, params)
                dt = time.time() - t0
                inst_fps = 1.0 / dt if dt > 0 else 0.0
                fps_smoothed = 0.9 * fps_smoothed + 0.1 * inst_fps if fps_smoothed > 0 else inst_fps

                colored = self.colorizeDisparity(disparity, params["numDisparities"])

                top = cv2.hconcat([rect_l, rect_r])
                top_small = cv2.resize(top, (960, int(960 * top.shape[0] / top.shape[1])))
                half_w = top_small.shape[1] // 2
                panel_h = top_small.shape[0]
                colored_disp = cv2.resize(colored, (half_w, panel_h), interpolation=cv2.INTER_NEAREST)
                gray_small = cv2.resize(cv2.cvtColor(gray_l_full, cv2.COLOR_GRAY2BGR), (half_w, panel_h))
                display = cv2.vconcat([top_small, cv2.hconcat([gray_small, colored_disp])])

                self.__probe.update(disparity=disparity, scale=scale, panel=(half_w, panel_h))
                if self.__probe["click"] is not None:
                    u, v = self.__probe["click"]
                    for ox, oy in ((0, 0), (0, panel_h), (half_w, panel_h)):
                        cv2.drawMarker(display, (int(ox + u * half_w), int(oy + v * panel_h)),
                                       (255, 255, 255), cv2.MARKER_CROSS, 18, 2)
                    self.__drawText(display, self.__measureAt(u, v), (15, 2 * panel_h - 15))

                full_res_equiv = int(params["numDisparities"] / scale)
                need = math.ceil(f_full * scale * baseline / self.Z_MIN_MM / 16) * 16
                cv2.putText(display,
                            f"scale={scale:.1f}  disparity compute: {fps_smoothed:5.1f} FPS  "
                            f"numDisp={params['numDisparities']} (~{full_res_equiv} @ full res)",
                            (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(display,
                            f"numDisp needed for Z_min={self.Z_MIN_MM / 10:.0f} cm at this scale: {need}",
                            (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow(self.DISPLAY_WINDOW, display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("s"):
                    self.__saveSnapshot(rect_l, rect_r, colored, params, scale, full_res_equiv)
                if key == ord("d"):
                    self.__writeParams(params, scale)
        finally:
            self.camera.release()
            cv2.destroyAllWindows()

    