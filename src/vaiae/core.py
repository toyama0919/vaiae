from vertexai import agent_engines
import vertexai
from gcpcost.logger import get_logger
import pprint


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
