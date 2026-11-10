import cv2
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
