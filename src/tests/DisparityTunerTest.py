from src.tuners.DisparityTuner import DisparityTuner

class TestDisparityTuner:
    def __init__(self):
        self.tuner = DisparityTuner()

    def test_run(self):
        try:
            self.tuner.tuneDisparity()
        except Exception as e:
            print(f"Error during tuning: {e}")

if __name__ == "__main__":
    test = TestDisparityTuner()
    test.test_run()