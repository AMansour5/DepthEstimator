"""Hardware-free regression tests for Configurator.setConfig.

Run from the repository root: python -m pytest -q src/tests/test_configurator_set_config.py
"""
import yaml
from src.utils.Configurator import Configurator


def _point_project_root_at(monkeypatch, project_root):
    monkeypatch.setattr(Configurator, "getProjectRoot", lambda: str(project_root))


def test_set_config_creates_missing_file(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    _point_project_root_at(monkeypatch, tmp_path)

    configurator = Configurator()
    configurator.setConfig(Configurator.STEREO_CAMERA, {"combined_width": 5, "combined_height": 8})

    written_file = tmp_path / "config" / "stereo_camera.yaml"
    assert written_file.exists()
    assert yaml.safe_load(written_file.read_text()) == {"combined_width": 5, "combined_height": 8}


def test_set_config_merges_and_preserves_untouched_keys(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "stereo_camera.yaml"
    config_file.write_text(yaml.safe_dump({"combined_width": 5, "combined_height": 8, "preview_width": 30}))
    _point_project_root_at(monkeypatch, tmp_path)

    configurator = Configurator()
    configurator.setConfig(Configurator.STEREO_CAMERA, {"combined_width": 6})

    updated = yaml.safe_load(config_file.read_text())
    assert updated == {"combined_width": 6, "combined_height": 8, "preview_width": 30}
