"""Shared helpers for the evidence scripts.

Every script here runs on SYNTHETIC data (no camera, no calibration file, no YOLO
weights needed). They import the real classes from src/ wherever possible, and
read the real values from config/*.yaml, so they exercise your actual code and
your actual settings.

Run any script from anywhere:  python docs/problems/evidence/pXX_name.py
Needs: numpy, opencv-python, pyyaml  (p04 also needs zope.interface, p06 needs pytest)
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Disparity-map size used in the experiments: a 1920x1080 frame at process_scale 0.5.
W, H = 960, 540


def load_stereo_processor_cfg():
    with open(ROOT / "config" / "stereo_processor.yaml") as f:
        return yaml.safe_load(f)


def build_matcher(matcher_params, **override):
    """Same SGBM construction as StereoProcessor.__buildMatcher (repo code)."""
    p = {**matcher_params, **override}
    b = p["blockSize"]
    return cv2.StereoSGBM_create(
        minDisparity=p["minDisparity"], numDisparities=p["numDisparities"], blockSize=b,
        P1=8 * b * b, P2=32 * b * b, disp12MaxDiff=p["disp12MaxDiff"],
        uniquenessRatio=p["uniquenessRatio"], speckleWindowSize=p["speckleWindowSize"],
        speckleRange=p["speckleRange"], preFilterCap=p["preFilterCap"],
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY,
    )


def disparity(matcher, left, right):
    """True disparity in pixels (SGBM returns fixed point x16), like StereoProcessor."""
    return matcher.compute(left, right).astype(np.float32) / 16.0


def make_scene(objects=(), bg_d=10, seed=5):
    """A textured stereo pair with known disparities.

    Background is at disparity `bg_d`. Each object is (x0, x1, y0, y1, d): its own
    random texture, drawn at x in the left image and at x-d in the right image.
    """
    rng = np.random.default_rng(seed)
    tex = cv2.GaussianBlur((rng.random((H, W + 400)) * 255).astype(np.uint8), (3, 3), 0)
    left = tex[:, :W].copy()
    right = tex[:, bg_d:bg_d + W].copy()
    for (x0, x1, y0, y1, d) in objects:
        patch = cv2.GaussianBlur((rng.random((y1 - y0, x1 - x0)) * 255).astype(np.uint8), (3, 3), 0)
        left[y0:y1, x0:x1] = patch
        right[y0:y1, x0 - d:x1 - d] = patch
    return left, right


def synthetic_calibration(path, img_size=(1920, 1080), f=1000.0, baseline=60.0):
    """Write a calibration .npz in the format StereoProcessor expects (illustrative numbers)."""
    K = np.array([[f, 0, img_size[0] / 2], [0, f, img_size[1] / 2], [0, 0, 1]])
    np.savez(path, K1=K, D1=np.zeros(5), K2=K, D2=np.zeros(5), R=np.eye(3),
             T=np.array([[-baseline], [0], [0]]), img_size=np.array(img_size), rms_stereo=0.3)
