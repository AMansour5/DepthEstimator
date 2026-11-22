class YoloModelNotFound(Exception):
    """Raised when the YOLO model file is not found."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)