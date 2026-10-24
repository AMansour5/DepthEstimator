import cv2
from zope.interface import implementer
from src.interfaces.ICamera import ICamera

@implementer(ICamera)
class StereoCamera:
    def __init__(self, camera_cfg: dict):
        self.camera_index = camera_cfg.get("camera_index", 0)
        self.combined_width = camera_cfg.get("combined_width", 1280)
        self.combined_height = camera_cfg.get("combined_height", 480)
        self.preview_width = camera_cfg.get("preview_width", 640)
        self.__capture = None

    def open(self):
        try:
            self.__capture = cv2.VideoCapture(self.camera_index)
            if not self.__capture.isOpened():
                raise RuntimeError(f"Could not open camera index {self.camera_index}")
            self.__setupCamera()
        except Exception as e:
            print(f"Error opening camera: {e}")
            self.__capture = None

    def __setupCamera(self):
        try:
            if self.__capture is not None:
                self.__capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.combined_width)
                self.__capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.combined_height)
                self.__capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.__capture.set(cv2.CAP_PROP_FPS, 30)

                actual_w = int(self.__capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(self.__capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"Requested {self.combined_width}x{self.combined_height}, camera reports {actual_w}x{actual_h}")
                if actual_w != self.combined_width or actual_h != self.combined_height:
                    print("WARNING: camera did not accept the requested resolution. "
                          "Update combined_width/combined_height to match what it reports, "
                          "or the left/right split below will be wrong.")
        except Exception as e:
            print(f"Error setting up camera: {e}")

    def getFrames(self):
        """__Capture a frame from the stereo camera and split it into left and right images."""
        if self.__capture is not None:
            ret, frame = self.__capture.read()
            if not ret:
                print("Failed to grab frame")
                return None, None
            return self.__split_frame(frame)
        else:
            print("Camera is not opened.")
            return None, None

    def __split_frame(self, frame):
        """Split a combined side-by-side stereo frame into (left, right) halves."""
        h, w = frame.shape[:2]
        mid = w // 2
        return frame[:, :mid], frame[:, mid:]

    def getCapture(self):
        return self.__capture

    def release(self):
        if self.__capture is not None:
            self.__capture.release()
            self.__capture = None

    def resize_for_preview(self, img):
        h, w = img.shape[:2]
        scale = self.preview_width / w
        return cv2.resize(img, (self.preview_width, int(h * scale)))

