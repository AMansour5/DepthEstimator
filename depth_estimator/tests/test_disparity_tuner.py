from depth_estimator.tuners.DisparityTuner import DisparityTuner

def test_run():
    tuner = DisparityTuner()
    tuner.tuneDisparity()
