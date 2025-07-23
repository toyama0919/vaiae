import yaml
from tabulate import tabulate
from typing import Dict, Any
import os
import importlib


class Util:
    @staticmethod
    def convert():
        pass

    @staticmethod
    def load_yaml_config(file_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            file_path (str): Path to the YAML configuration file.

        Returns:
            Dict[str, Any]: Configuration dictionary loaded from YAML.

        Raises:
            FileNotFoundError: If the YAML file doesn't exist.
            yaml.YAMLError: If the YAML file is malformed.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                config = yaml.safe_load(file)
                return config if config is not None else {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {e}")

    @staticmethod
    def import_from_string(import_path: str):
        """Import an object from a string path.

        Args:
            import_path (str): String path to the object (e.g., 'module.submodule.ClassName')

        Returns:
            The imported object

        Raises:
            ImportError: If the module or object cannot be imported
            AttributeError: If the object doesn't exist in the module
        """
        try:
            # Split the path into module and object name
            module_path, object_name = import_path.rsplit('.', 1)

            # Import the module
            module = importlib.import_module(module_path)

            # Get the object from the module
            obj = getattr(module, object_name)

            return obj
        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"Cannot import '{import_path}': {e}")
