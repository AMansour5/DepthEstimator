import cv2
import time
import numpy as np
from src.utils.Configurator import Configurator
from concurrent.futures import ThreadPoolExecutor
from src.services.StereoCamera import StereoCamera
from src.services.ObjectDetector import ObjectDetector
from src.services.DepthEstimator import DepthEstimator
from src.services.StereoProcessor import StereoProcessor


class Orchestrator:
    """Runs the whole pipeline, one frame at a time (fork-join):

        camera -> rectify -> +-> detect (YOLO, main thread)  -+-> depth -> draw
                             +-> disparity (SGBM, worker)    -+

    Detection and disparity both need only the rectified pair, so they run
    concurrently. Both results are joined before depth is computed, so a box
    and a disparity map always come from the same frame. Frame time is about
    max(yolo, sgbm) instead of their sum when YOLO runs on a GPU and SGBM on
    the CPU.

    Components are built from config/*.yaml by default; pass your own to
    override any of them (handy for tests).
    """

    WINDOW_NAME = "object depth: left + boxes | disparity"
    DISPLAY_WIDTH = 720     # width of each of the two display panels

    def __init__(self, camera=None, processor=None, detector=None, depth_estimator=None):
        self.configurator = Configurator()
        self.camera = camera if camera is not None else StereoCamera(
            self.__fetch(Configurator.STEREO_CAMERA))
        self.processor = processor if processor is not None else StereoProcessor(
            self.__fetch(Configurator.STEREO_PROCESSOR))
        self.detector = detector if detector is not None else ObjectDetector(
            self.__fetch(Configurator.OBJECT_DETECTOR))
        self.depth_estimator = depth_estimator if depth_estimator is not None else DepthEstimator(
            self.__fetch(Configurator.DEPTH_ESTIMATOR),
            focal_length=self.processor.getFocalLength(),
            baseline=self.processor.getBaseline(),
            scale=self.processor.process_scale,
        )
        self.num_disparities = self.processor.matcher_params["numDisparities"]
        # One worker is enough: only SGBM goes to it, YOLO runs on the main thread.
        self.pool = ThreadPoolExecutor(max_workers=1)

    def __fetch(self, config_type):
        cfg = self.configurator.fetchData(config_type)
        if cfg is None:
            raise RuntimeError(f"Could not load the '{config_type}' config.")
        return cfg

    # ------------------------------------------------------------------ #
    # One frame
    # ------------------------------------------------------------------ #
    def __timedDisparity(self, rect_left, rect_right):
        # The timer lives INSIDE the worker so it measures SGBM's real cost,
        # not how long the main thread waited for it.
        t0 = time.perf_counter()
        disparity = self.processor.computeDisparity(rect_left, rect_right)
        return disparity, (time.perf_counter() - t0) * 1000.0

    def processFrame(self, left_frame, right_frame):
        """Run the pipeline on one raw stereo pair (no drawing, no GUI)."""
        rect_left, rect_right = self.processor.rectifyImages(left_frame, right_frame)

        future = self.pool.submit(self.__timedDisparity, rect_left, rect_right)  # SGBM in background
        t0 = time.perf_counter()
        detections = self.detector.detect(rect_left) or []   # YOLO meanwhile (None on error -> [])
        yolo_ms = (time.perf_counter() - t0) * 1000.0
        disparity, sgbm_ms = future.result()                  # join: re-raises worker exceptions

        depths = self.depth_estimator.estimateDepths(disparity, detections)
        return dict(
            rect_left=rect_left, disparity=disparity,
            detections=detections, depths=depths,
            yolo_ms=yolo_ms, sgbm_ms=sgbm_ms,
        )

    # ------------------------------------------------------------------ #
    # Drawing (always on copies, after depth is computed)
    # ------------------------------------------------------------------ #
    @staticmethod
    def __drawText(img, text, org, scale=0.5):
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3)
        cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1)

    def __colorizeDisparity(self, disparity):
        valid = disparity > 0
        vis = np.zeros(disparity.shape, dtype=np.uint8)
        if np.any(valid):
            vis[valid] = np.clip(disparity[valid] * 255.0 / self.num_disparities, 0, 255).astype(np.uint8)
        colored = cv2.applyColorMap(vis, cv2.COLORMAP_TURBO)
        colored[~valid] = (0, 0, 0)
        return colored

    def __render(self, result, fps):
        """Left: rectified image with boxes + labels. Right: disparity with the
        same boxes, so a missing depth shows up as a hole under the box.

        green  = depth looks reliable
        orange = computed but suspicious (few valid pixels or wide spread), '?'
        red    = no usable disparity in the sampled region
        """
        rect_left = result["rect_left"]
        ds = self.DISPLAY_WIDTH / rect_left.shape[1]
        left = cv2.resize(rect_left, None, fx=ds, fy=ds)    # resize returns a new array
        disp_vis = cv2.resize(
            self.__colorizeDisparity(result["disparity"]),
            (left.shape[1], left.shape[0]), interpolation=cv2.INTER_NEAREST,
        )

        for det, dep in zip(result["detections"], result["depths"]):
            x1, y1, x2, y2 = [int(v * ds) for v in det["box"]]
            if dep is None:
                color = (0, 0, 255)
                label = f"{det['name']} {det['conf']:.2f} | no depth"
            else:
                color = (0, 200, 0) if dep["reliable"] else (0, 165, 255)
                flag = "" if dep["reliable"] else " ?"
                label = f"{det['name']} {det['conf']:.2f} | {dep['z_mm'] / 1000:.2f} m{flag}"
                rx1, ry1, rx2, ry2 = [int(v * ds) for v in dep["roi"]]
                cv2.rectangle(left, (rx1, ry1), (rx2, ry2), color, 1)   # the region actually sampled
            cv2.rectangle(left, (x1, y1), (x2, y2), color, 2)
            cv2.rectangle(disp_vis, (x1, y1), (x2, y2), color, 2)
            self.__drawText(left, label, (x1, max(15, y1 - 6)))

        display = cv2.hconcat([left, disp_vis])
        cv2.putText(display,
                    f"YOLO {result['yolo_ms']:.0f} ms | SGBM {result['sgbm_ms']:.0f} ms | {fps:.1f} FPS",
                    (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return display

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #
    def run(self):
        """Live demo. Press 'q' in the window (or Ctrl+C) to quit."""
        self.camera.open()
        if self.camera.getCapture() is None:
            raise RuntimeError("Could not open the stereo camera.")

        fps = 0.0
        prev = time.perf_counter()
        try:
            while True:
                left_frame, right_frame = self.camera.getFrames()
                if left_frame is None or right_frame is None:
                    print("No frame from the camera, stopping.")
                    break

                result = self.processFrame(left_frame, right_frame)

                now = time.perf_counter()
                fps = 0.9 * fps + 0.1 / (now - prev) if fps > 0 else 1.0 / (now - prev)
                prev = now

                cv2.imshow(self.WINDOW_NAME, self.__render(result, fps))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        except KeyboardInterrupt:
            print("Exiting depth estimation loop.")
        finally:
            self.close()

    def close(self):
        self.pool.shutdown(wait=True)
        self.camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    Orchestrator().run()