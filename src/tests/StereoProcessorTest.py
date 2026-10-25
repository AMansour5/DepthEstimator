import cv2
from src.utils.Configurator import Configurator
from src.services.StereoProcessor import StereoProcessor

class StereoProcessorTest:
    def __init__(self):
        self.configurator = Configurator()
        self.processor_cfg = self.configurator.fetchData(self.configurator.STEREO_PROCESSOR)
        self.stereo_processor = None

    def testInitialize(self):
        try:
            self.stereo_processor = StereoProcessor(self.processor_cfg)
            assert self.stereo_processor is not None
        except Exception as e:
            print(f"Initialization failed: {e}")

    def testRectify(self):
        try:
            assert self.stereo_processor is not None
            # Assuming rectify takes left and right images as input
            left_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/left/000.png")  # Replace with actual test image
            right_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/right/000.png")  # Replace with actual test image
            rectified_left, rectified_right = self.stereo_processor.rectifyImages(left_image, right_image)

            assert rectified_left is not None and rectified_right is not None
        except Exception as e:
            print(f"Rectification failed: {e}")

    def testGetFocalLength(self):
        try:
            assert self.stereo_processor is not None
            focal_length = self.stereo_processor.getFocalLength()
            print(f"Focal length: {focal_length} cm")
            assert focal_length is not None
        except Exception as e:
            print(f"Getting focal length failed: {e}")

    def testGetBaseline(self):
        try:
            assert self.stereo_processor is not None
            baseline = self.stereo_processor.getBaseline()
            print(f"Baseline: {baseline}")
            assert baseline is not None
        except Exception as e:
            print(f"Getting baseline failed: {e} px")

    def testcomputeDisparity(self):
        try:
            assert self.stereo_processor is not None
            left_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/left/000.png")  # Replace with actual test image
            right_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/right/000.png")  # Replace with actual test image
            disparity = self.stereo_processor.computeDisparity(left_image, right_image)
            print(f"Disparity: {disparity}")
            assert disparity is not None
        except Exception as e:
            print(f"Computing disparity failed: {e}")

if __name__ == "__main__":
    test = StereoProcessorTest()
    test.testInitialize()
    test.testRectify()
    test.testGetFocalLength()
    test.testGetBaseline()
    test.testcomputeDisparity()

