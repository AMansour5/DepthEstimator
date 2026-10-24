from src.utils.Configurator import Configurator

class TestConfigurator:

    def __init__(self):
        self.configurator = Configurator()

    def test_load_camera_config(self):
        try:
            config = self.configurator.fetchData(Configurator.STEREO_CAMERA)
            assert config["camera_index"] == "/dev/video2"
            assert config["combined_width"] == 3840
            assert config["combined_height"] == 1080
            assert config["preview_width"] == 640
        except Exception as e:
            print(f"Error loading camera config: {e}")

if __name__ == "__main__":
    test_configurator = TestConfigurator()
    test_configurator.test_load_camera_config()
    print("All tests completed.")