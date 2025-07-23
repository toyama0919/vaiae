#!/usr/bin/env python3
"""
Example usage of YAML-based agent engine configuration.
"""

from src.vaiae.core import Core


def main():
    # Initialize Core with YAML file and profile (required)
    core = Core(
        yaml_file_path=".agent-engine.yml",
        profile="default"
    )

    # Deploy or update agent engine from YAML configuration
    try:
        # Example 1: Basic usage with default profile
        core.create_or_update_from_yaml(
            yaml_file_path=".agent-engine.yml",
            profile="default",
            dry_run=True  # Set to False to actually deploy
        )
        print("Default profile loaded successfully!")

        # Example 2: Using development profile
        core.create_or_update_from_yaml(
            yaml_file_path=".agent-engine.yml",
            profile="development",
            dry_run=True
        )
        print("Development profile loaded successfully!")

        # Example 3: Using production profile
        core.create_or_update_from_yaml(
            yaml_file_path=".agent-engine.yml",
            profile="production",
            dry_run=True
        )
        print("Production profile loaded successfully!")

        # Example 4: Profile with overrides
        core.create_or_update_from_yaml(
            yaml_file_path=".agent-engine.yml",
            profile="development",
            dry_run=True,
            # Override YAML values
            description="Custom development description",
            env_vars={
                "GCPCOST_TABLE": "custom-dev-project.dataset.costs",
                "SLACK_WEBHOOK_URL": {"secret": "custom-dev-webhook", "version": "latest"}
            }
        )
        print("Development profile with overrides loaded successfully!")

        # Example 5: Delete agent engine using YAML profile
        core.delete_agent_engine_from_yaml(
            yaml_file_path=".agent-engine.yml",
            profile="development",
            force=False,
            dry_run=True  # Set to False to actually delete
        )
        print("Development profile agent engine deletion executed successfully!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
