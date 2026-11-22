"""P12: verify that a regular install packages depth_estimator/config/ and declares all third-party imports.

Offline and static: nothing is built or downloaded.
Part A: which top-level folders does the setuptools configuration ship?
Part B: what does Configurator.getProjectRoot() do when only depth_estimator/ exists (the site-packages layout)?
Part C: third-party imports in depth_estimator/ vs the declared dependencies.
"""
import ast, os, sys, tempfile
from common import *

try:
    import tomllib
except ImportError:
    print("needs Python 3.11+ (tomllib)"); sys.exit(0)

pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
st = pyproject.get("tool", {}).get("setuptools", {})

print("A) what pyproject.toml ships")
print("   packages.find:", st.get("packages", {}).get("find"))
print("   package-data:", st.get("package-data"))
ships_config = (
    "depth_estimator.config" in st.get("package-data", {})
    and all((ROOT / "depth_estimator" / "config" / f"{name}.yaml").is_file()
            for name in ("stereo_camera", "stereo_processor", "object_detector", "depth_estimator"))
)
print("   -> depth_estimator/config/*.yaml packaged:", ships_config,
      "| top-level package: depth_estimator")
print("   -> repository-level config/ duplicate exists:", (ROOT / "config").exists())

print("\nB) Configurator.fetchData() with packaged resources")
broken = False
try:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DEPTH_ESTIMATOR_CONFIG_DIR"] = tmp
        from depth_estimator.utils.Configurator import Configurator
        config = Configurator().fetchData(Configurator.STEREO_CAMERA)
        print("   packaged stereo_camera.yaml loaded:", bool(config))
except Exception as exc:
    broken = True
    print("   ", exc)

print("\nC) third-party imports in depth_estimator/ (excluding tests) vs [project].dependencies")
declared = {d.split(">")[0].split("<")[0].split("=")[0].strip().lower().replace("_", "-") for d in pyproject["project"]["dependencies"]}
dist = {"cv2": "opencv-python", "yaml": "pyyaml", "zope": "zope.interface"}
imported = set()
for f in (ROOT / "depth_estimator").rglob("*.py"):
    if "tests" in f.parts:
        continue
    for node in ast.walk(ast.parse(f.read_text())):
        mods = [node.module] if isinstance(node, ast.ImportFrom) and node.module else \
               [a.name for a in node.names] if isinstance(node, ast.Import) else []
        imported |= {m.split(".")[0] for m in mods}
third = sorted(m for m in imported if m not in sys.stdlib_module_names and m != "depth_estimator")
missing = [dist.get(m, m) for m in third if dist.get(m, m).lower() not in declared]
print("   imported:", third)
print("   declared:", sorted(declared))
print("   imported but not declared:", missing or "none")

verdict("STILL PRESENT" if (broken or missing or not ships_config or (ROOT / "config").exists()) else "FIXED",
        f"depth_estimator/config/*.yaml packaged: {ships_config}; resource loading {'works' if not broken else 'raises'}; "
        f"top-level config duplicate: {(ROOT / 'config').exists()}; undeclared imports: {missing or 'none'}")
