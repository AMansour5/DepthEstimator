import cv2
from src.utils.Configurator import Configurator
from src.services.ObjectDetector import ObjectDetector

def test_load_model():
    configurator = Configurator()
    object_detector_cfg = configurator.fetchData(configurator.OBJECT_DETECTOR)
    object_detector = ObjectDetector(object_detector_cfg)
    assert object_detector is not None

def test_detect_objects():
    configurator = Configurator()
    object_detector_cfg = configurator.fetchData(configurator.OBJECT_DETECTOR)
    object_detector = ObjectDetector(object_detector_cfg)
    # Replace 'sample_image' with an actual image for testing
    sample_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/porsche.png")  # Replace with the path to an actual image for testing
    detected_objects = object_detector.detect(sample_image)
    print(f"Detected objects: {detected_objects}")
    __draw_and_show(sample_image, detected_objects)
    assert detected_objects is not None

def __draw_and_show(image, detected_objects):
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