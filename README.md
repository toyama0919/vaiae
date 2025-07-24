# vaiae

[![PyPI version](https://badge.fury.io/py/vaiae.svg)](https://badge.fury.io/py/vaiae)
[![Build Status](https://github.com/toyama0919/vaiae/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/toyama0919/vaiae/actions/workflows/ci.yml)


Command Line utility for Vertex AI Agent Engines.

Supports python 3.8 and above.

## Features

- Deploy and manage Vertex AI Agent Engines
- YAML-based configuration for easy management
- Support for agent engine creation, updates, and deletion
- Interactive messaging with deployed agents

## Settings

```sh
export GOOGLE_CLOUD_PROJECT=your-gcp-project-id
export GOOGLE_CLOUD_LOCATION=asia-northeast1
export GOOGLE_STAGING_BUCKET=your-staging-bucket  # optional
```

* Support environment variables and service account authentication.

## YAML Configuration

Create a `.agent-engine.yml` file to define your agent engine configuration with multiple profiles:

```yaml
# Agent Engine Configuration with Profiles
default:
  # Vertex AI Configuration
  vertex_ai:
    project: "my-gcp-project"
    location: "asia-northeast1"
    staging_bucket: "xxxxxxxxxxxxxxxx"

  display_name: "xxxxxxxxxxxxx"
  description: "xxxxxx my-agent"
  gcs_dir_name: "gcpcost_advisor/0.3.1"

  agent_engine:
    instance_path: "xxxxx.xxxx.xxx.root_agent"

  env_vars:
    XXXXXXXXXX: "YYYYYYYYYYYYYYYY"
    SLACK_WEBHOOK_URL:
      secret: "slack-webhook-url"
      version: "latest"

  requirements:
    - "google-cloud-aiplatform[adk,agent_engines]==1.96.0"
    - "google-adk"
    - "slackweb"
    - "xxxxxxxx-0.0.1-py3-none-any.whl"

  extra_packages:
    - "xxxxxxxx-0.0.1-py3-none-any.whl"

development:
  # Vertex AI Configuration
  vertex_ai:
    project: "dev-project"
  ...

production:
  # Vertex AI Configuration
  vertex_ai:
    project: "prod-project"
    location: "asia-northeast1"
  ...
```

### Agent Instance Configuration

You have two options for configuring the agent engine:

#### Option 1: Using `instance_path` (Recommended)
Reference an existing agent instance by specifying its import path:

```yaml
agent_engine:
  instance_path: "gcpcost.agent.root_agent"
```

This will dynamically import and use the agent instance from `gcpcost.agent.root_agent`.

#### Option 2: Direct Configuration (Fallback)
Define agent parameters directly in the YAML file:

```yaml
agent_engine:
  name: "gcpcost_advisor"
  description: "Analyze the cost of GCP project and provide cost-saving advice."
  model: "gemini-2.5-pro"
  tools:
    - "gcpcost.tools.get_gcpcost"
    - "gcpcost.tools.get_gcpcost_by_products"
    - "gcpcost.tools.post_slack"
```

Tools can also be specified as import paths and will be dynamically imported.

## Examples

#### Deploy agent engine from YAML

```bash
$ vaiae deploy --dry-run
```

#### List deployed agent engines

```bash
$ vaiae list
```

#### Send message to agent

```bash
$ vaiae send -m "GCPのコストを分析してください" -d "gcpcost_advisor-0.3.1"
```

#### Delete agent engine

```bash
$ vaiae delete -n "gcpcost_advisor-0.3.1" --dry-run
```

## Python API Usage

```python
from src.vaiae.core import Core

# Initialize Core - Vertex AI settings will be loaded from YAML
core = Core()

# Or you can still provide fallback values
# core = Core(
#     project="fallback-project-id",
#     location="fallback-location",
#     staging_bucket="fallback-staging-bucket"
# )

# Example 1: Deploy using default profile
core.create_or_update_from_yaml(
    yaml_file_path=".agent-engine.yml",
    profile="default",
    dry_run=False
)

# Example 2: Deploy using development profile
core.create_or_update_from_yaml(
    yaml_file_path=".agent-engine.yml",
    profile="development",
    dry_run=False
)

# Example 3: Deploy using production profile
core.create_or_update_from_yaml(
    yaml_file_path=".agent-engine.yml",
    profile="production",
    dry_run=False
)

# Example 4: Deploy with profile and overrides
core.create_or_update_from_yaml(
    yaml_file_path=".agent-engine.yml",
    profile="development",
    dry_run=False,
    # Override specific values
    env_vars={
        "GCPCOST_TABLE": "custom-dev-project.dataset.costs"
    }
)

# Example 5: Delete agent engine using YAML profile
core.delete_agent_engine_from_yaml(
    yaml_file_path=".agent-engine.yml",
    profile="development",
    force=False,
    dry_run=False
)

# Send message to agent
core.send_message(
    message="GCPのコストを分析してください",
    display_name="gcpcost_advisor-0.3.1",
    user_id="user123"
)
```

### Profile Management

The YAML configuration supports multiple profiles for different environments:

- **default**: Base configuration
- **development**: Development environment settings
- **production**: Production environment settings
- **custom**: You can add any custom profile names

Each profile can have different:
- Display names
- Environment variables
- Package requirements
- GCS directory names
- Agent configurations

### Override Parameters

You can override any YAML configuration value using method parameters:

```python
core.create_or_update_from_yaml(
    yaml_file_path=".agent-engine.yml",
    profile="development",
    # Override any configuration
    description="Custom description",
    env_vars={"CUSTOM_VAR": "custom_value"},
    requirements=["additional-package"]
)
```

## Installation

```sh
pip install vaiae
```

## CI

### install test package

```
$ ./scripts/ci.sh install
```

### test

```
$ ./scripts/ci.sh run-test
```

flake8 and black and pytest.

### release pypi

```
$ ./scripts/ci.sh release
```

git tag and pypi release.
