import os
import cv2
import numpy as np

class StereoProcessor:

    _SGBM_MODES = {
    "SGBM": cv2.STEREO_SGBM_MODE_SGBM,
    "HH": cv2.STEREO_SGBM_MODE_HH,
    "SGBM_3WAY": cv2.STEREO_SGBM_MODE_SGBM_3WAY,
    "HH4": cv2.STEREO_SGBM_MODE_HH4,
    }

    def __init__(self, processor_cfg):
        self.calibration_path = processor_cfg["calibration_path"]
        self.matcher_params = processor_cfg["matcher_params"]
        self.matcher = None
        self.K1 = None
        self.D1 = None
        self.K2 = None
        self.D2 = None
        self.R = None
        self.T = None
        self.img_size = None
        self.rms_stereo = None
        self.map1x = None
        self.map1y = None
        self.map2x = None
        self.map2y = None
        self.Q = None

        self.__setup()

    def __setup(self):
        self.__buildMatcher()
        self.__loadCalibration()
        self.__computeRectification()

    def rectifyImages(self, left_img, right_img):
        if left_img is None or right_img is None:
            raise ValueError("Input images cannot be None.")
        try:
            rectified_left = cv2.remap(left_img, self.map1x, self.map1y, cv2.INTER_LINEAR)
            rectified_right = cv2.remap(right_img, self.map2x, self.map2y, cv2.INTER_LINEAR)
            return rectified_left, rectified_right
        except Exception as e:
            raise RuntimeError(f"Failed to rectify images: {e}")


    def __loadCalibration(self):
        if not os.path.exists(self.calibration_path):
            raise RuntimeError(f"No calibration file at {self.calibration_path}.")
        try:
            data = np.load(self.calibration_path)
            self.K1 = data["K1"]
            self.D1 = data["D1"]
            self.K2 = data["K2"]
            self.D2 = data["D2"]
            self.R = data["R"]
            self.T = data["T"]
            self.img_size = tuple(int(x) for x in data["img_size"])
            self.rms_stereo = float(data["rms_stereo"])
        except Exception as e:
            raise RuntimeError(f"Failed to load calibration file: {e}")
        
    def __computeRectification(self):
        try:
            R1, R2, P1, P2, self.Q, roi1, roi2 = cv2.stereoRectify(
                self.K1, self.D1, self.K2, self.D2, self.img_size, self.R, self.T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=0
            )
            self.map1x, self.map1y = cv2.initUndistortRectifyMap(self.K1, self.D1, R1, P1, self.img_size, cv2.CV_32FC1)
            self.map2x, self.map2y = cv2.initUndistortRectifyMap(self.K2, self.D2, R2, P2, self.img_size, cv2.CV_32FC1)
        except Exception as e:
            raise RuntimeError(f"Failed to compute rectification: {e}")

    def getBaseline(self):
        try:
            if self.Q is None:
                raise RuntimeError("Q matrix is not computed.")
            return abs(1.0 / float(self.Q[3, 2]))
        except Exception as e:
            raise RuntimeError(f"Failed to get baseline from Q matrix: {e}")
        
    def getFocalLength(self):
        try:
            if self.Q is None:
                raise RuntimeError("Q matrix is not computed.")
            return abs(float(self.Q[2, 3]))
        except Exception as e:
            raise RuntimeError(f"Failed to get focal length from Q matrix: {e}")

    def __buildMatcher(self):
        try:
            block_size = self.matcher_params["blockSize"]
            mode_name = self.matcher_params.get("mode", "SGBM_3WAY")
            if mode_name not in self._SGBM_MODES:
                raise ValueError(f"Invalid mode '{mode_name}'. Must be one of {list(self._SGBM_MODES)}.")
            self.matcher = cv2.StereoSGBM_create(
                minDisparity=self.matcher_params["minDisparity"],
                numDisparities=self.matcher_params["numDisparities"],
                blockSize=block_size,
                P1=8 * block_size ** 2,
                P2=32 * block_size ** 2,
                disp12MaxDiff=self.matcher_params["disp12MaxDiff"],
                uniquenessRatio=self.matcher_params["uniquenessRatio"],
                speckleWindowSize=self.matcher_params["speckleWindowSize"],
                speckleRange=self.matcher_params["speckleRange"],
                preFilterCap=self.matcher_params["preFilterCap"],
                mode=self._SGBM_MODES[mode_name],
            )
        except Exception as e:
            raise RuntimeError(f"Failed to build matcher: {e}")

    def computeDisparity(self, left_img, right_img):
        """True disparity in pixels (float32). SGBM output is fixed-point x16."""
        gray_l = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
        gray_r = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)
        raw = self.matcher.compute(gray_l, gray_r)
        return raw.astype(np.float32) / 16.0



