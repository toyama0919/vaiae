import pytest
import os
import tempfile
import yaml
from unittest.mock import patch
from vaiae.util import Util


class TestUtil:
    def setup_method(self, method):
        """各テストメソッドの前に実行される"""
        pass

    def teardown_method(self, method):
        """各テストメソッドの後に実行される"""
        pass

    def test_convert(self):
        """convert メソッドのテスト（現在は何もしない）"""
        # convertメソッドは現在何もしないので、例外が発生しないことを確認
        result = Util.convert()
        assert result is None

    def test_find_config_file_current_directory(self):
        """現在のディレクトリで設定ファイルを見つけるテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 一時ファイルを作成
            config_file = os.path.join(temp_dir, ".agent-engine.yml")
            with open(config_file, "w") as f:
                f.write("test: config")

            # 現在のディレクトリを一時ディレクトリに変更
            with patch("os.getcwd", return_value=temp_dir):
                result = Util.find_config_file()
                assert result == config_file

    def test_find_config_file_home_directory(self):
        """ホームディレクトリで設定ファイルを見つけるテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # ホームディレクトリに設定ファイルを作成
            config_file = os.path.join(temp_dir, ".agent-engine.yml")
            with open(config_file, "w") as f:
                f.write("test: config")

            # 現在のディレクトリには存在せず、ホームディレクトリに存在する場合
            with patch("os.getcwd", return_value="/nonexistent"):
                with patch("os.path.expanduser", return_value=temp_dir):
                    result = Util.find_config_file()
                    assert result == config_file

    def test_find_config_file_not_found(self):
        """設定ファイルが見つからない場合のテスト"""
        with patch("os.getcwd", return_value="/nonexistent"):
            with patch("os.path.expanduser", return_value="/nonexistent"):
                with pytest.raises(FileNotFoundError) as exc_info:
                    Util.find_config_file()
                assert "Configuration file '.agent-engine.yml' not found" in str(
                    exc_info.value
                )

    def test_find_config_file_custom_filename(self):
        """カスタムファイル名での設定ファイル検索テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # カスタムファイル名で設定ファイルを作成
            custom_filename = "custom-config.yml"
            config_file = os.path.join(temp_dir, custom_filename)
            with open(config_file, "w") as f:
                f.write("test: config")

            with patch("os.getcwd", return_value=temp_dir):
                result = Util.find_config_file(custom_filename)
                assert result == config_file

    def test_load_yaml_config_success(self):
        """YAML設定ファイルの正常読み込みテスト"""
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
            # プロファイル指定なしでの読み込み
            result = Util.load_yaml_config(temp_file)
            assert result == test_config

            # プロファイル指定ありでの読み込み
            result_default = Util.load_yaml_config(temp_file, "default")
            assert result_default == test_config["default"]

            result_production = Util.load_yaml_config(temp_file, "production")
            assert result_production == test_config["production"]
        finally:
            os.unlink(temp_file)

    def test_load_yaml_config_file_not_found(self):
        """存在しないYAMLファイルの読み込みテスト"""
        with pytest.raises(FileNotFoundError) as exc_info:
            Util.load_yaml_config("/nonexistent/config.yml")
        assert "Configuration file not found" in str(exc_info.value)

    def test_load_yaml_config_invalid_yaml(self):
        """不正なYAMLファイルの読み込みテスト"""
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
        """存在しないプロファイルの指定テスト"""
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
        """空のYAMLファイルの読み込みテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("")
            temp_file = f.name

        try:
            result = Util.load_yaml_config(temp_file)
            assert result == {}
        finally:
            os.unlink(temp_file)

    def test_import_from_string_success(self):
        """文字列からのインポート成功テスト"""
        # 標準ライブラリのモジュールをテスト
        result = Util.import_from_string("os.path.join")
        assert result == os.path.join

        # クラスのインポートテスト
        result = Util.import_from_string("tempfile.NamedTemporaryFile")
        assert result == tempfile.NamedTemporaryFile

    def test_import_from_string_module_not_found(self):
        """存在しないモジュールのインポートテスト"""
        with pytest.raises(ImportError) as exc_info:
            Util.import_from_string("nonexistent.module.function")
        assert "Cannot import 'nonexistent.module.function'" in str(exc_info.value)

    def test_import_from_string_attribute_not_found(self):
        """存在しない属性のインポートテスト"""
        with pytest.raises(ImportError) as exc_info:
            Util.import_from_string("os.nonexistent_function")
        assert "Cannot import 'os.nonexistent_function'" in str(exc_info.value)

    def test_import_from_string_invalid_path(self):
        """不正なインポートパスのテスト"""
        with pytest.raises(ImportError) as exc_info:
            Util.import_from_string("invalid_path_without_dots")
        assert "Cannot import 'invalid_path_without_dots'" in str(exc_info.value)
