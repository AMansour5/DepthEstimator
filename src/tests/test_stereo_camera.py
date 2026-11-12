import threading
import time
import cv2
import numpy as np
from src.utils.Configurator import Configurator
from src.services.StereoCamera import StereoCamera

def test_camera_open():
    """Test if the stereo camera can be opened successfully."""
    configurator = Configurator()
    stereo_camera_cfg = configurator.fetchData(configurator.STEREO_CAMERA)
    stereo_camera = StereoCamera(stereo_camera_cfg)
    stereo_camera.open()
    capture = stereo_camera.getCapture()
    assert capture is not None and capture.isOpened(), "Failed to open stereo camera."
    stereo_camera.release()

def test_frame_capture():
    """Test if a frame can be captured from the stereo camera."""
    configurator = Configurator()
    stereo_camera_cfg = configurator.fetchData(configurator.STEREO_CAMERA)
    stereo_camera = StereoCamera(stereo_camera_cfg)
    stereo_camera.open()
    left_frame, right_frame = stereo_camera.getFrames()
    assert left_frame is not None, "Failed to capture left frame."
    assert right_frame is not None, "Failed to capture right frame."
    stereo_camera.release()

def test_view_feed():
    """Test if the stereo camera feed can be viewed."""
    configurator = Configurator()
    stereo_camera_cfg = configurator.fetchData(configurator.STEREO_CAMERA)
    stereo_camera = StereoCamera(stereo_camera_cfg)
    preview_width = stereo_camera_cfg.get("preview_width", 640)
    stereo_camera.open()
    while True:
        left_frame, right_frame = stereo_camera.getFrames()
        if left_frame is None or right_frame is None:
            print("Failed to capture frames. Exiting.")
            break

        left_frame_resized = resize_for_preview(left_frame, preview_width)
        right_frame_resized = resize_for_preview(right_frame, preview_width)

        cv2.imshow("Left Camera Feed", left_frame_resized)
        cv2.imshow("Right Camera Feed", right_frame_resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    stereo_camera.release()

def resize_for_preview(img, target_width):
    h, w = img.shape[:2]
    scale = target_width / w
    return cv2.resize(img, (target_width, int(h * scale)))


class _FakeCapture:
    """Produces frames whose pixel value is the frame number, at a fixed rate."""

    def __init__(self, period=0.005):
        self.period = period
        self.count = 0

    def isOpened(self):
        return True

    def set(self, *_args):
        return True

    def get(self, *_args):
        return 1

    def read(self):
        time.sleep(self.period)
        self.count += 1
        return True, np.full((4, 8, 3), self.count % 256, dtype=np.uint8)

    def release(self):
        pass


def _open_fake_camera(monkeypatch):
    monkeypatch.setattr(cv2, "VideoCapture", lambda *_a, **_k: _FakeCapture())
    camera = StereoCamera({"combined_width": 8, "combined_height": 4})
    camera.open()
    return camera


def test_slow_consumer_gets_latest_frame(monkeypatch):
    camera = _open_fake_camera(monkeypatch)
    try:
        camera.getFrames()
        time.sleep(0.3)  # producer makes ~60 frames meanwhile
        left, _ = camera.getFrames()
        assert int(left[0, 0, 0]) > 20, "got an old queued frame instead of the latest"
    finally:
        camera.release()


def test_frames_are_not_returned_twice(monkeypatch):
    camera = _open_fake_camera(monkeypatch)
    try:
        values = [int(camera.getFrames()[0][0, 0, 0]) for _ in range(5)]
        assert values == sorted(set(values))
    finally:
        camera.release()


def test_release_stops_reader_thread(monkeypatch):
    camera = _open_fake_camera(monkeypatch)
    before = threading.active_count()
    camera.release()
    assert threading.active_count() == before - 1
