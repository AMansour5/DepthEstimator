"""P12: a non-editable install (pip install .) does not work: config/ is not shipped and ultralytics is not declared.

Offline and static: nothing is built or downloaded.
Part A: which top-level folders does the setuptools configuration ship?
Part B: what does Configurator.getProjectRoot() do when only src/ exists (the site-packages layout)?
Part C: third-party imports in src/ vs the declared dependencies.
"""
import ast, shutil, subprocess, sys, tempfile
from common import *

try:
    import tomllib
except ImportError:
    print("needs Python 3.11+ (tomllib)"); sys.exit(0)

pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
st = pyproject.get("tool", {}).get("setuptools", {})

print("A) what pyproject.toml ships")
print("   packages.find:", st.get("packages", {}).get("find"))
print("   package-data / data-files / include-package-data:", {k: st.get(k) for k in ("package-data", "data-files", "include-package-data")})
ships_config = any(k in st for k in ("package-data", "data-files")) or (ROOT / "MANIFEST.in").exists()
print("   -> config/*.yaml shipped:", ships_config, "| top-level package installed under the generic name 'src'")

print("\nB) Configurator.getProjectRoot() when only src/ is present (what site-packages looks like)")
broken = False
with tempfile.TemporaryDirectory() as tmp:
    shutil.copytree(ROOT / "src", f"{tmp}/site-packages/src",
                    ignore=shutil.ignore_patterns("tests", "images", "models", "matrices", "__pycache__"))
    r = subprocess.run([sys.executable, "-c",
                        "from src.utils.Configurator import Configurator; print(Configurator.getProjectRoot())"],
                       cwd=f"{tmp}/site-packages", capture_output=True, text=True)
    broken = r.returncode != 0
    print("   ", (r.stderr.strip().splitlines() or ["OK " + r.stdout.strip()])[-1])

print("\nC) third-party imports in src/ (excluding tests) vs [project].dependencies")
declared = {d.split(">")[0].split("<")[0].split("=")[0].strip().lower().replace("_", "-") for d in pyproject["project"]["dependencies"]}
dist = {"cv2": "opencv-python", "yaml": "pyyaml", "zope": "zope.interface"}
imported = set()
for f in (ROOT / "src").rglob("*.py"):
    if "tests" in f.parts:
        continue
    for node in ast.walk(ast.parse(f.read_text())):
        mods = [node.module] if isinstance(node, ast.ImportFrom) and node.module else \
               [a.name for a in node.names] if isinstance(node, ast.Import) else []
        imported |= {m.split(".")[0] for m in mods}
third = sorted(m for m in imported if m not in sys.stdlib_module_names and m != "src")
missing = [dist.get(m, m) for m in third if dist.get(m, m).lower() not in declared]
print("   imported:", third)
print("   declared:", sorted(declared))
print("   imported but not declared:", missing or "none")

verdict("STILL PRESENT" if (broken or missing) else "FIXED",
        f"config/ is not installed (getProjectRoot {'raises' if broken else 'works'}); undeclared imports: {missing or 'none'}")
