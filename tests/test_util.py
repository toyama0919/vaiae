import pytest
import os
import tempfile
import yaml
from unittest.mock import patch
from vaiae.util import Util


class TestUtil:
    def setup_method(self, method):
        """Executed before each test method"""
        pass

    def teardown_method(self, method):
        """Executed after each test method"""
        pass

    def test_convert(self):
        """Test convert method (currently does nothing)"""
        # Verify that convert method doesn't raise exceptions
        result = Util.convert()
        assert result is None

    def test_find_config_file_current_directory(self):
        """Test finding config file in current directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temporary file
            config_file = os.path.join(temp_dir, ".agent-engine.yml")
            with open(config_file, "w") as f:
                f.write("test: config")

            # Change current directory to temporary directory
            with patch("os.getcwd", return_value=temp_dir):
                result = Util.find_config_file()
                assert result == config_file

    def test_find_config_file_home_directory(self):
        """Test finding config file in home directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file in home directory
            config_file = os.path.join(temp_dir, ".agent-engine.yml")
            with open(config_file, "w") as f:
                f.write("test: config")

            # Test case when file doesn't exist in current directory but exists in home directory
            with patch("os.getcwd", return_value="/nonexistent"):
                with patch("os.path.expanduser", return_value=temp_dir):
                    result = Util.find_config_file()
                    assert result == config_file

    def test_find_config_file_not_found(self):
        """Test when config file is not found"""
        with patch("os.getcwd", return_value="/nonexistent"):
            with patch("os.path.expanduser", return_value="/nonexistent"):
                with pytest.raises(FileNotFoundError) as exc_info:
                    Util.find_config_file()
                assert "Configuration file '.agent-engine.yml' not found" in str(
                    exc_info.value
                )

    def test_find_config_file_custom_filename(self):
        """Test finding config file with custom filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file with custom filename
            custom_filename = "custom-config.yml"
            config_file = os.path.join(temp_dir, custom_filename)
            with open(config_file, "w") as f:
                f.write("test: config")

            with patch("os.getcwd", return_value=temp_dir):
                result = Util.find_config_file(custom_filename)
                assert result == config_file

    def test_load_yaml_config_success(self):
        """Test successful YAML config file loading"""
        test_config = {
            "default": {"display_name": "test-agent", "description": "Test agent"},
            "production": {
                "display_name": "prod-agent",
                "description": "Production agent",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(test_config, f)
            temp_file = f.name

        try:
            # Load without profile specification
            result = Util.load_yaml_config(temp_file)
            assert result == test_config

            # Load with profile specification
            result_default = Util.load_yaml_config(temp_file, "default")
            assert result_default == test_config["default"]

            result_production = Util.load_yaml_config(temp_file, "production")
            assert result_production == test_config["production"]
        finally:
            os.unlink(temp_file)

    def test_load_yaml_config_file_not_found(self):
        """Test loading non-existent YAML file"""
        with pytest.raises(FileNotFoundError) as exc_info:
            Util.load_yaml_config("/nonexistent/config.yml")
        assert "Configuration file not found" in str(exc_info.value)

    def test_load_yaml_config_invalid_yaml(self):
        """Test loading invalid YAML file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name

        try:
            with pytest.raises(yaml.YAMLError) as exc_info:
                Util.load_yaml_config(temp_file)
            assert "Error parsing YAML file" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_load_yaml_config_profile_not_found(self):
        """Test specifying non-existent profile"""
        test_config = {"default": {"display_name": "test-agent"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(test_config, f)
            temp_file = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                Util.load_yaml_config(temp_file, "nonexistent")
            assert "Profile 'nonexistent' not found" in str(exc_info.value)
            assert "Available profiles: ['default']" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_load_yaml_config_empty_file(self):
        """Test loading empty YAML file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("")
            temp_file = f.name

        try:
            result = Util.load_yaml_config(temp_file)
            assert result == {}
        finally:
            os.unlink(temp_file)

    def test_import_from_string_success(self):
        """Test successful import from string"""
        # Test importing standard library module
        result = Util.import_from_string("os.path.join")
        assert result == os.path.join

        # Test class import
        result = Util.import_from_string("tempfile.NamedTemporaryFile")
        assert result == tempfile.NamedTemporaryFile

    def test_import_from_string_module_not_found(self):
        """Test importing non-existent module"""
        with pytest.raises(ImportError) as exc_info:
            Util.import_from_string("nonexistent.module.function")
        assert "Cannot import 'nonexistent.module.function'" in str(exc_info.value)

    def test_import_from_string_attribute_not_found(self):
        """Test importing non-existent attribute"""
        with pytest.raises(ImportError) as exc_info:
            Util.import_from_string("os.nonexistent_function")
        assert "Cannot import 'os.nonexistent_function'" in str(exc_info.value)

    def test_import_from_string_invalid_path(self):
        """Test invalid import path"""
        with pytest.raises(ImportError) as exc_info:
            Util.import_from_string("invalid_path_without_dots")
        assert "Cannot import 'invalid_path_without_dots'" in str(exc_info.value)
