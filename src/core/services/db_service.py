
import psycopg2
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# 데이터베이스 접속 정보 (요청에 따라 하드코딩)
DB_CONFIG = {
    "host": "postgresdb.lab.miraker.me",
    "user": "shacea",
    "password": "alfkzj9389",
    "port": 5333,
    "database": "duck_agent"
}

class DbService:
    """Handles database connection and queries for application configuration."""

    def __init__(self, db_config: Dict[str, Any] = DB_CONFIG):
        self.db_config = db_config
        self.connection = None
        self.connect()

    def connect(self):
        """Establishes a connection to the PostgreSQL database."""
        if self.connection and not self.connection.closed:
            return # Already connected

        try:
            logger.info(f"Connecting to database '{self.db_config['database']}' on {self.db_config['host']}...")
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("Database connection successful.")
        except psycopg2.Error as e:
            logger.critical(f"Database connection failed: {e}", exc_info=True)
            self.connection = None
            # Propagate the error to potentially stop the application
            raise ConnectionError(f"Failed to connect to the database: {e}")

    def disconnect(self):
        """Closes the database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Database connection closed.")
        self.connection = None

    def _execute_query(self, query: str, params: Optional[tuple] = None, fetch_one: bool = False) -> Optional[Any]:
        """Executes a SQL query and returns the result."""
        if not self.connection or self.connection.closed:
            logger.error("Cannot execute query: Database connection is not active.")
            # Try to reconnect
            logger.info("Attempting to reconnect to the database...")
            self.connect()
            if not self.connection or self.connection.closed:
                 raise ConnectionError("Database connection lost and could not be re-established.")


        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            if fetch_one:
                result = cursor.fetchone()
                return result[0] if result else None # Return single value if fetch_one
            else:
                # Check if the query returns columns (SELECT)
                if cursor.description:
                    colnames = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    # Convert rows to list of dictionaries
                    return [dict(zip(colnames, row)) for row in rows]
                else:
                    # For non-SELECT queries (INSERT, UPDATE, DELETE), commit changes
                    self.connection.commit()
                    return None # Or return rowcount if needed: cursor.rowcount
        except psycopg2.Error as e:
            logger.error(f"Database query failed: {e}\nQuery: {query}\nParams: {params}", exc_info=True)
            if self.connection:
                self.connection.rollback() # Rollback on error
            return None # Indicate failure
        finally:
            if cursor:
                cursor.close()

    def get_application_config(self, profile_name: str = 'default') -> Optional[Dict[str, Any]]:
        """Fetches application configuration for a given profile."""
        query = """
            SELECT * FROM application_config WHERE profile_name = %s;
        """
        result = self._execute_query(query, (profile_name,))
        if result and isinstance(result, list) and len(result) > 0:
            logger.info(f"Application config loaded for profile '{profile_name}'.")
            # Convert numeric temperature to float explicitly
            config_data = result[0]
            if 'gemini_temperature' in config_data and config_data['gemini_temperature'] is not None:
                try:
                    config_data['gemini_temperature'] = float(config_data['gemini_temperature'])
                except (ValueError, TypeError):
                     logger.warning(f"Could not convert gemini_temperature '{config_data['gemini_temperature']}' to float. Using default.")
                     config_data['gemini_temperature'] = 0.0 # Default fallback
            return config_data
        else:
            logger.error(f"Application config not found for profile '{profile_name}'.")
            return None

    def get_active_api_key(self, provider: str) -> Optional[str]:
        """Fetches the first active API key for a given provider."""
        query = """
            SELECT api_key FROM api_keys
            WHERE provider = %s AND is_active = TRUE
            ORDER BY id
            LIMIT 1;
        """
        result = self._execute_query(query, (provider,), fetch_one=True)
        if result:
            logger.info(f"Active API key found for provider '{provider}'.")
            return result
        else:
            logger.warning(f"No active API key found for provider '{provider}'.")
            return None

    # --- Methods for potential future use (Rate Limiting, Saving Config) ---
    # def get_model_rate_limit(self, model_name: str) -> Optional[Dict[str, Any]]: ...
    # def get_api_key_usage(self, api_key_id: int) -> Optional[Dict[str, Any]]: ...
    # def update_api_key_usage(...) -> bool: ...
    # def save_application_config(self, profile_name: str, config_data: Dict[str, Any]) -> bool: ...

    def __del__(self):
        """Ensure disconnection when the service object is destroyed."""
        self.disconnect()

