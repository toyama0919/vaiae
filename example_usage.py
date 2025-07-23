#!/usr/bin/env python3
"""
Example usage of YAML-based agent engine configuration.
"""

from src.vaiae.core import Core


def main():
    # Initialize Core with your GCP project settings
    core = Core(
        project="your-gcp-project-id",
        location="asia-northeast1",  # or your preferred location
        staging_bucket="your-staging-bucket"  # optional
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

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
