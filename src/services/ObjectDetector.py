from ultralytics import YOLO

class ObjectDetector:
    def __init__(self, detector_cfg):
        self.model_path = detector_cfg.get("model_path")
        self.conf_threshold = detector_cfg.get("conf_threshold", 0.5)
        self.classes = detector_cfg.get("classes", None)
        self.device = detector_cfg.get("device", None)
        self.yolo_imgsz = detector_cfg.get("yolo_imgsz", 640)
        try:
            self.model = YOLO(self.model_path)
        except Exception as e:
            print(f"Error: Failed to load YOLO model from '{self.model_path}'. Details: {e}")

    def detect(self, image):
        """
        Perform object detection on the given image using the YOLO model.

        :param image: Input image for object detection.
        :return: Detection results.
        """
        try:
            results = self.model(
                image, imgsz=self.yolo_imgsz, conf=self.conf_threshold, classes=self.classes,
                device=self.device, verbose=False,
                )[0]
            boxes = results.boxes
            if boxes is None or len(boxes) == 0:
                return []
            xyxy = boxes.xyxy.cpu().numpy()
            conf = boxes.conf.cpu().numpy()
            cls = boxes.cls.cpu().numpy().astype(int)
            return [
                dict(box=xyxy[i].tolist(), conf=float(conf[i]), cls=int(cls[i]),
                     name=str(results.names[int(cls[i])]))
                for i in range(len(xyxy))
            ]
        except Exception as e:
            print(f"Error: Failed to perform object detection. Details: {e}")
            return None