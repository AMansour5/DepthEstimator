class DifferentImageSizeError(Exception):
    """Raised when the captured image size does not match the size in the calibration matrix."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)