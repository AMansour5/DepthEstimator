import os
import pathlib
import shutil
from importlib.resources import files

import yaml


class Configurator:
    STEREO_CAMERA = "stereo_camera"
    OBJECT_DETECTOR = "object_detector"
    STEREO_PROCESSOR = "stereo_processor"
    DEPTH_ESTIMATOR = "depth_estimator"

    def __init__(self):
        self.__configFile = ""

    @staticmethod
    def getProjectRoot():
        return str(pathlib.Path(__file__).resolve().parents[1])

    @staticmethod
    def getConfigDir():
        override = os.environ.get("DEPTH_ESTIMATOR_CONFIG_DIR")
        if override:
            return pathlib.Path(override).expanduser()

        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        config_home = pathlib.Path(xdg_config_home).expanduser() if xdg_config_home else pathlib.Path.home() / ".config"
        return config_home / "depth-estimator"

    @staticmethod
    def resolvePath(path):
        if not path:
            return path
        artifact_path = pathlib.Path(path).expanduser()
        if artifact_path.is_absolute():
            return str(artifact_path)
        return str(pathlib.Path(Configurator.getProjectRoot()) / artifact_path)

    def __ensureMutableConfigDir(self):
        config_dir = Configurator.getConfigDir()
        config_dir.mkdir(parents=True, exist_ok=True)
        packaged = files("depth_estimator.config")
        for name in (
            f"{Configurator.STEREO_CAMERA}.yaml",
            f"{Configurator.OBJECT_DETECTOR}.yaml",
            f"{Configurator.STEREO_PROCESSOR}.yaml",
            f"{Configurator.DEPTH_ESTIMATOR}.yaml",
        ):
            destination = config_dir / name
            if not destination.exists():
                source = packaged.joinpath(name)
                with source.open("rb") as src, destination.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        return config_dir

    def __raiseTypeError(self, data_type):
        consts = [
            attr
            for attr in dir(self)
            if not callable(getattr(self, attr)) and not attr.startswith("_")
        ]
        raise TypeError(
            f"Config file of type {data_type} doesn't exist, only {', '.join(consts)} are allowed."
        )

    def __validateType(self, data_type):
        supported_types = (
            Configurator.STEREO_CAMERA,
            Configurator.OBJECT_DETECTOR,
            Configurator.STEREO_PROCESSOR,
            Configurator.DEPTH_ESTIMATOR,
        )
        if data_type not in supported_types:
            self.__raiseTypeError(data_type)

    def fetchData(self, data_type):
        try:
            self.__validateType(data_type)
            config_dir = Configurator.getConfigDir()
            mutable_file = config_dir / f"{data_type}.yaml"
            if mutable_file.exists():
                self.__configFile = str(mutable_file)
                with open(mutable_file, "r") as file:
                    return yaml.safe_load(file)

            packaged = files("depth_estimator.config").joinpath(f"{data_type}.yaml")
            self.__configFile = str(packaged)
            with packaged.open("r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: The file '{self.__configFile}' was not found.")
        except yaml.YAMLError:
            raise RuntimeError("Error: Failed to parse the YAML file.")
        except TypeError as e:
            raise TypeError(f"Error: {e}")

    def setConfig(self, data_type, new_data):
        try:
            self.__validateType(data_type)
            config_dir = self.__ensureMutableConfigDir()
            self.__configFile = str(config_dir / f"{data_type}.yaml")

            try:
                with open(self.__configFile, "r") as file:
                    existing_data = yaml.safe_load(file) or {}
            except FileNotFoundError:
                existing_data = {}
                print(f"Warning: {self.__configFile} not found. A new file will be created.")

            updated_data = {**existing_data, **new_data}
            with open(self.__configFile, "w") as file:
                yaml.safe_dump(updated_data, file, default_flow_style=False)

            print(f"Configuration for '{data_type}' updated successfully.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: The directory for '{self.__configFile}' was not found.")
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error: Failed to write YAML data. Details: {e}")
        except TypeError as e:
            raise TypeError(f"Error: {e}")
