# vaiae

[![PyPI version](https://badge.fury.io/py/vaiae.svg)](https://badge.fury.io/py/vaiae)
[![Build Status](https://github.com/toyama0919/vaiae/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/toyama0919/vaiae/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/vaiae.svg)](https://pypi.org/project/vaiae/)
[![License](https://img.shields.io/github/license/toyama0919/vaiae.svg)](https://github.com/toyama0919/vaiae/blob/main/LICENSE)

A command-line tool for deploying and managing **Vertex AI Agent Engine**.

Easily create, update, delete, and send messages to agent engines using YAML-based configuration files.

## 🚀 Features

- **Easy Deployment**: Define agent engines in YAML files and deploy with a single command
- **Profile Management**: Manage multiple environment configurations (dev, prod, etc.) in one file
- **Interactive Messaging**: Chat with your deployed agents
- **Comprehensive Management**: Create, update, delete, and list agent engines
- **Python API**: Use as a Python library in addition to the CLI
- **Dry Run Support**: Preview operations before executing them

## 📋 Requirements

- Python 3.10 or higher
- Google Cloud Platform account
- Vertex AI API enabled

## 🔧 Installation

### Install from PyPI

```bash
pip install vaiae
```

### Install Development Version

```bash
git clone https://github.com/toyama0919/vaiae.git
cd vaiae
pip install -e .
```

## ⚙️ Initial Setup

### Authentication Setup

Configure Google Cloud authentication:

```bash
# Using Application Default Credentials
gcloud auth application-default login

# Using service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## 📝 Configuration File

Create a `.agent-engine.yml` file in your project root to define agent engine configurations.

### Basic Configuration Example

```yaml
# Default profile
default:
  # Vertex AI settings
  vertex_ai:
    project: "my-gcp-project"
    location: "asia-northeast1"
    staging_bucket: "my-staging-bucket"

  display_name: "my-agent-engine"
  description: "My custom agent engine"
  gcs_dir_name: "my-agent/1.0.0"

  # Agent configuration
  agent_engine:
    instance_path: "my_package.agents.main_agent"

  # Environment variables
  env_vars:
    API_KEY: "your-api-key"
    SLACK_WEBHOOK_URL:
      secret: "slack-webhook-url"
      version: "latest"

  # Dependencies
  requirements:
    - "google-cloud-aiplatform[adk,agent_engines]==1.96.0"
    - "google-adk"
    - "requests"

  # Extra packages
  extra_packages:
    - "my-custom-package-1.0.0-py3-none-any.whl"

# Development environment
development:
  vertex_ai:
    project: "dev-project"
    location: "asia-northeast1"
  display_name: "my-agent-dev"
  description: "Development environment agent"
  # Other settings inherit from default

# Production environment
production:
  vertex_ai:
    project: "prod-project"
    location: "asia-northeast1"
  display_name: "my-agent-prod"
  description: "Production environment agent"
  # Other settings inherit from default
```

### Agent Configuration

```yaml
agent_engine:
  instance_path: "my_package.agents.root_agent"
```

Dynamically imports and uses an existing agent instance.

### Deploy Agent Engine

```bash
# Dry run to preview deployment
vaiae deploy --dry-run

# Actually deploy
vaiae deploy

# Use specific profile
vaiae --profile production deploy

# Use custom config file
vaiae --yaml-file custom-config.yml deploy
```

### List Deployed Agent Engines

```bash
vaiae list
```

### Send Messages to Agent

```bash
# Basic message sending
vaiae send -m "Hello, please perform analysis" -d "my-agent-engine"

# Continue conversation with session ID
vaiae send -m "Please continue" -d "my-agent-engine" -s "session-123"

# Specify user ID
vaiae send -m "Create a report" -d "my-agent-engine" -u "user-456"
```

### Delete Agent Engine

```bash
# Delete by name (dry run)
vaiae delete -n "my-agent-engine" --dry-run

# Actually delete
vaiae delete -n "my-agent-engine"

# Delete using current profile configuration
vaiae delete --dry-run

# Force delete (including child resources)
vaiae delete -n "my-agent-engine" --force
```

### Debug Mode

```bash
# Debug with verbose logging
vaiae --debug deploy
```

## 🐍 Python API Usage

### Basic Usage

```python
from vaiae.core import Core

# Initialize Core instance
core = Core(
    yaml_file_path=".agent-engine.yml",
    profile="default"
)

# Deploy
core.create_or_update_from_yaml(dry_run=False)

# Send message
response = core.send_message(
    message="Please perform analysis",
    display_name="my-agent-engine",
    user_id="user123"
)
print(response)
```

### Profile-based Deployment

```python
from vaiae.core import Core

# Deploy to development environment
dev_core = Core(yaml_file_path=".agent-engine.yml", profile="development")
dev_core.create_or_update_from_yaml(dry_run=False)

# Deploy to production environment
prod_core = Core(yaml_file_path=".agent-engine.yml", profile="production")
prod_core.create_or_update_from_yaml(dry_run=False)
```

### Override Configuration

```python
from vaiae.core import Core

core = Core(yaml_file_path=".agent-engine.yml", profile="development")

# Partially override YAML configuration
core.create_or_update_from_yaml(
    dry_run=False,
    description="Custom description",
    env_vars={
        "CUSTOM_VAR": "custom_value",
        "API_ENDPOINT": "https://api.example.com"
    },
    requirements=["additional-package==1.0.0"]
)
```

### Agent Engine Management

```python
from vaiae.core import Core

core = Core(yaml_file_path=".agent-engine.yml", profile="default")

# List agent engines
agent_engines = core.list_agent_engine()
for engine in agent_engines:
    print(f"Name: {engine.display_name}")
    print(f"Resource: {engine.resource_name}")

# Delete
core.delete_agent_engine_from_yaml(
    force=False,
    dry_run=False
)
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Authentication Error

```
Error: Could not automatically determine credentials
```

**Solution:**
```bash
gcloud auth application-default login
# or
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### Permission Denied Error

```
Error: Permission denied
```

**Solution:**
- The service account or user needs the following permissions:
  - `aiplatform.agentEngines.create`
  - `aiplatform.agentEngines.update`
  - `aiplatform.agentEngines.delete`
  - `aiplatform.agentEngines.list`

#### YAML Configuration Error

```
Error: Invalid YAML configuration
```

**Solution:**
- Check YAML syntax is correct
- Verify required fields are configured
- Verify indentation is correct

### Debugging

For detailed logs:

```bash
vaiae --debug deploy
```

## 🧪 Development & Testing

### Development Environment Setup

```bash
git clone https://github.com/toyama0919/vaiae.git
cd vaiae

# Install development dependencies
pip install -e ".[test]"
```

### Run Tests

```bash
# Install test packages
./scripts/ci.sh install

# Run tests
./scripts/ci.sh run-test

# Run individual tests
pytest tests/test_commands.py
pytest tests/test_util.py
```

### Code Quality Checks

```bash
# Run flake8, black, pytest
./scripts/ci.sh run-test
```

### Release

```bash
# Create version tag and PyPI release
./scripts/ci.sh release
```

## 📚 API Reference

### Core Class

Main API class.

#### Initialization

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

#### Main Methods

- `create_or_update_from_yaml(dry_run=False, **overrides)`: Deploy agent engine
- `delete_agent_engine_from_yaml(force=False, dry_run=False)`: Delete agent engine
- `send_message(message, display_name, session_id=None, user_id=None)`: Send message
- `list_agent_engine()`: List agent engines

## 🤝 Contributing

Contributions to the project are welcome!

### How to Contribute

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

### Development Guidelines

- Code style: Black + flake8
- Testing: pytest
- Commit messages: Keep them concise and in English
- Documentation: Add appropriate documentation for new features

## 📄 License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Hiroshi Toyama** - [toyama0919@gmail.com](mailto:toyama0919@gmail.com)

## 🔗 Related Links

- [PyPI Package](https://pypi.org/project/vaiae/)
- [GitHub Repository](https://github.com/toyama0919/vaiae)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai)
- [Vertex AI Agent Builder](https://cloud.google.com/vertex-ai/docs/agent-builder)
