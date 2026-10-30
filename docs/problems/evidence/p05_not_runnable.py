"""P05: a clean clone cannot run (artifacts are git-ignored), and paths depend on the working directory."""
import os, tempfile
from common import *
from src.services.StereoProcessor import StereoProcessor

cfg = load_stereo_processor_cfg()
print("config paths:", cfg["calibration_path"], "(relative)")
print("tracked in git?  models/*.pt and matrices/*.npz are covered by .gitignore (*.pt, *.npz)\n")

print("A) fresh clone: is there a calibration file?")
exists = (ROOT / cfg["calibration_path"]).exists()
print("  ", (ROOT / cfg["calibration_path"]), "->", "present" if exists else "MISSING")

print("\nB) same calibration file, same code, different working directory")
with tempfile.TemporaryDirectory() as tmp:
    os.makedirs(f"{tmp}/rel")
    synthetic_calibration(f"{tmp}/rel/stereo_calib.npz")
    cfg["calibration_path"] = "rel/stereo_calib.npz"          # relative, like the real config
    for label, cwd in (("cwd = folder that contains rel/", tmp), ("cwd = anywhere else", "/")):
        os.chdir(cwd)
        try:
            StereoProcessor(cfg); print(f"   {label}: OK")
        except Exception as e:
            print(f"   {label}: FAILED -> {e}")
