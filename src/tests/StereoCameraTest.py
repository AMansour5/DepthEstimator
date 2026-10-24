import cv2
from src.utils.Configurator import Configurator
from src.services.StereoCamera import StereoCamera

class StereoCameraTest:
    def __init__(self):
        self.configurator = Configurator()
        self.stereo_camera_cfg = self.configurator.fetchData(self.configurator.STEREO_CAMERA)
        self.stereo_camera = StereoCamera(self.stereo_camera_cfg)
        self.preview_width = self.stereo_camera_cfg.get("preview_width", 640)
        self.capture = None

    def test_camera_open(self):
        """Test if the stereo camera can be opened successfully."""
        self.stereo_camera.open()
        self.capture = self.stereo_camera.getCapture()
        assert self.capture is not None and self.capture.isOpened(), "Failed to open stereo camera."

    def test_frame_capture(self):
        """Test if a frame can be captured from the stereo camera."""
        left_frame, right_frame = self.stereo_camera.getFrames()
        assert left_frame is not None, "Failed to capture left frame."
        assert right_frame is not None, "Failed to capture right frame."

    def test_view_feed(self):
        """Test if the stereo camera feed can be viewed."""
        while True:
            left_frame, right_frame = self.stereo_camera.getFrames()
            if left_frame is None or right_frame is None:
                print("Failed to capture frames. Exiting.")
                break

            left_frame_resized = self.resize_for_preview(left_frame, self.preview_width)
            right_frame_resized = self.resize_for_preview(right_frame, self.preview_width)

            cv2.imshow("Left Camera Feed", left_frame_resized)
            cv2.imshow("Right Camera Feed", right_frame_resized)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()
        self.stereo_camera.release()

    def resize_for_preview(self, img, target_width):
        h, w = img.shape[:2]
        scale = target_width / w
        return cv2.resize(img, (target_width, int(h * scale)))

if __name__ == "__main__":
    test = StereoCameraTest()
    test.test_camera_open()
    test.test_frame_capture()
    test.test_view_feed()