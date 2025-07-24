from vertexai import agent_engines
import vertexai
from .logger import get_logger
import pprint
from .util import Util


class Core:
    def __init__(
        self,
        yaml_file_path: str = None,
        profile: str = "default",
    ):
        self.project = None
        self.location = None
        self.staging_bucket = None
        self.logger = get_logger()
        self.profile = profile
        self.config = None

        # Find YAML file if not specified
        if yaml_file_path is None:
            yaml_file_path = Util.find_config_file()
            self.logger.info(f"Using configuration file: {yaml_file_path}")

        self.yaml_file_path = yaml_file_path

        # Initialize from YAML (required)
        self._initialize_from_yaml(yaml_file_path, profile)

        # Initialize Vertex AI if all required parameters are provided
        self._initialize_vertex_ai()

    def send_message(
        self,
        message: str,
        display_name: str,
        session_id: str = None,
        user_id: str = None,
    ):
        self.app = self.get_agent_engine(
            display_name=display_name,
        )

        if session_id is None:
            session = self.app.create_session(user_id=user_id)
            session_id = session.get("id")

        events = self.app.stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        )

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
        agent_engine_list = list(
            agent_engines.list(
                filter=f'display_name="{display_name}"',
            )
        )
        return agent_engine_list[0] if agent_engine_list else None

    def list_agent_engine(self) -> list:
        """List all agent engines.

        Returns:
            list: List of all agent engine objects.
        """
        self.logger.info("Listing all agent engines...")
        agent_engine_list = list(agent_engines.list())
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

            self.logger.info(f"Found agent engine: {agent_engine.resource_name}")

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

    def create_or_update_from_yaml(
        self,
        dry_run: bool = False,
        **overrides
    ) -> None:
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
        agent_engine_config = self._build_agent_engine_config(config)

        # Get display_name from config
        config_display_name = config.get('display_name')
        if not config_display_name:
            raise ValueError("display_name must be provided in YAML config")

        # Call existing create_or_update method
        self.create_or_update(agent_engine_config, config_display_name, dry_run)

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
        config_display_name = config.get('display_name')
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

        vertex_ai_config = self.config.get('vertex_ai', {})

        # Update instance variables with YAML values
        if vertex_ai_config.get('project'):
            self.project = vertex_ai_config.get('project')
        if vertex_ai_config.get('location'):
            self.location = vertex_ai_config.get('location')
        if vertex_ai_config.get('staging_bucket'):
            self.staging_bucket = vertex_ai_config.get('staging_bucket')

    def _initialize_vertex_ai(self) -> None:
        """Initialize Vertex AI with current instance settings.

        Returns:
            None
        """
        if self.project and self.location:
            self.logger.info("Initializing Vertex AI...")
            self.logger.info(f"Project: [{self.project}]")
            self.logger.info(f"Location: [{self.location}]")

            init_kwargs = {
                "project": self.project,
                "location": self.location,
            }

            if self.staging_bucket:
                self.logger.info(f"Staging Bucket: [{self.staging_bucket}]")
                init_kwargs["staging_bucket"] = f"gs://{self.staging_bucket}"

            vertexai.init(**init_kwargs)

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
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_update(updated_config, overrides)
        return updated_config

    def _build_agent_engine_config(self, config: dict) -> dict:
        """Build agent engine configuration from YAML config.

        Args:
            config (dict): Configuration dictionary loaded from YAML.

        Returns:
            dict: Agent engine configuration ready for create/update.
        """
        # Extract agent engine configuration
        agent_config = config.get('agent_engine', {})

        # Get agent instance from string path
        agent_instance_path = agent_config.get('instance_path')
        if agent_instance_path:
            # Import agent instance from string path
            agent_instance = Util.import_from_string(agent_instance_path)
        else:
            # Error if instance_path is not provided
            raise ValueError("instance_path must be provided in agent_engine configuration")

        # Build the complete configuration
        agent_engine_config = {
            'agent_engine': agent_instance,
            'description': config.get('description'),
            'display_name': config.get('display_name'),
            'env_vars': config.get('env_vars', {}),
            'extra_packages': config.get('extra_packages', []),
            'gcs_dir_name': config.get('gcs_dir_name'),
            'requirements': config.get('requirements', []),
        }

        return agent_engine_config

    def create_or_update(
        self, agent_engine_config: dict, display_name: str, dry_run: bool = False
    ) -> None:
        """Deploy or update an agent engine based on whether it already exists.

        Args:
            agent_engine_config (dict): Configuration for the agent engine.
            display_name (str): Display name to check for existing agent engine.
            dry_run (bool, optional): If True, performs validation without actually
                deploying or updating. Defaults to False.

        Returns:
            None
        """
        self.logger.info(
            "Agent Engine Config:\n" + pprint.pformat(agent_engine_config, indent=2)
        )
        agent_engine = self.get_agent_engine(display_name)
        if agent_engine:
            self.logger.info(
                f"Found existing agent engine: {agent_engine.resource_name}"
            )
            if dry_run:
                self.logger.info("Dry run mode: not updating the agent engine.")
            else:
                agent_engines.update(
                    resource_name=agent_engine.resource_name,
                    **agent_engine_config,
                )
        else:
            if dry_run:
                self.logger.info("Dry run mode: not deploying the agent engine.")
            else:
                self.logger.info("Deploying agent engine...")
                agent_engines.create(**agent_engine_config)
