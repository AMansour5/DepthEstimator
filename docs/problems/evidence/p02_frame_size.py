"""P02: nothing checks that the frames being rectified have the size the calibration was made for."""
import tempfile
from common import *
from src.services.StereoProcessor import StereoProcessor

with tempfile.TemporaryDirectory() as tmp:
    calib = f"{tmp}/stereo_calib.npz"
    synthetic_calibration(calib, img_size=(1920, 1080))
    cfg = load_stereo_processor_cfg()
    cfg["calibration_path"] = calib
    sp = StereoProcessor(cfg)
    print(f"calibrated for {sp.img_size}\n")

    rng = np.random.default_rng(0)
    cases = {"matches calibration": (1920, 1080),
             "StereoCamera default size 1280x480 combined -> 640x480 per eye": (640, 480),
             "camera negotiated 1280x720 combined -> 640x720 per eye": (640, 720)}
    for label, (w, h) in cases.items():
        img = (rng.random((h, w, 3)) * 255).astype(np.uint8)
        rl, rr = sp.rectifyImages(img, img)
        print(f"{label}\n   input {w}x{h} -> output {rl.shape[1]}x{rl.shape[0]}, "
              f"no exception, {(rl.sum(axis=2) > 0).mean():.0%} of output pixels have image content")
