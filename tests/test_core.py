import tempfile
import os
import yaml
from unittest.mock import patch, MagicMock
import pytest
from vaiae.core import Core


class TestCore:
    """Test Core class"""

    def create_test_yaml_config(self, temp_dir, profile="default"):
        """Create a YAML configuration file for testing"""
        config = {
            profile: {
                "vertex_ai": {
                    "project": "test-project",
                    "location": "us-central1",
                    "staging_bucket": "test-bucket",
                },
                "display_name": "test-agent",
                "description": "Test agent description",
                "gcs_dir_name": "test-agent/1.0.0",
                "agent_engine": {"instance_path": "test.agent.main"},
                "env_vars": {"TEST_VAR": "test_value"},
                "requirements": ["google-cloud-aiplatform[adk,agent_engines]==1.132.0"],
                "extra_packages": ["test_package.whl"],
                "service_account": "test-sa@test-project.iam.gserviceaccount.com",
                "labels": {"env": "test"},
                "min_instances": 1,
                "max_instances": 3,
            }
        }

        config_file = os.path.join(temp_dir, ".agent-engine.yml")
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        return config_file

    def test_init_with_yaml_file(self):
        """Test Core initialization with YAML file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            assert core.project == "test-project"
            assert core.location == "us-central1"
            assert core.staging_bucket == "test-bucket"
            assert core.profile == "default"
            assert core.config is not None
            assert core.config["display_name"] == "test-agent"

    def test_init_without_yaml_file(self):
        """Test Core initialization without YAML file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            os.chdir(temp_dir)

            with patch("vaiae.util.Util.find_config_file", return_value=config_file):
                core = Core(profile="default", debug=False)

                assert core.project == "test-project"
                assert core.location == "us-central1"

    def test_init_with_invalid_profile(self):
        """Test Core initialization with invalid profile"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            with pytest.raises(ValueError, match="Profile 'invalid' not found"):
                Core(yaml_file_path=config_file, profile="invalid", debug=False)

    @patch("vertexai.init")
    @patch("vertexai.Client")
    def test_ensure_vertex_ai_initialized(self, mock_client_class, mock_vertexai_init):
        """Test Vertex AI initialization"""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            # Trigger initialization
            core._ensure_vertex_ai_initialized()

            mock_vertexai_init.assert_called_once_with(
                project="test-project",
                location="us-central1",
                staging_bucket="gs://test-bucket",
            )
            mock_client_class.assert_called_once_with(
                project="test-project",
                location="us-central1",
            )
            assert core._vertex_ai_initialized is True
            assert core._client == mock_client_instance

    @patch("vertexai.init")
    @patch("vertexai.Client")
    def test_get_agent_engine_success(self, mock_client_class, mock_vertexai_init):
        """Test get_agent_engine with success"""
        mock_client_instance = MagicMock()
        mock_agent_engine = MagicMock()
        mock_agent_engine.api_resource.name = (
            "projects/test/locations/us-central1/reasoningEngines/123"
        )
        mock_agent_engine.api_resource.display_name = "test-agent"

        mock_client_instance.agent_engines.list.return_value = [mock_agent_engine]
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            result = core.get_agent_engine("test-agent")

            assert result == mock_agent_engine
            mock_client_instance.agent_engines.list.assert_called_once_with(
                config={"filter": 'display_name="test-agent"'}
            )

    @patch("vertexai.init")
    @patch("vertexai.Client")
    def test_get_agent_engine_not_found(self, mock_client_class, mock_vertexai_init):
        """Test get_agent_engine when agent engine is not found"""
        mock_client_instance = MagicMock()
        mock_client_instance.agent_engines.list.return_value = []
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            result = core.get_agent_engine("nonexistent-agent")

            assert result is None

    @patch("vertexai.init")
    @patch("vertexai.Client")
    def test_list_agent_engine(self, mock_client_class, mock_vertexai_init):
        """Test list_agent_engine"""
        mock_client_instance = MagicMock()
        mock_agent_engine_1 = MagicMock()
        mock_agent_engine_2 = MagicMock()

        mock_client_instance.agent_engines.list.return_value = [
            mock_agent_engine_1,
            mock_agent_engine_2,
        ]
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            result = core.list_agent_engine()

            assert len(result) == 2
            assert result[0] == mock_agent_engine_1
            assert result[1] == mock_agent_engine_2
            mock_client_instance.agent_engines.list.assert_called_once()

    @patch("vertexai.init")
    @patch("vertexai.Client")
    def test_delete_agent_engine_success(self, mock_client_class, mock_vertexai_init):
        """Test delete_agent_engine with success"""
        mock_client_instance = MagicMock()
        mock_agent_engine = MagicMock()
        mock_agent_engine.api_resource.name = (
            "projects/test/locations/us-central1/reasoningEngines/123"
        )
        mock_agent_engine.delete = MagicMock()

        mock_client_instance.agent_engines.list.return_value = [mock_agent_engine]
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            core.delete_agent_engine("test-agent", force=True, dry_run=False)

            mock_agent_engine.delete.assert_called_once_with(force=True)

    @patch("vertexai.init")
    @patch("vertexai.Client")
    def test_delete_agent_engine_not_found(self, mock_client_class, mock_vertexai_init):
        """Test delete_agent_engine when agent engine is not found"""
        mock_client_instance = MagicMock()
        mock_client_instance.agent_engines.list.return_value = []
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            with pytest.raises(
                Exception, match="Agent engine with display name 'test-agent' not found"
            ):
                core.delete_agent_engine("test-agent", force=False, dry_run=False)

    @patch("vertexai.init")
    @patch("vertexai.Client")
    def test_delete_agent_engine_dry_run(self, mock_client_class, mock_vertexai_init):
        """Test delete_agent_engine in dry run mode"""
        mock_client_instance = MagicMock()
        mock_agent_engine = MagicMock()
        mock_agent_engine.api_resource.name = (
            "projects/test/locations/us-central1/reasoningEngines/123"
        )
        mock_agent_engine.delete = MagicMock()

        mock_client_instance.agent_engines.list.return_value = [mock_agent_engine]
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            core.delete_agent_engine("test-agent", force=False, dry_run=True)

            # Verify delete was not called
            mock_agent_engine.delete.assert_not_called()

    @patch("vaiae.util.Util.import_from_string")
    def test_get_agent_instance_from_config(self, mock_import):
        """Test _get_agent_instance_from_config"""
        mock_agent = MagicMock()
        mock_import.return_value = mock_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            agent_config = {"instance_path": "test.agent.main"}
            result = core._get_agent_instance_from_config(agent_config)

            assert result == mock_agent
            mock_import.assert_called_once_with("test.agent.main")

    def test_get_agent_instance_from_config_no_instance_path(self):
        """Test _get_agent_instance_from_config without instance_path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            agent_config = {}

            with pytest.raises(
                ValueError,
                match="instance_path must be provided in agent_engine configuration",
            ):
                core._get_agent_instance_from_config(agent_config)

    @patch("vaiae.util.Util.import_from_string")
    def test_build_agent_engine_config(self, mock_import):
        """Test _build_agent_engine_config"""
        mock_agent = MagicMock()
        mock_import.return_value = mock_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            assert core.config is not None
            agent_instance, config_dict = core._build_agent_engine_config(core.config)

            assert agent_instance == mock_agent
            assert config_dict["display_name"] == "test-agent"
            assert config_dict["description"] == "Test agent description"
            assert config_dict["gcs_dir_name"] == "test-agent/1.0.0"
            assert config_dict["requirements"] == [
                "google-cloud-aiplatform[adk,agent_engines]==1.132.0"
            ]
            assert config_dict["extra_packages"] == ["test_package.whl"]
            assert config_dict["env_vars"] == {"TEST_VAR": "test_value"}
            assert (
                config_dict["service_account"]
                == "test-sa@test-project.iam.gserviceaccount.com"
            )
            assert config_dict["staging_bucket"] == "gs://test-bucket"
            assert config_dict["labels"] == {"env": "test"}
            assert config_dict["min_instances"] == 1
            assert config_dict["max_instances"] == 3

    @patch("vertexai.init")
    @patch("vertexai.Client")
    @patch("vaiae.util.Util.import_from_string")
    def test_create_or_update_create_new(
        self, mock_import, mock_client_class, mock_vertexai_init
    ):
        """Test create_or_update when creating new agent engine"""
        mock_agent = MagicMock()
        mock_import.return_value = mock_agent

        mock_client_instance = MagicMock()
        mock_client_instance.agent_engines.list.return_value = []
        mock_client_instance.agent_engines.create.return_value = MagicMock()
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            config_dict = {
                "display_name": "test-agent",
                "description": "Test agent",
                "requirements": [],
                "extra_packages": [],
                "gcs_dir_name": "test-agent/1.0.0",
                "env_vars": {},
                "staging_bucket": "gs://test-bucket",
            }

            core.create_or_update(mock_agent, config_dict, "test-agent", dry_run=False)

            mock_client_instance.agent_engines.create.assert_called_once_with(
                agent=mock_agent,
                config=config_dict,
            )

    @patch("vertexai.init")
    @patch("vertexai.Client")
    @patch("vaiae.util.Util.import_from_string")
    def test_create_or_update_update_existing(
        self, mock_import, mock_client_class, mock_vertexai_init
    ):
        """Test create_or_update when updating existing agent engine"""
        mock_agent = MagicMock()
        mock_import.return_value = mock_agent

        mock_existing_agent = MagicMock()
        mock_existing_agent.api_resource.name = (
            "projects/test/locations/us-central1/reasoningEngines/123"
        )

        mock_client_instance = MagicMock()
        mock_client_instance.agent_engines.list.return_value = [mock_existing_agent]
        mock_client_instance.agent_engines.update.return_value = MagicMock()
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            config_dict = {
                "display_name": "test-agent",
                "description": "Test agent",
                "requirements": [],
                "extra_packages": [],
                "gcs_dir_name": "test-agent/1.0.0",
                "env_vars": {},
                "staging_bucket": "gs://test-bucket",
            }

            core.create_or_update(mock_agent, config_dict, "test-agent", dry_run=False)

            mock_client_instance.agent_engines.update.assert_called_once_with(
                name="projects/test/locations/us-central1/reasoningEngines/123",
                agent=mock_agent,
                config=config_dict,
            )

    @patch("vertexai.init")
    @patch("vertexai.Client")
    @patch("vaiae.util.Util.import_from_string")
    def test_create_or_update_dry_run_create(
        self, mock_import, mock_client_class, mock_vertexai_init
    ):
        """Test create_or_update in dry run mode (create)"""
        mock_agent = MagicMock()
        mock_import.return_value = mock_agent

        mock_client_instance = MagicMock()
        mock_client_instance.agent_engines.list.return_value = []
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            config_dict = {
                "display_name": "test-agent",
                "description": "Test agent",
                "requirements": [],
                "extra_packages": [],
                "gcs_dir_name": "test-agent/1.0.0",
                "env_vars": {},
                "staging_bucket": "gs://test-bucket",
            }

            core.create_or_update(mock_agent, config_dict, "test-agent", dry_run=True)

            # Verify create was not called
            mock_client_instance.agent_engines.create.assert_not_called()

    @patch("vertexai.init")
    @patch("vertexai.Client")
    @patch("vaiae.util.Util.import_from_string")
    def test_create_or_update_from_yaml(
        self, mock_import, mock_client_class, mock_vertexai_init
    ):
        """Test create_or_update_from_yaml"""
        mock_agent = MagicMock()
        mock_import.return_value = mock_agent

        mock_client_instance = MagicMock()
        mock_client_instance.agent_engines.list.return_value = []
        mock_client_instance.agent_engines.create.return_value = MagicMock()
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            core.create_or_update_from_yaml(dry_run=False)

            # Verify create was called with correct parameters
            mock_client_instance.agent_engines.create.assert_called_once()
            call_args = mock_client_instance.agent_engines.create.call_args
            assert call_args[1]["agent"] == mock_agent
            assert call_args[1]["config"]["display_name"] == "test-agent"

    @patch("vaiae.util.Util.import_from_string")
    def test_create_or_update_from_yaml_no_display_name(self, mock_import):
        """Test create_or_update_from_yaml without display_name"""
        mock_agent = MagicMock()
        mock_import.return_value = mock_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config without display_name
            config = {
                "default": {
                    "vertex_ai": {
                        "project": "test-project",
                        "location": "us-central1",
                    },
                    "agent_engine": {"instance_path": "test.agent.main"},
                }
            }

            config_file = os.path.join(temp_dir, ".agent-engine.yml")
            with open(config_file, "w") as f:
                yaml.dump(config, f)

            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            with pytest.raises(
                ValueError, match="display_name must be provided in YAML config"
            ):
                core.create_or_update_from_yaml(dry_run=False)

    @patch("vertexai.init")
    @patch("vertexai.Client")
    def test_delete_agent_engine_from_yaml(self, mock_client_class, mock_vertexai_init):
        """Test delete_agent_engine_from_yaml"""
        mock_client_instance = MagicMock()
        mock_agent_engine = MagicMock()
        mock_agent_engine.api_resource.name = (
            "projects/test/locations/us-central1/reasoningEngines/123"
        )
        mock_agent_engine.delete = MagicMock()

        mock_client_instance.agent_engines.list.return_value = [mock_agent_engine]
        mock_client_class.return_value = mock_client_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            core.delete_agent_engine_from_yaml(force=True, dry_run=False)

            mock_agent_engine.delete.assert_called_once_with(force=True)

    def test_apply_overrides(self):
        """Test _apply_overrides"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)
            core = Core(yaml_file_path=config_file, profile="default", debug=False)

            original_config = {
                "display_name": "original-name",
                "description": "original description",
                "env_vars": {"VAR1": "value1"},
            }

            overrides = {
                "description": "new description",
                "env_vars": {"VAR2": "value2"},
            }

            updated_config = core._apply_overrides(original_config, overrides)

            assert updated_config["display_name"] == "original-name"
            assert updated_config["description"] == "new description"
            # deep_update merges dictionaries, so VAR1 should still be present
            assert updated_config["env_vars"] == {"VAR1": "value1", "VAR2": "value2"}
            # Verify original config is not modified
            assert original_config["description"] == "original description"
