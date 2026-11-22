"""P09: Configurator. fetchData now raises; setConfig still destroys comments, re-sorts keys and is not atomic.

Everything runs against a temporary copy of the config folder; your real files are never touched.
"""
import tempfile
from pathlib import Path
from common import *
from depth_estimator.utils.Configurator import Configurator

with tempfile.TemporaryDirectory() as tmp:
    config_dir = Path(tmp)
    Configurator.getConfigDir = staticmethod(lambda: config_dir)
    source = ROOT / "depth_estimator" / "config" / "object_detector.yaml"
    target = config_dir / "object_detector.yaml"
    target.write_text(source.read_text())
    lines = lambda: "\n".join("   | " + l for l in target.read_text().splitlines())
    before = target.read_text()

    print("A) object_detector.yaml before setConfig(conf_threshold=0.6):\n" + lines())
    Configurator().setConfig(Configurator.OBJECT_DETECTOR, {"conf_threshold": 0.6})
    print("\n   after:\n" + lines())
    comments_lost = "#" in before and "#" not in target.read_text()

    print("\nB) fetchData errors")
    c = Configurator()
    (config_dir / "stereo_camera.yaml").write_text("camera_index: [unclosed")
    raised = 0
    for label, call in (("unknown type", lambda: c.fetchData("bogus")),
                        ("malformed yaml", lambda: c.fetchData(Configurator.STEREO_CAMERA))):
        try:
            print(f"   {label:<15} -> returned {call()!r}")
        except Exception as e:
            raised += 1
            print(f"   {label:<15} -> {type(e).__name__}")

    print("\nC) setConfig with a value YAML cannot serialise (simulates a failure while writing)")
    good = target.read_text()
    try:
        Configurator().setConfig(Configurator.OBJECT_DETECTOR, {"conf_threshold": object()})
    except Exception as e:
        print(f"   raised {type(e).__name__}")
    left = target.read_text()
    non_atomic = left != good
    print(f"   file afterwards: {len(left)} bytes (was {len(good)})" + ("  <-- the original content is gone" if non_atomic else ""))

print()
if raised == 2 and not comments_lost and not non_atomic:
    verdict("FIXED", "errors raise, comments survive, writes are atomic")
elif raised == 2:
    verdict("PARTLY FIXED", "fetchData raises; setConfig still drops comments / re-sorts keys"
            + (" and a failed write empties the file" if non_atomic else ""))
else:
    verdict("STILL PRESENT", "fetchData still turns errors into None")
