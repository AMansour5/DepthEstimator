import yaml
from pathlib import Path
from depth_estimator.utils.Configurator import Configurator

def test_load_camera_config():
    configurator = Configurator()
    config = configurator.fetchData(Configurator.STEREO_CAMERA)
    assert config["camera_index"] == "/dev/video2"
    assert config["combined_width"] == 3840
    assert config["combined_height"] == 1080
    assert config["preview_width"] == 640

def _point_config_dir_at(monkeypatch, config_dir):
    monkeypatch.setattr(Configurator, "getConfigDir", lambda: config_dir)

def test_set_config_creates_missing_file(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    _point_config_dir_at(monkeypatch, config_dir)

    configurator = Configurator()
    configurator.setConfig(Configurator.STEREO_CAMERA, {"combined_width": 5, "combined_height": 8})

    written_file = config_dir / "stereo_camera.yaml"
    assert written_file.exists()
    assert yaml.safe_load(written_file.read_text()) == {
        "camera_index": "/dev/video2",
        "combined_width": 5,
        "combined_height": 8,
        "preview_width": 640,
    }

def test_set_config_merges_and_preserves_untouched_keys(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "stereo_camera.yaml"
    config_file.write_text(yaml.safe_dump({"combined_width": 5, "combined_height": 8, "preview_width": 30}))
    _point_config_dir_at(monkeypatch, config_dir)

    configurator = Configurator()
    configurator.setConfig(Configurator.STEREO_CAMERA, {"combined_width": 6})

    updated = yaml.safe_load(config_file.read_text())
    assert updated == {"combined_width": 6, "combined_height": 8, "preview_width": 30}


def test_resolve_path_is_package_relative(tmp_path):
    package_relative = Configurator.resolvePath("matrices/stereo_calib.npz")
    assert package_relative == str(Path(Configurator.getProjectRoot()) / "matrices/stereo_calib.npz")
    absolute = tmp_path / "calibration.npz"
    assert Configurator.resolvePath(str(absolute)) == str(absolute)
