import tempfile
import os
import yaml
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from vaiae import commands


class TestCommands:
    def setup_method(self, method):
        """Executed before each test method"""
        self.runner = CliRunner()

    def teardown_method(self, method):
        """Executed after each test method"""
        pass

    def create_test_yaml_config(self, temp_dir):
        """Create a YAML configuration file for testing"""
        config = {
            "default": {
                "vertex_ai": {
                    "project": "test-project",
                    "location": "asia-northeast1",
                    "staging_bucket": "test-bucket",
                },
                "display_name": "test-agent",
                "description": "Test agent description",
                "gcs_dir_name": "test-agent/1.0.0",
                "agent_engine": {"instance_path": "test.agent.main"},
                "env_vars": {"TEST_VAR": "test_value"},
                "requirements": ["google-cloud-aiplatform[adk,agent_engines]==1.96.0"],
            }
        }

        config_file = os.path.join(temp_dir, ".agent-engine.yml")
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        return config_file

    @patch("vaiae.commands.Core")
    def test_cli_initialization_success(self, mock_core_class):
        """Test successful CLI initialization"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        # Verify that CLI works correctly with --help option
        result = self.runner.invoke(commands.cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    @patch("vaiae.commands.Core")
    def test_cli_initialization_error(self, mock_core_class):
        """Test CLI initialization error"""
        mock_core_class.side_effect = Exception("Initialization error")

        result = self.runner.invoke(
            commands.cli, ["--yaml-file", "nonexistent.yml", "deploy"]
        )
        assert result.exit_code == 1
        assert "Error initializing Core" in result.output

    @patch("vaiae.commands.Core")
    def test_deploy_command_dry_run(self, mock_core_class):
        """Test deploy command dry run"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                [
                    "--yaml-file",
                    config_file,
                    "--profile",
                    "default",
                    "deploy",
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0
            assert "Dry run completed for profile 'default'" in result.output
            mock_core_instance.create_or_update_from_yaml.assert_called_once_with(
                dry_run=True
            )

    @patch("vaiae.commands.Core")
    def test_deploy_command_success(self, mock_core_class):
        """Test successful deploy command"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                ["--yaml-file", config_file, "--profile", "default", "deploy"],
            )

            assert result.exit_code == 0
            assert (
                "Successfully deployed agent engine using profile 'default'"
                in result.output
            )
            mock_core_instance.create_or_update_from_yaml.assert_called_once_with(
                dry_run=False
            )

    @patch("vaiae.commands.Core")
    def test_deploy_command_error(self, mock_core_class):
        """Test deploy command error"""
        mock_core_instance = MagicMock()
        mock_core_instance.create_or_update_from_yaml.side_effect = Exception(
            "Deploy error"
        )
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli, ["--yaml-file", config_file, "deploy"]
            )

            assert result.exit_code == 1
            assert "Error: Deploy error" in result.output

    @patch("vaiae.commands.Core")
    def test_list_command_success(self, mock_core_class):
        """Test successful list command"""
        mock_core_instance = MagicMock()

        # Create mock agent engine object
        mock_agent_engine = MagicMock()
        mock_agent_engine.display_name = "test-agent"
        mock_agent_engine.resource_name = (
            "projects/test/locations/asia-northeast1/agentEngines/test-agent"
        )
        mock_agent_engine.create_time = "2024-01-01T00:00:00Z"
        mock_agent_engine.update_time = "2024-01-01T00:00:00Z"

        mock_core_instance.list_agent_engine.return_value = [mock_agent_engine]
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli, ["--yaml-file", config_file, "list"]
            )

            assert result.exit_code == 0
            assert "Found 1 agent engine(s):" in result.output
            assert "test-agent" in result.output

    @patch("vaiae.commands.Core")
    def test_list_command_no_engines(self, mock_core_class):
        """Test list command when no agent engines are found"""
        mock_core_instance = MagicMock()
        mock_core_instance.list_agent_engine.return_value = []
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli, ["--yaml-file", config_file, "list"]
            )

            assert result.exit_code == 0
            assert "No agent engines found." in result.output

    @patch("vaiae.commands.Core")
    def test_list_command_error(self, mock_core_class):
        """Test list command error"""
        mock_core_instance = MagicMock()
        mock_core_instance.list_agent_engine.side_effect = Exception("List error")
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli, ["--yaml-file", config_file, "list"]
            )

            assert result.exit_code == 1
            assert "Error: List error" in result.output

    @patch("vaiae.commands.Core")
    def test_send_command_success(self, mock_core_class):
        """Test successful send command"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                [
                    "--yaml-file",
                    config_file,
                    "send",
                    "-m",
                    "Hello, agent!",
                    "-u",
                    "test-user",
                    "-s",
                    "session-123",
                ],
            )

            assert result.exit_code == 0
            mock_core_instance.send_message.assert_called_once_with(
                message="Hello, agent!",
                session_id="session-123",
                user_id="test-user",
                local=False,
            )

    @patch("vaiae.commands.Core")
    def test_send_command_error(self, mock_core_class):
        """Test send command error"""
        mock_core_instance = MagicMock()
        mock_core_instance.send_message.side_effect = Exception("Send error")
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                [
                    "--yaml-file",
                    config_file,
                    "send",
                    "-m",
                    "Hello, agent!",
                ],
            )

            assert result.exit_code == 1
            assert "Error: Send error" in result.output

    @patch("vaiae.commands.Core")
    def test_send_command_local_mode(self, mock_core_class):
        """Test send command local mode"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                [
                    "--yaml-file",
                    config_file,
                    "send",
                    "-m",
                    "Hello, agent!",
                    "--local",
                ],
            )

            assert result.exit_code == 0
            mock_core_instance.send_message.assert_called_once_with(
                message="Hello, agent!",
                session_id=None,
                user_id=os.environ.get("USER"),
                local=True,
            )

    @patch("vaiae.commands.Core")
    def test_delete_command_by_name_dry_run(self, mock_core_class):
        """Test delete command dry run with name"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                ["--yaml-file", config_file, "delete", "-n", "test-agent", "--dry-run"],
            )

            assert result.exit_code == 0
            assert "Dry run completed for 'test-agent' deletion" in result.output
            mock_core_instance.delete_agent_engine.assert_called_once_with(
                name="test-agent", force=False, dry_run=True
            )

    @patch("vaiae.commands.Core")
    def test_delete_command_by_profile(self, mock_core_class):
        """Test delete command with profile"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                [
                    "--yaml-file",
                    config_file,
                    "--profile",
                    "default",
                    "delete",
                    "--force",
                ],
            )

            assert result.exit_code == 0
            assert (
                "Successfully deleted agent engine using profile 'default'"
                in result.output
            )
            mock_core_instance.delete_agent_engine_from_yaml.assert_called_once_with(
                force=True, dry_run=False
            )

    @patch("vaiae.commands.Core")
    def test_delete_command_error(self, mock_core_class):
        """Test delete command error"""
        mock_core_instance = MagicMock()
        mock_core_instance.delete_agent_engine.side_effect = Exception("Delete error")
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli, ["--yaml-file", config_file, "delete", "-n", "test-agent"]
            )

            assert result.exit_code == 1
            assert "Error: Delete error" in result.output

    @patch("vaiae.commands.Core")
    def test_cli_with_debug_flag(self, mock_core_class):
        """Test CLI with debug flag"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                ["--yaml-file", config_file, "--debug", "deploy", "--dry-run"],
            )

            assert result.exit_code == 0
            # Verify that Core is initialized with correct arguments
            mock_core_class.assert_called_once_with(
                yaml_file_path=config_file, profile="default", debug=True
            )

    def test_main_function(self):
        """Test main function"""
        # Verify that main function can be called without raising exceptions
        with patch("vaiae.commands.cli") as mock_cli:
            commands.main()
            mock_cli.assert_called_once_with(obj={})
