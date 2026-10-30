"""P04: a detector that failed to load looks exactly like a scene with nothing in it."""
import sys, types
from common import *

# Offline stand-in for ultralytics whose model load fails (e.g. wrong model_path).
stub = types.ModuleType("ultralytics")
def YOLO(path): raise FileNotFoundError(f"{path} not found")
stub.YOLO = YOLO
sys.modules["ultralytics"] = stub

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

print("1) construct ObjectDetector with a model that fails to load")
det = ObjectDetector(dict(model_path="src/models/yolov8n.pt", device=None))
print("   constructor returned normally; has .model?", hasattr(det, "model"))
frame = np.zeros((1080, 1920, 3), np.uint8)
print("\n2) detect() on a frame")
print("   returned:", repr(det.detect(frame)), "  (an empty scene returns [] - callers can't tell them apart)")
print("\n3) Orchestrator.processFrame, 3 frames")
orch = Orchestrator(camera=FakeCamera(), processor=FakeProcessor(), detector=det)
for i in range(3):
    r = orch.processFrame(frame, frame)
    print(f"   frame {i}: detections={r['detections']} depths={r['depths']}")
orch.close()
