"""P06: are the tests meaningful now? They are discoverable and can fail, but hardware/GUI tests run by default.

Part A: what pytest collects, and how each test file is classified from its source.
Part B: a test with a deliberately different (but valid) config: does it fail, and why?
Part C: which problems have a regression test.
Part D: which tests pass in a clean clone (tracked files only).
"""
import re, subprocess, sys
from pathlib import Path
from common import *

print("A) pytest --collect-only")
out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "src/tests"],
                     cwd=ROOT, capture_output=True, text=True).stdout
ids = [l for l in out.splitlines() if "::" in l]
print(f"   {len(ids)} tests collected from {len({i.split('::')[0] for i in ids})} files")

print("\n   per-file classification (static scan of the test source):")
print(f"   {'file':<28}{'tests':>6}  swallows asserts | abs. /home path | GUI (imshow/waitKey) | real camera | real model/calib")
flagged_files = 0
for f in sorted((ROOT / "src/tests").glob("test_*.py")):
    text = f.read_text()
    n = len(re.findall(r"^def test_", text, re.M))
    swallow = bool(re.search(r"except\s+(Exception|AssertionError)", text))
    abs_path = "/home/" in text
    gui = "imshow" in text or "waitKey" in text or "tuneDisparity" in text
    camera = bool(re.search(r"StereoCamera\(\s*\w*cfg|stereo_camera_cfg", text)) or "tuneDisparity" in text
    real = bool(re.search(r"fetchData\(\s*configurator\.(OBJECT|STEREO_PROCESSOR)", text))
    flagged_files += bool(abs_path or gui or camera or real)
    mark = lambda b: "yes" if b else "-"
    print(f"   {f.name:<28}{n:>6}  {mark(swallow):>15} | {mark(abs_path):>15} | {mark(gui):>20} | {mark(camera):>11} | {mark(real):>15}")
print(f"   -> {flagged_files} of the files need the author's machine, a camera, a display, or real weights/calibration")

print("\nB) test_load_camera_config against another valid config (camera index 0, 1280x480)")
import importlib
from src.utils.Configurator import Configurator
Configurator.fetchData = lambda self, t: dict(camera_index=0, combined_width=1280, combined_height=480, preview_width=640)
mod = importlib.import_module("src.tests.test_configurator")
try:
    mod.test_load_camera_config()
    print("   passed")
except AssertionError:
    print("   AssertionError: the test can fail (good), but it asserts this machine's values, so it fails on any other setup")

print("\nC) regression tests that exist for the documented problems")
names = {f.name: f.read_text() for f in (ROOT / "src/tests").glob("test_*.py")}
checks = {
    "P01 dead band": "test_stereo_dead_band.py",
    "P03 minDisparity sentinel": None,
    "P02 frame size": None,
    "P04 detector errors": None,
    "P09 Configurator": "test_configurator.py",
    "P11 camera latency": "test_stereo_camera.py",
}
patterns = {"P03 minDisparity sentinel": r"minDisparity\"?[=:]\s*[1-9]|\"minDisparity\":\s*[1-9]", "P02 frame size": r"DifferentImageSizeError",
            "P04 detector errors": r"DetectionError|YoloModelNotFound"}
for problem, fname in checks.items():
    if fname:
        found = fname in names
    else:
        found = any(re.search(patterns[problem], t) for t in names.values())
    print(f"   {problem:<28}: {'covered' if found else 'NO regression test'}")

print("\nD) a clean clone: copy what git would contain (tracked and new, not ignored) to a temporary folder and run the tests there")
import shutil, tempfile
tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True).stdout.split()
with tempfile.TemporaryDirectory() as tmp:
    for f in tracked:
        if not (ROOT / f).is_file():
            continue
        (Path(tmp) / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, Path(tmp) / f)

    def run(*args):
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
                           cwd=tmp, capture_output=True, text=True, timeout=300)
        return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:]

    cam = "src/tests/test_stereo_camera.py::test_"
    portable = ["src/tests/test_configurator.py", "src/tests/test_depth_estimator.py", "src/tests/test_stereo_dead_band.py",
                cam + "slow_consumer_gets_latest_frame", cam + "frames_are_not_returned_twice",
                cam + "release_stops_reader_thread", cam + "camera_rejects_negotiated_resolution_mismatch"]
    print("   no camera, display, model or calibration needed :", run(*portable))
    print("   test_stereo_processor.py (needs calibration+images):", run("src/tests/test_stereo_processor.py"))
print("   (camera, GUI and model tests are not run here: they would open a window or block)")

verdict("PARTLY FIXED",
        "tests are named test_*.py, assertions are not swallowed, and 22 tests run on a clean clone; but the other 11 need "
        "the author's calibration/images, a camera, a display or the model, and the P03/P04 fixes have no regression test")
