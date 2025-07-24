import tempfile
import os
import yaml
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from vaiae import commands


class TestCommands:
    def setup_method(self, method):
        """各テストメソッドの前に実行される"""
        self.runner = CliRunner()

    def teardown_method(self, method):
        """各テストメソッドの後に実行される"""
        pass

    def create_test_yaml_config(self, temp_dir):
        """テスト用のYAML設定ファイルを作成"""
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
        """CLIの正常な初期化テスト"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        # --helpオプションでCLIが正常に動作することを確認
        result = self.runner.invoke(commands.cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    @patch("vaiae.commands.Core")
    def test_cli_initialization_error(self, mock_core_class):
        """CLI初期化エラーのテスト"""
        mock_core_class.side_effect = Exception("Initialization error")

        result = self.runner.invoke(
            commands.cli, ["--yaml-file", "nonexistent.yml", "deploy"]
        )
        assert result.exit_code == 1
        assert "Error initializing Core" in result.output

    @patch("vaiae.commands.Core")
    def test_deploy_command_dry_run(self, mock_core_class):
        """deployコマンドのドライランテスト"""
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
        """deployコマンドの成功テスト"""
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
        """deployコマンドのエラーテスト"""
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
        """listコマンドの成功テスト"""
        mock_core_instance = MagicMock()

        # モックエージェントエンジンオブジェクトを作成
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
        """listコマンドでエージェントエンジンが見つからない場合のテスト"""
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
        """listコマンドのエラーテスト"""
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
        """sendコマンドの成功テスト"""
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
                    "-d",
                    "test-agent",
                    "-u",
                    "test-user",
                    "-s",
                    "session-123",
                ],
            )

            assert result.exit_code == 0
            mock_core_instance.send_message.assert_called_once_with(
                message="Hello, agent!",
                display_name="test-agent",
                session_id="session-123",
                user_id="test-user",
            )

    @patch("vaiae.commands.Core")
    def test_send_command_error(self, mock_core_class):
        """sendコマンドのエラーテスト"""
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
                    "-d",
                    "test-agent",
                ],
            )

            assert result.exit_code == 1
            assert "Error: Send error" in result.output

    @patch("vaiae.commands.Core")
    def test_delete_command_by_name_dry_run(self, mock_core_class):
        """deleteコマンドの名前指定ドライランテスト"""
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
        """deleteコマンドのプロファイル指定テスト"""
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
        """deleteコマンドのエラーテスト"""
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
        """デバッグフラグ付きCLIテスト"""
        mock_core_instance = MagicMock()
        mock_core_class.return_value = mock_core_instance

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = self.create_test_yaml_config(temp_dir)

            result = self.runner.invoke(
                commands.cli,
                ["--yaml-file", config_file, "--debug", "deploy", "--dry-run"],
            )

            assert result.exit_code == 0
            # Coreが正しい引数で初期化されることを確認
            mock_core_class.assert_called_once_with(
                yaml_file_path=config_file, profile="default", debug=True
            )

    def test_main_function(self):
        """main関数のテスト"""
        # main関数が例外を発生させずに呼び出せることを確認
        with patch("vaiae.commands.cli") as mock_cli:
            commands.main()
            mock_cli.assert_called_once_with(obj={})
