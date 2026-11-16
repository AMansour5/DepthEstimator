"""P13: the calibration loader requires two keys that nothing uses, and the unit they describe is still assumed.

StereoProcessor.__loadCalibration reads `square_size_mm` and `checkerboard` (added after the original schema), stores them
and never uses them again. Consequences checked here:
  A) a calibration file made before they existed no longer loads,
  B) the stored unit does not influence the baseline, so a file made with squares entered in cm still reads as mm (P08),
  C) nothing else in src/ reads the two attributes.
"""
import re, tempfile
from common import *
from src.services.StereoProcessor import StereoProcessor

cfg = load_stereo_processor_cfg()


def load(path):
    return StereoProcessor(dict(cfg, calibration_path=path))


with tempfile.TemporaryDirectory() as tmp:
    print("A) loading calibration files")
    new, old = f"{tmp}/new.npz", f"{tmp}/old.npz"
    synthetic_calibration(new)
    keys = {k: np.load(new)[k] for k in np.load(new).files if k not in ("square_size_mm", "checkerboard")}
    np.savez(old, **keys)
    rejected = False
    for label, path in (("with square_size_mm + checkerboard", new), ("original schema (without them)", old)):
        try:
            load(path)
            print(f"   {label:<38}: loads")
        except RuntimeError as e:
            rejected = True
            print(f"   {label:<38}: RuntimeError: {e}")

    print("\nB) does the stored unit change the baseline? (same translation T, different square_size_mm)")
    baselines = {}
    for size in (30.0, 3.0):
        p = f"{tmp}/size{size}.npz"
        synthetic_calibration(p, baseline=60.0, square_size_mm=size)
        baselines[size] = load(p).getBaseline()
        print(f"   square_size_mm={size:>5}: getBaseline() = {baselines[size]:.1f}")
    unit_ignored = baselines[30.0] == baselines[3.0]

print("\nC) uses of the two attributes in src/ (outside tests)")
uses = []
for f in (ROOT / "src").rglob("*.py"):
    if "tests" in f.parts:
        continue
    for i, line in enumerate(f.read_text().splitlines(), 1):
        if re.search(r"square_size_mm|checkerboard_dims|\[\"checkerboard\"\]", line):
            uses.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()}")
print("   " + "\n   ".join(uses))
only_assigned = all(re.match(r"self\.\w+ = ", u.split(": ", 1)[1]) for u in uses)

if rejected or unit_ignored or only_assigned:
    verdict("STILL PRESENT",
            f"old calibration files are rejected: {rejected}; stored unit ignored by getBaseline: {unit_ignored}; "
            f"keys only assigned, never read: {only_assigned}")
else:
    verdict("FIXED", "optional keys, and the unit is applied")
