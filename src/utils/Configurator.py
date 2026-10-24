import yaml
import pathlib

class Configurator():
    STEREO_CAMERA = "stereo_camera"
    OBJECT_DETECTOR = "object_detector"
    
    def __init__(self):
        self.__configFile = ''
    
    @staticmethod
    def getProjectRoot():
        # Both markers are required: package dirs may also hold a config/ folder.
        current = pathlib.Path(__file__).resolve()
        for parent in current.parents:
            if (parent / 'config').is_dir() and (parent / 'src').is_dir():
                return str(parent)
        raise FileNotFoundError("Could not find project root with /config and /src directories")

    def __getConfigDir(self):
        project_root = Configurator.getProjectRoot()
        return f"{project_root}/config"
    
    def __raiseTypeError(self,data_type):
        consts = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("_")]
        raise TypeError(f"Config file of type {data_type} doesn't exist, only {', '.join(consts)} are allowed.")

    def __getYamlFile(self, data_type):
        config_dir = self.__getConfigDir()
        supported_types = (
            Configurator.STEREO_CAMERA,
            Configurator.OBJECT_DETECTOR
        )
        if data_type not in supported_types:
            self.__raiseTypeError(data_type)
        self.__configFile = f"{config_dir}/{data_type}.yaml"

    def fetchData(self,data_type):
        try:
            self.__getYamlFile(data_type)
            with open(self.__configFile, 'r') as file:
                data = yaml.safe_load(file)
                return data
        except FileNotFoundError:
            print(f"Error: The file '{self.__configFile}' was not found.")
        except yaml.YAMLError:
            print("Error: Failed to parse the YAML file.")
        except TypeError as e:
            print(e)

    def setConfig(self, data_type, new_data):
        """
        Update the YAML configuration file with new_data.
        Only updates the keys provided in new_data and keeps other keys intact.

        :param data_type: Type of configuration (e.g., "checkerboard", "calibrator")
        :param new_data: Dictionary containing the new key-value pairs to update.
        """
        try:
            self.__getYamlFile(data_type)

            # Load existing data
            try:
                with open(self.__configFile, 'r') as file:
                    existing_data = yaml.safe_load(file) or {}  # Handle empty file case
            except FileNotFoundError:
                existing_data = {}
                print(f"Warning: {self.__configFile} not found. A new file will be created.")

            # Update existing data with new_data (merge dictionaries)
            updated_data = {**existing_data, **new_data}

            # Write back to file
            with open(self.__configFile, 'w') as file:
                yaml.safe_dump(updated_data, file, default_flow_style=False)

            print(f"Configuration for '{data_type}' updated successfully.")

        except FileNotFoundError:
            print(f"Error: The directory for '{self.__configFile}' was not found.")
        except yaml.YAMLError as e:
            print(f"Error: Failed to write YAML data. Details: {e}")
        except TypeError as e:
            print(e)