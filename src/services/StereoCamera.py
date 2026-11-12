import cv2
import threading
from zope.interface import implementer
from src.interfaces.ICamera import ICamera

@implementer(ICamera)
class StereoCamera:
    def __init__(self, camera_cfg: dict):
        self.camera_index = camera_cfg.get("camera_index", 0)
        self.combined_width = camera_cfg.get("combined_width", 1280)
        self.combined_height = camera_cfg.get("combined_height", 480)
        self.preview_width = camera_cfg.get("preview_width", 640)
        self.frame_timeout = camera_cfg.get("frame_timeout", 2.0)
        self.__capture = None
        self.__thread = None
        self.__stop = threading.Event()
        self.__cond = threading.Condition()
        self.__latest = None
        self.__latest_id = 0
        self.__last_returned_id = 0
        self.__read_failed = False

    def open(self):
        try:
            self.__capture = cv2.VideoCapture(self.camera_index)
            if not self.__capture.isOpened():
                raise RuntimeError(f"Could not open camera index {self.camera_index}")
            self.__setupCamera()
            self.__startReader()
        except Exception as e:
            print(f"Error opening camera: {e}")
            self.__capture = None

    def __startReader(self):
        """Continuously drain the camera so only the newest frame is kept, whatever the backend queues."""
        self.__stop.clear()
        self.__latest = None
        self.__latest_id = 0
        self.__last_returned_id = 0
        self.__read_failed = False
        self.__thread = threading.Thread(target=self.__readLoop, args=(self.__capture,), daemon=True)
        self.__thread.start()

    def __readLoop(self, capture):
        while not self.__stop.is_set():
            ret, frame = capture.read()
            with self.__cond:
                if not ret:
                    self.__read_failed = True
                    self.__cond.notify_all()
                    return
                self.__latest = frame
                self.__latest_id += 1
                self.__cond.notify_all()

    def __setupCamera(self):
        try:
            if self.__capture is not None:
                self.__capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.combined_width)
                self.__capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.combined_height)
                self.__capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.__capture.set(cv2.CAP_PROP_FPS, 30)
                accepted = self.__capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not accepted or int(self.__capture.get(cv2.CAP_PROP_BUFFERSIZE)) != 1:
                    print("WARNING: backend did not honor CAP_PROP_BUFFERSIZE=1; "
                          "the reader thread still keeps only the latest frame.")

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
        """Return the newest frame from the stereo camera split into left and right images.

        Waits for a frame newer than the last one returned, so no frame is processed twice.
        """
        if self.__capture is not None:
            with self.__cond:
                got_new = self.__cond.wait_for(
                    lambda: self.__latest_id > self.__last_returned_id or self.__read_failed,
                    timeout=self.frame_timeout,
                )
                if not got_new or self.__latest_id == self.__last_returned_id:
                    print("Failed to grab frame")
                    return None, None
                frame = self.__latest
                self.__last_returned_id = self.__latest_id
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
        self.__stop.set()
        if self.__thread is not None:
            self.__thread.join(timeout=2.0)
            self.__thread = None
        if self.__capture is not None:
            self.__capture.release()
            self.__capture = None

    def resize_for_preview(self, img):
        h, w = img.shape[:2]
        scale = self.preview_width / w
        return cv2.resize(img, (self.preview_width, int(h * scale)))

