import logging
from typing import List, Optional

from .db_service import DbService
from core.pydantic_models.ssh_config import SshConnectionConfig

logger = logging.getLogger(__name__)

class SshConfigService:
    """
    Manages SSH connection configurations using DbService.
    Provides methods for CRUD operations on SSH settings.
    """

    def __init__(self, db_service: DbService):
        """
        Initializes SshConfigService with a DbService instance.

        Args:
            db_service: An instance of DbService to interact with the database.
        """
        self.db_service = db_service
        logger.info("SshConfigService initialized.")

    def add_connection(self, config: SshConnectionConfig) -> Optional[int]:
        """
        Adds a new SSH connection configuration to the database.

        Args:
            config: An SshConnectionConfig object representing the connection details.

        Returns:
            The ID of the newly added connection, or None if failed.
        """
        try:
            # Ensure ID is None before adding
            config.id = None
            return self.db_service.add_ssh_connection(config)
        except Exception as e:
            logger.error(f"Error adding SSH connection '{config.alias}': {e}", exc_info=True)
            return None

    def get_connection(self, connection_id: int) -> Optional[SshConnectionConfig]:
        """
        Retrieves a specific SSH connection configuration by its ID.

        Args:
            connection_id: The ID of the connection to retrieve.

        Returns:
            An SshConnectionConfig object if found, otherwise None.
        """
        try:
            return self.db_service.get_ssh_connection(connection_id)
        except Exception as e:
            logger.error(f"Error retrieving SSH connection ID {connection_id}: {e}", exc_info=True)
            return None

    def list_connections(self) -> List[SshConnectionConfig]:
        """
        Retrieves a list of all saved SSH connection configurations, ordered by alias.

        Returns:
            A list of SshConnectionConfig objects.
        """
        try:
            return self.db_service.list_ssh_connections()
        except Exception as e:
            logger.error(f"Error listing SSH connections: {e}", exc_info=True)
            return []

    def update_connection(self, config: SshConnectionConfig) -> bool:
        """
        Updates an existing SSH connection configuration in the database.

        Args:
            config: An SshConnectionConfig object with the updated details (must include the ID).

        Returns:
            True if the update was successful, False otherwise.
        """
        if config.id is None:
            logger.error("Cannot update SSH connection: ID is missing in the config object.")
            return False
        try:
            return self.db_service.update_ssh_connection(config)
        except Exception as e:
            logger.error(f"Error updating SSH connection ID {config.id}: {e}", exc_info=True)
            return False

    def delete_connection(self, connection_id: int) -> bool:
        """
        Deletes an SSH connection configuration from the database.

        Args:
            connection_id: The ID of the connection to delete.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        try:
            return self.db_service.delete_ssh_connection(connection_id)
        except Exception as e:
            logger.error(f"Error deleting SSH connection ID {connection_id}: {e}", exc_info=True)
            return False

    def get_connection_by_alias(self, alias: str) -> Optional[SshConnectionConfig]:
        """
        Retrieves a specific SSH connection configuration by its alias.
        Note: This might be less efficient than getting by ID if not indexed.

        Args:
            alias: The alias of the connection to retrieve.

        Returns:
            An SshConnectionConfig object if found, otherwise None.
        """
        connections = self.list_connections()
        for conn in connections:
            if conn.alias == alias:
                return conn
        logger.warning(f"SSH connection with alias '{alias}' not found.")
        return None
