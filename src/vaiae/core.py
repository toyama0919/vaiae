from vertexai import agent_engines
import vertexai
from gcpcost.logger import get_logger
import pprint
from .util import Util


class Core:
    def __init__(
        self,
        project: str = None,
        location: str = None,
        staging_bucket: str = None,
    ):
        self.project = project
        self.location = location
        self.logger = get_logger()
        # Initialize Vertex AI if all required parameters are provided
        if self.project and self.location:
            self.logger.info("Initializing Vertex AI...")
            self.logger.info(f"Project: [{self.project}]")
            self.logger.info(f"Location: [{self.location}]")

            init_kwargs = {
                "project": self.project,
                "location": self.location,
            }

            if staging_bucket:
                self.logger.info(f"Staging Bucket: [{staging_bucket}]")
                init_kwargs["staging_bucket"] = f"gs://{staging_bucket}"

            vertexai.init(**init_kwargs)

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
        yaml_file_path: str,
        profile: str = "default",
        dry_run: bool = False,
        **overrides
    ) -> None:
        """Deploy or update an agent engine from YAML configuration.

        Args:
            yaml_file_path (str): Path to the YAML configuration file.
            profile (str, optional): Profile name to use from YAML config. Defaults to "default".
            dry_run (bool, optional): If True, performs validation without actually
                deploying or updating. Defaults to False.
            **overrides: Additional parameters to override YAML configuration values.

        Returns:
            None
        """
        # Load configuration from YAML file
        full_config = Util.load_yaml_config(yaml_file_path)

        # Extract profile configuration
        if profile not in full_config:
            available_profiles = list(full_config.keys())
            raise ValueError(f"Profile '{profile}' not found in YAML config. Available profiles: {available_profiles}")

        config = full_config[profile]
        self.logger.info(f"Using profile: {profile}")

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
            # Fallback: create LlmAgent instance if no instance_path is provided
            from vertexai.generative_models import LlmAgent

            # Resolve tools from string paths if provided
            tools = []
            tool_paths = agent_config.get('tools', [])
            for tool_path in tool_paths:
                if isinstance(tool_path, str):
                    try:
                        tool = Util.import_from_string(tool_path)
                        tools.append(tool)
                    except ImportError as e:
                        self.logger.warning(f"Could not import tool '{tool_path}': {e}")
                else:
                    # If it's already an object, use it as-is
                    tools.append(tool_path)

            agent_instance = LlmAgent(
                name=agent_config.get('name'),
                description=agent_config.get('description'),
                model=agent_config.get('model'),
                instruction=agent_config.get('instruction', ''),
                global_instruction=agent_config.get('global_instruction', ''),
                tools=tools,
                disallow_transfer_to_parent=agent_config.get('disallow_transfer_to_parent', False),
                disallow_transfer_to_peers=agent_config.get('disallow_transfer_to_peers', False),
                include_contents=agent_config.get('include_contents', 'default'),
            )

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
