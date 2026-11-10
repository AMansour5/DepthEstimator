import cv2
from src.utils.Configurator import Configurator
from src.services.StereoProcessor import StereoProcessor

def test_initialize():
    configurator = Configurator()
    processor_cfg = configurator.fetchData(configurator.STEREO_PROCESSOR)
    stereo_processor = StereoProcessor(processor_cfg)
    assert stereo_processor is not None

def test_rectify():
    configurator = Configurator()
    processor_cfg = configurator.fetchData(configurator.STEREO_PROCESSOR)
    stereo_processor = StereoProcessor(processor_cfg)
    # Assuming rectify takes left and right images as input
    left_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/left/000.png")  # Replace with actual test image
    right_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/right/000.png")  # Replace with actual test image
    rectified_left, rectified_right = stereo_processor.rectifyImages(left_image, right_image)
    assert rectified_left is not None and rectified_right is not None

def test_get_focal_length():
    configurator = Configurator()
    processor_cfg = configurator.fetchData(configurator.STEREO_PROCESSOR)
    stereo_processor = StereoProcessor(processor_cfg)
    focal_length = stereo_processor.getFocalLength()
    print(f"Focal length: {focal_length} px")
    assert focal_length is not None

def test_get_baseline():
    configurator = Configurator()
    processor_cfg = configurator.fetchData(configurator.STEREO_PROCESSOR)
    stereo_processor = StereoProcessor(processor_cfg)
    assert stereo_processor is not None
    baseline = stereo_processor.getBaseline()
    print(f"Baseline: {baseline} cm")
    assert baseline is not None

def test_compute_disparity():
    configurator = Configurator()
    processor_cfg = configurator.fetchData(configurator.STEREO_PROCESSOR)
    stereo_processor = StereoProcessor(processor_cfg)
    assert stereo_processor is not None
    left_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/left/000.png")  # Replace with actual test image
    right_image = cv2.imread("/home/mansour/Desktop/DepthEstimator/src/images/right/000.png")  # Replace with actual test image
    disparity = stereo_processor.computeDisparity(left_image, right_image)
    print(f"Disparity: {disparity}")
    assert disparity is not None


