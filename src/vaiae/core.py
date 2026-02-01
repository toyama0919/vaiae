import io
import sys

import pprint
import logging
from .logger import get_logger
from .util import Util


class Core:
    def __init__(
        self,
        yaml_file_path: str = None,
        profile: str = "default",
        debug: bool = False,
    ):
        self.project = None
        self.location = None
        self.staging_bucket = None
        self.logger = get_logger(level=logging.DEBUG if debug else logging.INFO)
        self.profile = profile
        self.config = None
        self._vertex_ai_initialized = False
        self._client = None

        # Find YAML file if not specified
        if yaml_file_path is None:
            yaml_file_path = Util.find_config_file()
            self.logger.debug(f"Using configuration file: {yaml_file_path}")

        self.yaml_file_path = yaml_file_path

        # Initialize from YAML (required)
        self._initialize_from_yaml(yaml_file_path, profile)

    def send_message(
        self,
        message: str,
        session_id: str = None,
        user_id: str = None,
        local: bool = False,
    ):
        from vertexai.preview import reasoning_engines

        self._ensure_vertex_ai_initialized()

        if local:
            # For local mode, get agent instance from current config
            agent_config = self.config.get("agent_engine", {})
            agent_instance = self._get_agent_instance_from_config(agent_config)
            self.app = reasoning_engines.AdkApp(
                agent=agent_instance,
                enable_tracing=True,
            )
        else:
            display_name = self.config.get("display_name")
            self.app = self.get_agent_engine(
                display_name=display_name,
            )

        # suppress output to stderr
        sys.stderr = io.StringIO()
        if session_id is None:
            session = self.app.create_session(user_id=user_id)
            if isinstance(session, dict):
                session_id = session.get("id")
            else:
                session_id = session.id

        query_params = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
        self.logger.debug(f"Sending message with params: {query_params}")
        events = self.app.stream_query(**query_params)

        for event in events:
            self.logger.debug(event)
            for part in event.get("content").get("parts", []):
                text = part.get("text")
                if text:
                    print(text)

    def get_agent_engine(self, display_name: str):
        """Get agent engine filtered by display name.

        Args:
            display_name (str): The display name to filter agent engines by.

        Returns:
            Agent engine object if found, None if no matching agent engine exists.
        """
        self._ensure_vertex_ai_initialized()

        agent_engine_list = list(
            self._client.agent_engines.list(
                config={"filter": f'display_name="{display_name}"'},
            )
        )
        return agent_engine_list[0] if agent_engine_list else None

    def list_agent_engine(self) -> list:
        """List all agent engines.

        Returns:
            list: List of all agent engine objects.
        """
        self._ensure_vertex_ai_initialized()
        self.logger.debug("Listing all agent engines...")
        agent_engine_list = list(self._client.agent_engines.list())
        return agent_engine_list

    def delete_agent_engine(
        self,
        name: str,
        force: bool = False,
        dry_run: bool = False,
    ) -> None:
        """Delete the gcpcost_advisor agent engine from Vertex AI.

        Args:
            name (str): Display name of the agent engine to delete.
            force (bool, optional): Force deletion even if the agent engine is in use.
                Defaults to False.
            dry_run (bool, optional): If True, performs validation without actually
                deleting the agent engine. Defaults to False.

        Returns:
            None

        Raises:
            Exception: If agent engine is not found or deletion fails.
        """
        self.logger.info("Deleting Gcpcost Advisor Agent...")
        self.logger.info(f"Display Name: [{name}]")
        self.logger.info(f"Force: [{force}]")

        try:
            # Get the agent engine instance by display name
            agent_engine = self.get_agent_engine(name)
            if not agent_engine:
                raise Exception(f"Agent engine with display name '{name}' not found")

            self.logger.info(f"Found agent engine: {agent_engine.api_resource.name}")

            # Delete the agent engine
            self.logger.info("Deleting agent engine...")
            if dry_run:
                self.logger.info("Dry run mode: not deleting the agent engine.")
                return
            agent_engine.delete(force=force)
            self.logger.info("Agent engine deleted successfully.")

        except Exception as e:
            self.logger.info(f"Error deleting agent engine: {e}")
            raise

    def create_or_update_from_yaml(self, dry_run: bool = False, **overrides) -> None:
        """Deploy or update an agent engine from YAML configuration.

        Args:
            dry_run (bool, optional): If True, performs validation without actually
                deploying or updating. Defaults to False.
            **overrides: Additional parameters to override YAML configuration values.

        Returns:
            None
        """
        # Use cached configuration from initialization
        config = self.config
        self.logger.info(f"Using profile: {self.profile}")

        # Apply overrides to config
        if overrides:
            config = self._apply_overrides(config, overrides)

        # Extract agent engine configuration
        agent_instance, config_dict = self._build_agent_engine_config(config)

        # Get display_name from config
        config_display_name = config.get("display_name")
        if not config_display_name:
            raise ValueError("display_name must be provided in YAML config")

        # Call existing create_or_update method
        self.create_or_update(agent_instance, config_dict, config_display_name, dry_run)

    def delete_agent_engine_from_yaml(
        self,
        force: bool = False,
        dry_run: bool = False,
    ) -> None:
        """Delete an agent engine using YAML configuration.

        Args:
            force (bool, optional): Force deletion even if the agent engine is in use.
                Defaults to False.
            dry_run (bool, optional): If True, performs validation without actually
                deleting the agent engine. Defaults to False.

        Returns:
            None
        """
        # Use cached configuration from initialization
        config = self.config
        self.logger.info(f"Using profile: {self.profile}")

        # Get display_name from config
        config_display_name = config.get("display_name")
        if not config_display_name:
            raise ValueError("display_name must be provided in YAML config")

        # Call existing delete_agent_engine method
        self.delete_agent_engine(config_display_name, force, dry_run)

    def _initialize_from_yaml(self, yaml_file_path: str, profile: str) -> None:
        """Initialize Vertex AI settings from YAML configuration.

        Args:
            yaml_file_path (str): Path to the YAML configuration file.
            profile (str): Profile name to use from YAML config.

        Returns:
            None
        """
        # Load configuration from YAML file with profile validation
        self.config = Util.load_yaml_config(yaml_file_path, profile)

        vertex_ai_config = self.config.get("vertex_ai", {})

        # Update instance variables with YAML values
        if vertex_ai_config.get("project"):
            self.project = vertex_ai_config.get("project")
        if vertex_ai_config.get("location"):
            self.location = vertex_ai_config.get("location")
        if vertex_ai_config.get("staging_bucket"):
            self.staging_bucket = vertex_ai_config.get("staging_bucket")

    def _ensure_vertex_ai_initialized(self) -> None:
        """Ensure Vertex AI is initialized (lazy initialization).

        Returns:
            None
        """
        if self._vertex_ai_initialized:
            return

        if self.project and self.location:
            import vertexai

            self.logger.debug("Initializing Vertex AI...")
            self.logger.debug(f"Project: [{self.project}]")
            self.logger.debug(f"Location: [{self.location}]")

            init_kwargs = {
                "project": self.project,
                "location": self.location,
            }

            if self.staging_bucket:
                self.logger.debug(f"Staging Bucket: [{self.staging_bucket}]")
                init_kwargs["staging_bucket"] = f"gs://{self.staging_bucket}"

            vertexai.init(**init_kwargs)
            # Create client for new API
            self._client = vertexai.Client(
                project=self.project,
                location=self.location,
            )
            self._vertex_ai_initialized = True

    def _apply_overrides(self, config: dict, overrides: dict) -> dict:
        """Apply override parameters to configuration.

        Args:
            config (dict): Original configuration dictionary.
            overrides (dict): Override parameters.

        Returns:
            dict: Updated configuration with overrides applied.
        """
        import copy

        updated_config = copy.deepcopy(config)

        # Apply overrides recursively
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if (
                    isinstance(value, dict)
                    and key in base_dict
                    and isinstance(base_dict[key], dict)
                ):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_update(updated_config, overrides)
        return updated_config

    def _get_agent_instance_from_config(self, agent_config: dict):
        """Get agent instance from agent configuration.

        Args:
            agent_config (dict): Agent engine configuration dictionary.

        Returns:
            object: Agent instance imported from the specified path.

        Raises:
            ValueError: If instance_path is not provided in configuration.
        """
        agent_instance_path = agent_config.get("instance_path")
        if agent_instance_path:
            # Import agent instance from string path
            return Util.import_from_string(agent_instance_path)
        else:
            # Error if instance_path is not provided
            raise ValueError(
                "instance_path must be provided in agent_engine configuration"
            )

    def _build_agent_engine_config(self, config: dict) -> tuple:
        """Build agent engine configuration from YAML config.

        Args:
            config (dict): Configuration dictionary loaded from YAML.

        Returns:
            tuple: (agent_instance, config_dict) ready for create/update with new API.
        """
        # Extract agent engine configuration
        agent_config = config.get("agent_engine", {})

        # Get agent instance using the reusable method
        agent_instance = self._get_agent_instance_from_config(agent_config)

        # Build the configuration dict according to new API
        config_dict = {
            "display_name": config.get("display_name"),
            "description": config.get("description"),
            "requirements": config.get("requirements", []),
            "extra_packages": config.get("extra_packages", []),
            "gcs_dir_name": config.get("gcs_dir_name"),
            "env_vars": config.get("env_vars", {}),
        }

        # Add staging_bucket if available
        if self.staging_bucket:
            config_dict["staging_bucket"] = f"gs://{self.staging_bucket}"

        # Add new optional parameters if provided
        if "labels" in config:
            config_dict["labels"] = config["labels"]
        if "build_options" in config:
            config_dict["build_options"] = config["build_options"]
        if "identity_type" in config:
            config_dict["identity_type"] = config["identity_type"]
        if "service_account" in config:
            config_dict["service_account"] = config["service_account"]
        if "min_instances" in config:
            config_dict["min_instances"] = config["min_instances"]
        if "max_instances" in config:
            config_dict["max_instances"] = config["max_instances"]
        if "resource_limits" in config:
            config_dict["resource_limits"] = config["resource_limits"]
        if "container_concurrency" in config:
            config_dict["container_concurrency"] = config["container_concurrency"]
        if "encryption_spec" in config:
            config_dict["encryption_spec"] = config["encryption_spec"]
        if "agent_framework" in config:
            config_dict["agent_framework"] = config["agent_framework"]

        # Private Service Connect configuration for VPC access
        if "psc_interface_config" in config:
            config_dict["psc_interface_config"] = config["psc_interface_config"]

        return agent_instance, config_dict

    def create_or_update(
        self,
        agent_instance,
        config_dict: dict,
        display_name: str,
        dry_run: bool = False,
    ) -> None:
        """Deploy or update an agent engine based on whether it already exists.

        Args:
            agent_instance: The agent instance to deploy.
            config_dict (dict): Configuration dictionary for the agent engine.
            display_name (str): Display name to check for existing agent engine.
            dry_run (bool, optional): If True, performs validation without actually
                deploying or updating. Defaults to False.

        Returns:
            None
        """
        self._ensure_vertex_ai_initialized()
        self.logger.info("Agent Instance: " + str(type(agent_instance).__name__))
        self.logger.info(
            "Agent Engine Config:\n" + pprint.pformat(config_dict, indent=2)
        )
        agent_engine = self.get_agent_engine(display_name)
        if agent_engine:
            self.logger.info(
                f"Found existing agent engine: {agent_engine.api_resource.name}"
            )
            if dry_run:
                self.logger.info("Dry run mode: not updating the agent engine.")
            else:
                self.logger.info("Updating agent engine...")
                self._client.agent_engines.update(
                    name=agent_engine.api_resource.name,
                    agent=agent_instance,
                    config=config_dict,
                )
        else:
            if dry_run:
                self.logger.info("Dry run mode: not deploying the agent engine.")
            else:
                self.logger.info("Deploying agent engine...")
                self._client.agent_engines.create(
                    agent=agent_instance,
                    config=config_dict,
                )
