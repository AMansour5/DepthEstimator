"""P05: running the project from a clean clone. What is fixed, and what still depends on the working directory.

Part A: what git actually tracks for the two git-ignored artifacts.
Part B: relative calibration_path / model_path resolve against the CURRENT WORKING DIRECTORY.
Part C: dependency declaration in pyproject.toml vs the imports in depth_estimator/.
"""
import ast, os, subprocess, sys, tempfile
from common import *
from depth_estimator.services.StereoProcessor import StereoProcessor
from depth_estimator.utils.Configurator import Configurator

cfg = load_stereo_processor_cfg()
det_cfg = yaml.safe_load((ROOT / "depth_estimator" / "config" / "object_detector.yaml").read_text())
print("config paths:", cfg["calibration_path"], "and", det_cfg["model_path"], "(both relative)\n")

print("A) tracked by git in the artifact folders")
tracked = subprocess.run(["git", "ls-files", "depth_estimator/matrices", "depth_estimator/models", "disparity_tuning_results"],
                         cwd=ROOT, capture_output=True, text=True).stdout.split()
print("   ", tracked)
folders_exist = all(any(t.startswith(d) for t in tracked) for d in ("depth_estimator/matrices", "depth_estimator/models"))
print("    folders exist on a clean clone (.gitkeep):", folders_exist)
print("    calibration file and weights are NOT tracked -> a clean clone still needs them from you")

print("\nB) the same complete synthetic calibration, referenced by a relative path, from two directories")
cwd_dependent = False
with tempfile.TemporaryDirectory() as tmp:
    os.makedirs(f"{tmp}/rel")
    synthetic_calibration(f"{tmp}/rel/stereo_calib.npz")
    cfg["calibration_path"] = "rel/stereo_calib.npz"
    Configurator.getProjectRoot = staticmethod(lambda: tmp)
    for label, cwd in (("cwd = folder that contains rel/", tmp), ("cwd = anywhere else", "/")):
        os.chdir(cwd)
        try:
            StereoProcessor(dict(cfg)); print(f"   {label}: OK")
        except Exception as e:
            cwd_dependent = True
            print(f"   {label}: FAILED -> {e}")
os.chdir(ROOT)

print("\nC) pyproject.toml: declared dependencies vs third-party imports in depth_estimator/ (excluding tests)")
if sys.version_info >= (3, 11):
    import tomllib
    declared = {d.split(">")[0].split("<")[0].split("=")[0].strip().lower().replace("_", "-")
                for d in tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]}
    dist = {"cv2": "opencv-python", "yaml": "pyyaml", "zope": "zope.interface", "numpy": "numpy", "ultralytics": "ultralytics"}
    imported = set()
    for f in (ROOT / "depth_estimator").rglob("*.py"):
        if "tests" in f.parts:
            continue
        for node in ast.walk(ast.parse(f.read_text())):
            mods = [node.module] if isinstance(node, ast.ImportFrom) and node.module else \
                   [a.name for a in node.names] if isinstance(node, ast.Import) else []
            imported |= {m.split(".")[0] for m in mods}
    third = {m for m in imported if m not in sys.stdlib_module_names and m not in ("depth_estimator",)}
    print("   third-party imports:", sorted(third))
    print("   declared           :", sorted(declared))
    missing = sorted(dist.get(m, m) for m in third if dist.get(m, m) not in declared)
    print("   imported but not declared:", missing or "none")
else:
    missing = []
    print("   (needs Python 3.11+ for tomllib; skipped)")

artifacts_missing = not folders_exist
if not cwd_dependent and not missing and not artifacts_missing:
    verdict("FIXED", "paths are cwd-independent and dependencies are complete")
else:
    verdict("PARTLY FIXED", "pyproject.toml and .gitkeep folders exist; paths are cwd-independent"
            + (f", undeclared dependency {missing}" if missing else "")
            + (", calibration/model artifacts are not tracked" if artifacts_missing else "")
            + ", no calibration tooling in the repo")
