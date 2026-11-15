class DetectionError(Exception):
    """Raised when an error occurs during object detection."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)