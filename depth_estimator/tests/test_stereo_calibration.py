import warnings

import numpy as np
import pytest

from depth_estimator.services.StereoProcessor import StereoProcessor


def _write_calibration(path, *, translation_unit=None, square_size_mm=None, checkerboard=None, baseline=60.0):
    camera_matrix = np.array([[1000.0, 0, 960], [0, 1000.0, 540], [0, 0, 1]])
    values = {
        "K1": camera_matrix,
        "D1": np.zeros(5),
        "K2": camera_matrix,
        "D2": np.zeros(5),
        "R": np.eye(3),
        "T": np.array([[-baseline], [0], [0]]),
        "img_size": np.array([1920, 1080]),
        "rms_stereo": 0.3,
    }
    if translation_unit is not None:
        values["translation_unit"] = translation_unit
    if square_size_mm is not None:
        values["square_size_mm"] = square_size_mm
    if checkerboard is not None:
        values["checkerboard"] = np.array(checkerboard)
    np.savez(path, **values)


def _processor(path):
    matcher_params = {
        "blockSize": 3,
        "minDisparity": 0,
        "numDisparities": 16,
        "disp12MaxDiff": 1,
        "uniquenessRatio": 0,
        "speckleWindowSize": 0,
        "speckleRange": 0,
        "preFilterCap": 31,
        "mode": "SGBM_3WAY",
    }
    return StereoProcessor({
        "calibration_path": str(path),
        "process_scale": 1.0,
        "matcher_params": matcher_params,
    })


def test_legacy_calibration_loads_with_millimetre_warning(tmp_path):
    calibration = tmp_path / "legacy.npz"
    _write_calibration(calibration)

    with pytest.warns(RuntimeWarning, match="assuming legacy translations are in millimetres"):
        processor = _processor(calibration)

    assert processor.translation_unit == "mm"
    assert processor.square_size_mm is None
    assert processor.checkerboard_dims is None
    assert processor.getBaseline() == pytest.approx(60.0)


def test_marked_calibration_loads_optional_metadata_without_warning(tmp_path):
    calibration = tmp_path / "marked.npz"
    _write_calibration(calibration, translation_unit="mm", square_size_mm=30.0, checkerboard=(8, 5))

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        processor = _processor(calibration)

    assert processor.translation_unit == "mm"
    assert processor.square_size_mm == 30.0
    assert processor.checkerboard_dims == (8, 5)
    assert processor.getBaseline() == pytest.approx(60.0)


def test_unsupported_translation_unit_is_rejected(tmp_path):
    calibration = tmp_path / "centimetres.npz"
    _write_calibration(calibration, translation_unit="cm")

    with pytest.raises(RuntimeError, match="Unsupported translation_unit 'cm'"):
        _processor(calibration)


def test_square_size_metadata_does_not_rescale_translation(tmp_path):
    baselines = []
    for square_size in (30.0, 3.0):
        calibration = tmp_path / f"size-{square_size}.npz"
        _write_calibration(calibration, translation_unit="mm", square_size_mm=square_size)
        baselines.append(_processor(calibration).getBaseline())

    assert baselines == pytest.approx([60.0, 60.0])
