"""P09: Configurator turns errors into None, and setConfig rewrites the whole file."""
import tempfile
from pathlib import Path
from common import *
from src.utils.Configurator import Configurator

with tempfile.TemporaryDirectory() as tmp:
    (Path(tmp) / "config").mkdir()
    Configurator.getProjectRoot = staticmethod(lambda: tmp)
    shutil_src = ROOT / "config" / "object_detector.yaml"
    target = Path(tmp) / "config" / "object_detector.yaml"
    target.write_text(shutil_src.read_text())
    print("A) object_detector.yaml before setConfig(conf_threshold=0.6):\n" +
          "\n".join("   | " + l for l in target.read_text().splitlines()))
    Configurator().setConfig(Configurator.OBJECT_DETECTOR, {"conf_threshold": 0.6})
    print("\n   after (comments gone, keys re-sorted, quotes dropped):\n" +
          "\n".join("   | " + l for l in target.read_text().splitlines()))

    print("\nB) errors become None")
    c = Configurator()
    print("   unknown type          ->", c.fetchData("bogus"))
    (Path(tmp) / "config" / "stereo_camera.yaml").write_text("camera_index: [unclosed")
    print("   malformed yaml        ->", c.fetchData(Configurator.STEREO_CAMERA))
    print("   missing file          ->", c.fetchData(Configurator.DEPTH_ESTIMATOR))
