from zope.interface import Interface

class ICamera(Interface):
    """
    Interface for different camera type implementations.
    """

    def open():
        """
        Open the camera for capturing frames.
        """
        pass

    def getFrames():
        """
        Capture a frame from the camera and return it.
        For stereo cameras, this should return a tuple of (left_frame, right_frame).
        """
        pass

    def getCapture():
        """
        Return the underlying cv2.VideoCapture object.
        """
        pass

    def release():
        """
        Release the camera resources.
        """
        pass