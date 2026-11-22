"""P02: reject frames whose size does not match the calibration or the requested camera mode.

Part A: StereoProcessor.rectifyImages with the real class and a synthetic 1920x1080 calibration.
Part B: StereoCamera when the device negotiates another resolution (fake capture, no hardware).
"""
import tempfile
from common import *
from src.services.StereoCamera import StereoCamera
from src.services.StereoProcessor import StereoProcessor
from src.exceptions.DifferentImageSizeError import DifferentImageSizeError

with tempfile.TemporaryDirectory() as tmp:
    calib = f"{tmp}/stereo_calib.npz"
    synthetic_calibration(calib, img_size=(1920, 1080))
    cfg = load_stereo_processor_cfg()
    cfg["calibration_path"] = calib
    sp = StereoProcessor(cfg)
    print(f"calibrated for {sp.calib_img_size}\n")
    print("A) rectifyImages(left, right)")

    rng = np.random.default_rng(0)
    img = lambda w, h: (rng.random((h, w, 3)) * 255).astype(np.uint8)
    cases = {
        "both 1920x1080 (matches)": (img(1920, 1080), img(1920, 1080)),
        "both 640x480 (StereoCamera's default 1280x480 combined)": (img(640, 480), img(640, 480)),
        "both 640x720 (camera negotiated 1280x720 combined)": (img(640, 720), img(640, 720)),
        "left 1920x1080, RIGHT 640x480": (img(1920, 1080), img(640, 480)),
    }
    outcome = {}
    for label, (l, r) in cases.items():
        try:
            rl, rr = sp.rectifyImages(l, r)
            outcome[label] = "no error"
            print(f"   {label:<58} -> no exception, right output {rr.shape[1]}x{rr.shape[0]}, "
                  f"{(rr.sum(axis=2) > 0).mean():.0%} of it has image content")
        except DifferentImageSizeError:
            outcome[label] = "raised"
            print(f"   {label:<58} -> DifferentImageSizeError")

print("\nB) StereoCamera.open() when the device does not give the requested size")


class FakeCapture:
    """Requested 3840x1080, but reports 1280x720 (a common V4L2 fallback)."""
    def isOpened(self): return True
    def set(self, *_): return True
    def get(self, prop):
        return {cv2.CAP_PROP_FRAME_WIDTH: 1280, cv2.CAP_PROP_FRAME_HEIGHT: 720}.get(prop, 1)
    def read(self): return False, None
    def release(self): pass


cv2.VideoCapture = lambda *_a, **_k: FakeCapture()
cam = StereoCamera({"combined_width": 3840, "combined_height": 1080})
print("   (console output of open():)")
camera_rejected = False
try:
    cam.open()
except RuntimeError as e:
    camera_rejected = True
    print(f"   open() rejected the size mismatch: {e}")
else:
    print("   open() unexpectedly accepted the size mismatch")
cam.release()

right_unchecked = outcome["left 1920x1080, RIGHT 640x480"] == "no error"
left_checked = outcome["both 640x480 (StereoCamera's default 1280x480 combined)"] == "raised"
if left_checked and not right_unchecked and camera_rejected:
    verdict("FIXED", "both images and the camera are checked")
elif left_checked:
    verdict("PARTLY FIXED",
            "a wrong LEFT size now raises DifferentImageSizeError, but a wrong RIGHT size passes unchecked or the camera "
            "accepts a mismatched negotiated size")
else:
    verdict("STILL PRESENT", "mismatched frames are still rectified silently")
