# vaiae

[![PyPI version](https://badge.fury.io/py/vaiae.svg)](https://badge.fury.io/py/vaiae)
[![Build Status](https://github.com/toyama0919/vaiae/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/toyama0919/vaiae/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/vaiae.svg)](https://pypi.org/project/vaiae/)
[![License](https://img.shields.io/github/license/toyama0919/vaiae.svg)](https://github.com/toyama0919/vaiae/blob/main/LICENSE)

**Vertex AI Agent Engine**のデプロイと管理を行うためのコマンドラインツールです。

YAMLベースの設定ファイルを使用して、エージェントエンジンの作成、更新、削除、およびメッセージ送信を簡単に行うことができます。

## 🚀 特徴

- **簡単なデプロイ**: YAMLファイルでエージェントエンジンを定義し、ワンコマンドでデプロイ
- **プロファイル管理**: 開発、本番環境など複数の環境設定を一つのファイルで管理
- **インタラクティブメッセージング**: デプロイしたエージェントとの対話機能
- **包括的な管理**: エージェントエンジンの作成、更新、削除、一覧表示
- **Python API**: コマンドライン以外にもPython APIとしても利用可能
- **ドライラン対応**: 実際の操作前に設定内容を確認可能

## 📋 要件

- Python 3.10以上
- Google Cloud Platform アカウント
- Vertex AI API の有効化

## 🔧 インストール

### PyPIからのインストール

```bash
pip install vaiae
```

### 開発版のインストール

```bash
git clone https://github.com/toyama0919/vaiae.git
cd vaiae
pip install -e .
```

## ⚙️ 初期設定

### 認証の設定

Google Cloud認証を設定します：

```bash
# Application Default Credentials を使用する場合
gcloud auth application-default login

# サービスアカウントキーを使用する場合
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## 📝 設定ファイル

プロジェクトルートに `.agent-engine.yml` ファイルを作成し、エージェントエンジンの設定を定義します。

### 基本的な設定例

```yaml
# 基本プロファイル
default:
  # Vertex AI 設定
  vertex_ai:
    project: "my-gcp-project"
    location: "asia-northeast1"
    staging_bucket: "my-staging-bucket"

  display_name: "my-agent-engine"
  description: "My custom agent engine"
  gcs_dir_name: "my-agent/1.0.0"

  # エージェント設定
  agent_engine:
    instance_path: "my_package.agents.main_agent"

  # 環境変数
  env_vars:
    API_KEY: "your-api-key"
    SLACK_WEBHOOK_URL:
      secret: "slack-webhook-url"
      version: "latest"

  # 依存関係
  requirements:
    - "google-cloud-aiplatform[adk,agent_engines]==1.96.0"
    - "google-adk"
    - "requests"

  # 追加パッケージ
  extra_packages:
    - "my-custom-package-1.0.0-py3-none-any.whl"

# 開発環境
development:
  vertex_ai:
    project: "dev-project"
    location: "asia-northeast1"
  display_name: "my-agent-dev"
  description: "Development environment agent"
  # 他の設定は default から継承

# 本番環境
production:
  vertex_ai:
    project: "prod-project"
    location: "asia-northeast1"
  display_name: "my-agent-prod"
  description: "Production environment agent"
  # 他の設定は default から継承
```

### エージェント設定の方法

```yaml
agent_engine:
  instance_path: "my_package.agents.root_agent"
```

既存のエージェントインスタンスを動的にインポートして使用します。

### エージェントエンジンのデプロイ

```bash
# ドライランでデプロイ内容を確認
vaiae deploy --dry-run

# 実際にデプロイ
vaiae deploy

# 特定のプロファイルを使用
vaiae --profile production deploy

# カスタム設定ファイルを使用
vaiae --yaml-file custom-config.yml deploy
```

### デプロイ済みエージェントエンジンの一覧表示

```bash
vaiae list
```

### エージェントへのメッセージ送信

```bash
# 基本的なメッセージ送信
vaiae send -m "こんにちは、分析をお願いします" -d "my-agent-engine"

# セッションIDを指定して継続的な会話
vaiae send -m "続きをお願いします" -d "my-agent-engine" -s "session-123"

# ユーザーIDを指定
vaiae send -m "レポートを作成してください" -d "my-agent-engine" -u "user-456"
```

### エージェントエンジンの削除

```bash
# 名前を指定して削除（ドライラン）
vaiae delete -n "my-agent-engine" --dry-run

# 実際に削除
vaiae delete -n "my-agent-engine"

# 現在のプロファイル設定を使用して削除
vaiae delete --dry-run

# 強制削除（子リソースも含む）
vaiae delete -n "my-agent-engine" --force
```

### デバッグモード

```bash
# 詳細なログ出力でデバッグ
vaiae --debug deploy
```

## 🐍 Python API使用方法

### 基本的な使用方法

```python
from vaiae.core import Core

# Core インスタンスの初期化
core = Core(
    yaml_file_path=".agent-engine.yml",
    profile="default"
)

# デプロイ
core.create_or_update_from_yaml(dry_run=False)

# メッセージ送信
response = core.send_message(
    message="分析をお願いします",
    display_name="my-agent-engine",
    user_id="user123"
)
print(response)
```

### プロファイル別のデプロイ

```python
from vaiae.core import Core

# 開発環境にデプロイ
dev_core = Core(yaml_file_path=".agent-engine.yml", profile="development")
dev_core.create_or_update_from_yaml(dry_run=False)

# 本番環境にデプロイ
prod_core = Core(yaml_file_path=".agent-engine.yml", profile="production")
prod_core.create_or_update_from_yaml(dry_run=False)
```

### 設定のオーバーライド

```python
from vaiae.core import Core

core = Core(yaml_file_path=".agent-engine.yml", profile="development")

# YAML設定を部分的にオーバーライド
core.create_or_update_from_yaml(
    dry_run=False,
    description="カスタム説明",
    env_vars={
        "CUSTOM_VAR": "custom_value",
        "API_ENDPOINT": "https://api.example.com"
    },
    requirements=["additional-package==1.0.0"]
)
```

### エージェントエンジンの管理

```python
from vaiae.core import Core

core = Core(yaml_file_path=".agent-engine.yml", profile="default")

# 一覧取得
agent_engines = core.list_agent_engine()
for engine in agent_engines:
    print(f"Name: {engine.display_name}")
    print(f"Resource: {engine.resource_name}")

# 削除
core.delete_agent_engine_from_yaml(
    force=False,
    dry_run=False
)
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 認証エラー

```
Error: Could not automatically determine credentials
```

**解決方法:**
```bash
gcloud auth application-default login
# または
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### 権限不足エラー

```
Error: Permission denied
```

**解決方法:**
- サービスアカウントまたはユーザーに以下の権限が必要です：
  - `aiplatform.agentEngines.create`
  - `aiplatform.agentEngines.update`
  - `aiplatform.agentEngines.delete`
  - `aiplatform.agentEngines.list`

#### YAML設定エラー

```
Error: Invalid YAML configuration
```

**解決方法:**
- YAML構文が正しいか確認
- 必須フィールドが設定されているか確認
- インデントが正しいか確認

### デバッグ方法

詳細なログを確認するには：

```bash
vaiae --debug deploy
```

## 🧪 開発・テスト

### 開発環境のセットアップ

```bash
git clone https://github.com/toyama0919/vaiae.git
cd vaiae

# 開発用依存関係のインストール
pip install -e ".[test]"
```

### テストの実行

```bash
# テストパッケージのインストール
./scripts/ci.sh install

# テスト実行
./scripts/ci.sh run-test

# 個別テスト実行
pytest tests/test_commands.py
pytest tests/test_util.py
```

### コード品質チェック

```bash
# flake8, black, pytestを実行
./scripts/ci.sh run-test
```

### リリース

```bash
# バージョンタグ作成とPyPIリリース
./scripts/ci.sh release
```

## 📚 API リファレンス

### Core クラス

主要なAPIクラスです。

#### 初期化

```python
Core(
    yaml_file_path: str = None,
    profile: str = "default",
    project: str = None,
    location: str = None,
    staging_bucket: str = None,
    debug: bool = False
)
```

#### 主要メソッド

- `create_or_update_from_yaml(dry_run=False, **overrides)`: エージェントエンジンのデプロイ
- `delete_agent_engine_from_yaml(force=False, dry_run=False)`: エージェントエンジンの削除
- `send_message(message, display_name, session_id=None, user_id=None)`: メッセージ送信
- `list_agent_engine()`: エージェントエンジン一覧取得

## 🤝 貢献

プロジェクトへの貢献を歓迎します！

### 貢献方法

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### 開発ガイドライン

- コードスタイル: Black + flake8
- テスト: pytest
- コミットメッセージ: 英語で簡潔に
- ドキュメント: 新機能には適切なドキュメントを追加

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 👨‍💻 作者

**Hiroshi Toyama** - [toyama0919@gmail.com](mailto:toyama0919@gmail.com)

## 🔗 関連リンク

- [PyPI Package](https://pypi.org/project/vaiae/)
- [GitHub Repository](https://github.com/toyama0919/vaiae)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai)
- [Vertex AI Agent Builder](https://cloud.google.com/vertex-ai/docs/agent-builder)

## 📈 変更履歴

### v0.1.0
- 初回リリース
- YAMLベース設定サポート
- プロファイル管理機能
- 基本的なCRUD操作
- Python API提供
