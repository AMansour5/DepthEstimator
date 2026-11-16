"""P04: a broken detector used to look like an empty scene. It now fails loudly (fail-fast).

Offline: ultralytics is replaced by a stub, so no weights or GPU are needed.
Part A: a model that fails to load.   Part B: a model that raises on every frame (e.g. CUDA out of memory).
Part C: what the Orchestrator does with that failure.   Part D: leftovers in the source.
"""
import sys, types
from common import *

stub = types.ModuleType("ultralytics")
state = {"load_fails": True}


class RaisingModel:
    def __call__(self, *a, **k):
        raise RuntimeError("CUDA out of memory (simulated)")


def YOLO(path):
    if state["load_fails"]:
        raise FileNotFoundError(f"{path} not found")
    return RaisingModel()


stub.YOLO = YOLO
sys.modules["ultralytics"] = stub

from src.exceptions.DetectionError import DetectionError
from src.exceptions.YoloModelNotFound import YoloModelNotFound
from src.services.ObjectDetector import ObjectDetector
from src.services.Orchestrator import Orchestrator


class FakeProcessor:
    process_scale = 0.5; matcher_params = dict(numDisparities=64)
    def getFocalLength(self): return 1000.0
    def getBaseline(self): return 60.0
    def rectifyImages(self, l, r): return l, r
    def computeDisparity(self, l, r): return np.full((540, 960), 40.0, np.float32)


class FakeCamera:
    def open(self): pass
    def getCapture(self): return object()
    def getFrames(self): return None, None
    def release(self): pass


frame = np.zeros((1080, 1920, 3), np.uint8)
cfg = dict(model_path="src/models/yolov8n.pt", device=None)
results = {}

print("A) ObjectDetector with a model that fails to load")
try:
    ObjectDetector(cfg)
    results["load"] = False
    print("   constructor returned normally")
except YoloModelNotFound as e:
    results["load"] = True
    print(f"   raised YoloModelNotFound: {e}")

print("\nB) detect() when the model raises on every frame")
state["load_fails"] = False
det = ObjectDetector(cfg)
try:
    print("   returned:", repr(det.detect(frame)))
    results["detect"] = False
except DetectionError as e:
    results["detect"] = True
    print(f"   raised DetectionError: {e}")

print("\nC) Orchestrator.processFrame with that detector")
orch = Orchestrator(camera=FakeCamera(), processor=FakeProcessor(), detector=det)
try:
    r = orch.processFrame(frame, frame)
    results["orchestrator"] = False
    print(f"   returned detections={r['detections']} depths={r['depths']}")
except DetectionError:
    results["orchestrator"] = True
    print("   DetectionError propagates out of processFrame (run() lets it reach main(), which prints it and exits 1)")
orch.close()

print("\nD) leftovers in the source")
src = (ROOT / "src/services/Orchestrator.py").read_text()
stale = "None on error" in src or "or []" in src.split("def processFrame", 1)[1].split("def __render", 1)[0]
print("   Orchestrator.processFrame still has a stale comment or an `or []` fallback:", stale)
print("   transient errors are not tolerated: one bad frame stops the demo (no 'DETECTOR ERROR' banner, no retry)")

if all(results.values()):
    verdict("FIXED", "load and runtime failures raise; a failed frame stops the demo (fail-fast)" if not stale
            else "load and runtime failures raise, but a stale comment or fallback remains")
else:
    verdict("STILL PRESENT", f"silent paths: {[k for k, v in results.items() if not v]}")
