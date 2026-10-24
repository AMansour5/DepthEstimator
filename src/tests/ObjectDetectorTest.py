import cv2
from src.utils.Configurator import Configurator
from src.services.ObjectDetector import ObjectDetector

class ObjectDetectorTest:
    def __init__(self):
        self.configurator = Configurator()
        self.object_detector_cfg = self.configurator.fetchData(self.configurator.OBJECT_DETECTOR)
        self.object_detector = None

    def test_load_model(self):
        try:
            self.object_detector = ObjectDetector(self.object_detector_cfg)
        except Exception as e:
            print(f"Failed to load model: {e}")

    def test_detect_objects(self):
        try:
            if self.object_detector is None:
                self.object_detector = ObjectDetector(self.object_detector_cfg)
            # Replace 'sample_image' with an actual image for testing
            sample_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/porsche.png")  # Replace with the path to an actual image for testing
            detected_objects = self.object_detector.detect(sample_image)
            print(f"Detected objects: {detected_objects}")
            self.__draw_and_show(sample_image, detected_objects)
        except Exception as e:
            print(f"Failed to detect objects: {e}")

    def __draw_and_show(self, image, detected_objects):
        if image is None or not detected_objects:
            return
        annotated = image.copy()
        for obj in detected_objects:
            x1, y1, x2, y2 = (int(coord) for coord in obj["box"])
            label = f"{obj['name']} {obj['conf']:.2f}"
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - text_h - baseline), (x1 + text_w, y1), (0, 255, 0), -1)
            cv2.putText(annotated, label, (x1, y1 - baseline), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        cv2.imshow("Detected Objects", annotated)
        while True:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # Stop looping if the window is closed via the 'X' button.
            if cv2.getWindowProperty("Detected Objects", cv2.WND_PROP_VISIBLE) < 1:
                break
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test = ObjectDetectorTest()
    test.test_load_model()
    test.test_detect_objects()