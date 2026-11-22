"""P13: legacy calibration metadata is optional and T's unit is explicit in the current schema."""
import tempfile
import warnings
from common import *
from depth_estimator.services.StereoProcessor import StereoProcessor

cfg = load_stereo_processor_cfg()


def load(path):
    return StereoProcessor(dict(cfg, calibration_path=path))


with tempfile.TemporaryDirectory() as tmp:
    print("A) loading calibration files")
    new, old, unknown = f"{tmp}/new.npz", f"{tmp}/old.npz", f"{tmp}/unknown.npz"
    synthetic_calibration(new)
    with np.load(new) as data:
        keys = {k: data[k] for k in data.files
                if k not in ("square_size_mm", "checkerboard", "translation_unit")}
    np.savez(old, **keys)
    synthetic_calibration(unknown, translation_unit="cm")
    marked = load(new)
    print(f"   current schema with translation_unit=mm: loads, baseline={marked.getBaseline():.1f} mm")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        legacy = load(old)
    legacy_warned = any("assuming legacy translations are in millimetres" in str(w.message) for w in caught)
    print(f"   original schema (without metadata)     : loads with assumed-mm warning={legacy_warned}")
    try:
        load(unknown)
        unsupported_rejected = False
    except RuntimeError as e:
        unsupported_rejected = "Unsupported translation_unit 'cm'" in str(e)
        print(f"   translation_unit=cm                    : rejected clearly={unsupported_rejected}")

    print("\nB) does square_size_mm rescale T? (same T, different descriptive metadata)")
    baselines = {}
    for size in (30.0, 3.0):
        p = f"{tmp}/size{size}.npz"
        synthetic_calibration(p, baseline=60.0, square_size_mm=size)
        baselines[size] = load(p).getBaseline()
        print(f"   square_size_mm={size:>5}: getBaseline() = {baselines[size]:.1f}")
    same_t_same_baseline = baselines[30.0] == baselines[3.0]
    print(f"   same T yields same baseline (expected): {same_t_same_baseline}")

if legacy_warned and legacy.translation_unit == "mm" and marked.translation_unit == "mm" and unsupported_rejected and same_t_same_baseline:
    verdict("FIXED", "legacy metadata is optional; new files declare T in mm; unsupported units are rejected")
else:
    verdict("STILL PRESENT", "the calibration schema or unit contract did not behave as expected")
