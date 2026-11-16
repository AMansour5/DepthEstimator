import cv2
import numpy as np

from src.services.StereoProcessor import StereoProcessor
from src.utils.DisparityVisualizer import DisparityVisualizer


def _processor(num_disparities=64):
    params = dict(
        blockSize=5,
        disp12MaxDiff=1,
        minDisparity=0,
        mode="SGBM_3WAY",
        numDisparities=num_disparities,
        preFilterCap=31,
        speckleRange=0,
        speckleWindowSize=0,
        uniquenessRatio=0,
    )
    processor = StereoProcessor.__new__(StereoProcessor)
    processor.process_scale = 1.0
    processor.matcher_params = params
    processor.matcher = processor.buildMatcher()
    return processor


def _stereo_pair(width=320, height=160, disparity=24):
    rng = np.random.default_rng(42)
    texture = rng.integers(0, 256, (height, width + disparity), dtype=np.uint8)
    texture = cv2.GaussianBlur(texture, (3, 3), 0.7)
    left = texture[:, :width]
    right = texture[:, disparity:disparity + width]
    return cv2.cvtColor(left, cv2.COLOR_GRAY2BGR), cv2.cvtColor(right, cv2.COLOR_GRAY2BGR)


def test_compute_disparity_recovers_left_edge_and_keeps_original_shape():
    processor = _processor()
    left, right = _stereo_pair()

    disparity = processor.computeDisparity(left, right)

    assert disparity.shape == left.shape[:2]
    valid_fraction = np.mean(disparity > 0, axis=0)
    first_valid_column = int(np.flatnonzero(valid_fraction > 0.5)[0])
    assert first_valid_column < processor.matcher_params["numDisparities"] // 2

    recovered = disparity[20:-20, 32:40]
    recovered = recovered[recovered > 0]
    assert recovered.size > 0
    assert abs(float(np.median(recovered)) - 24.0) < 1.0


def test_compute_disparity_pads_after_resize_using_override_range():
    processor = _processor(num_disparities=16)
    processor.process_scale = 0.5
    captured = {}

    class RecordingMatcher:
        def compute(self, left, right):
            captured["left_shape"] = left.shape
            captured["right_shape"] = right.shape
            return np.full(left.shape, 12 * 16, dtype=np.int16)

    matcher = RecordingMatcher()
    processor.buildMatcher = lambda _overrides: matcher
    image = np.zeros((80, 100, 3), dtype=np.uint8)

    disparity = processor.computeDisparity(image, image, {"numDisparities": 32})

    assert captured["left_shape"] == (40, 82)
    assert captured["right_shape"] == (40, 82)
    assert disparity.shape == (40, 50)
    assert np.all(disparity == 12.0)


def test_left_invalid_band_highlight_uses_map_validity():
    disparity = np.full((6, 12), -1.0, dtype=np.float32)
    disparity[:, 4:] = 10.0
    colored = DisparityVisualizer.colorizeDisparity(disparity, 32)

    highlighted = DisparityVisualizer.highlightLeftInvalidBand(colored, disparity)

    assert np.all(highlighted[:, :4] == (0, 0, 128))
    assert np.all(highlighted[:, 4] == (0, 0, 255))
    assert np.all(highlighted[:, 5:] == colored[:, 5:])


def test_left_invalid_band_highlight_skips_maps_without_valid_disparity():
    disparity = np.full((6, 12), -1.0, dtype=np.float32)
    colored = DisparityVisualizer.colorizeDisparity(disparity, 32)

    highlighted = DisparityVisualizer.highlightLeftInvalidBand(colored, disparity)

    assert np.array_equal(highlighted, colored)
