
import psycopg2
import logging
from typing import Optional, Dict, Any, List
import json # JSON 직렬화/역직렬화를 위해 추가
import datetime # 시간 관련 작업 위해 추가
from decimal import Decimal # NUMERIC 타입 처리를 위해 추가

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
    """Handles database connection and queries for application configuration and logging."""

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

    def _execute_query(self, query: str, params: Optional[tuple] = None, fetch_one: bool = False, fetch_all: bool = False, return_id: bool = False) -> Optional[Any]:
        """Executes a SQL query and returns the result."""
        if not self.connection or self.connection.closed:
            logger.error("Cannot execute query: Database connection is not active.")
            logger.info("Attempting to reconnect to the database...")
            self.connect()
            if not self.connection or self.connection.closed:
                 raise ConnectionError("Database connection lost and could not be re-established.")

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)

            if return_id:
                # INSERT ... RETURNING id
                result = cursor.fetchone()
                self.connection.commit()
                return result[0] if result else None
            elif fetch_one:
                # SELECT single value or row
                result = cursor.fetchone()
                if result and cursor.description:
                    # Return as dict if columns are available
                    colnames = [desc[0] for desc in cursor.description]
                    return dict(zip(colnames, result))
                elif result:
                    # Return single value if only one column
                    return result[0]
                else:
                    return None # No result found
            elif fetch_all:
                 # SELECT multiple rows/columns
                if cursor.description:
                    colnames = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(colnames, row)) for row in rows]
                else:
                    return [] # No results for SELECT
            else:
                # For non-SELECT queries (UPDATE, DELETE, simple INSERT without RETURNING)
                self.connection.commit()
                return cursor.rowcount # Return number of affected rows
        except psycopg2.Error as e:
            logger.error(f"Database query failed: {e}\nQuery: {query}\nParams: {params}", exc_info=True)
            if self.connection:
                self.connection.rollback() # Rollback on error
            # Re-raise specific errors if needed, otherwise return None or raise generic error
            raise e # Re-raise the psycopg2 error for more specific handling upstream
        finally:
            if cursor:
                cursor.close()

    def get_application_config(self, profile_name: str = 'default') -> Optional[Dict[str, Any]]:
        """Fetches application configuration for a given profile."""
        query = """
            SELECT * FROM application_config WHERE profile_name = %s;
        """
        try:
            # Use fetch_one=True as profile_name is unique
            result = self._execute_query(query, (profile_name,), fetch_one=True)
            if result and isinstance(result, dict):
                logger.info(f"Application config loaded for profile '{profile_name}'.")
                config_data = result
                # Convert NUMERIC from Decimal to float for Pydantic
                if 'gemini_temperature' in config_data and isinstance(config_data['gemini_temperature'], Decimal):
                    config_data['gemini_temperature'] = float(config_data['gemini_temperature'])
                return config_data
            else:
                logger.error(f"Application config not found for profile '{profile_name}'.")
                return None
        except psycopg2.Error as e:
             logger.error(f"Failed to get application config for profile '{profile_name}': {e}")
             return None # Return None on DB error

    def save_application_config(self, profile_name: str, config_data: Dict[str, Any]) -> bool:
        """
        Inserts or updates the application configuration for a given profile.
        Handles data type conversions for DB compatibility.
        """
        logger.info(f"Attempting to save application configuration for profile '{profile_name}'...")

        # Prepare data for insertion/update, handling potential missing keys and types
        # Convert sets/lists to lists for PostgreSQL TEXT[]
        allowed_extensions = list(config_data.get('allowed_extensions', []))
        excluded_dirs = list(config_data.get('excluded_dirs', []))
        default_ignore_list = list(config_data.get('default_ignore_list', []))
        gemini_available_models = list(config_data.get('gemini_available_models', []))
        claude_available_models = list(config_data.get('claude_available_models', []))
        gpt_available_models = list(config_data.get('gpt_available_models', []))

        # Ensure boolean values are correctly interpreted
        gemini_enable_thinking = bool(config_data.get('gemini_enable_thinking', True))
        gemini_enable_search = bool(config_data.get('gemini_enable_search', True))

        # Ensure numeric values are correctly interpreted, providing defaults
        try:
            gemini_temperature = float(config_data.get('gemini_temperature', 0.0))
        except (ValueError, TypeError):
            gemini_temperature = 0.0
        try:
            gemini_thinking_budget = int(config_data.get('gemini_thinking_budget', 24576))
        except (ValueError, TypeError):
            gemini_thinking_budget = 24576

        # SQL query using ON CONFLICT for upsert
        sql = """
            INSERT INTO application_config (
                profile_name, default_system_prompt, allowed_extensions, excluded_dirs,
                default_ignore_list, gemini_default_model, claude_default_model, gpt_default_model,
                gemini_available_models, claude_available_models, gpt_available_models,
                gemini_temperature, gemini_enable_thinking, gemini_thinking_budget, gemini_enable_search
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (profile_name) DO UPDATE SET
                default_system_prompt = EXCLUDED.default_system_prompt,
                allowed_extensions = EXCLUDED.allowed_extensions,
                excluded_dirs = EXCLUDED.excluded_dirs,
                default_ignore_list = EXCLUDED.default_ignore_list,
                gemini_default_model = EXCLUDED.gemini_default_model,
                claude_default_model = EXCLUDED.claude_default_model,
                gpt_default_model = EXCLUDED.gpt_default_model,
                gemini_available_models = EXCLUDED.gemini_available_models,
                claude_available_models = EXCLUDED.claude_available_models,
                gpt_available_models = EXCLUDED.gpt_available_models,
                gemini_temperature = EXCLUDED.gemini_temperature,
                gemini_enable_thinking = EXCLUDED.gemini_enable_thinking,
                gemini_thinking_budget = EXCLUDED.gemini_thinking_budget,
                gemini_enable_search = EXCLUDED.gemini_enable_search,
                updated_at = NOW();
        """
        params = (
            profile_name,
            config_data.get('default_system_prompt'),
            allowed_extensions,
            excluded_dirs,
            default_ignore_list,
            config_data.get('gemini_default_model'),
            config_data.get('claude_default_model'),
            config_data.get('gpt_default_model'),
            gemini_available_models,
            claude_available_models,
            gpt_available_models,
            gemini_temperature,
            gemini_enable_thinking,
            gemini_thinking_budget,
            gemini_enable_search
        )

        try:
            affected_rows = self._execute_query(sql, params)
            logger.info(f"Application configuration for profile '{profile_name}' saved successfully. Rows affected: {affected_rows}")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error saving application configuration for profile '{profile_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during config save for profile '{profile_name}': {e}")
            return False


    def get_active_api_key(self, provider: str) -> Optional[str]:
        """Fetches the first active API key for a given provider."""
        query = """
            SELECT api_key FROM api_keys
            WHERE provider = %s AND is_active = TRUE
            ORDER BY id
            LIMIT 1;
        """
        try:
            # Use fetch_one=True, but expect single value (api_key)
            result_dict = self._execute_query(query, (provider,), fetch_one=True)
            if result_dict and 'api_key' in result_dict:
                logger.info(f"Active API key found for provider '{provider}'.")
                return result_dict['api_key']
            else:
                logger.warning(f"No active API key found for provider '{provider}'.")
                return None
        except psycopg2.Error as e:
             logger.error(f"Failed to get active API key for provider '{provider}': {e}")
             return None # Return None on DB error

    def get_api_key_id(self, api_key_string: str) -> Optional[int]:
        """Fetches the ID of a given API key string."""
        if not api_key_string:
            return None
        query = "SELECT id FROM api_keys WHERE api_key = %s;"
        try:
            # Use fetch_one=True, expect single value (id)
            result_dict = self._execute_query(query, (api_key_string,), fetch_one=True)
            if result_dict and 'id' in result_dict:
                key_id = result_dict['id']
                logger.debug(f"Found API key ID for the provided key.")
                return key_id
            else:
                logger.warning(f"API key string not found in the database.")
                return None
        except psycopg2.Error as e:
            logger.error(f"Failed to get API key ID: {e}")
            return None

    def log_gemini_request(self, model_name: str, request_prompt: str, request_attachments: Optional[List[Dict[str, Any]]], api_key_id: Optional[int]) -> Optional[int]:
        """Logs the initial Gemini API request details and returns the log ID."""
        query = """
            INSERT INTO gemini_api_logs (model_name, request_prompt, request_attachments, api_key_id, request_timestamp)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """
        # Serialize attachments metadata to JSON string
        attachments_json = None
        if request_attachments:
            # Only keep metadata, remove large 'data' field
            metadata_attachments = []
            for att in request_attachments:
                meta_att = {k: v for k, v in att.items() if k != 'data'}
                metadata_attachments.append(meta_att)
            try:
                attachments_json = json.dumps(metadata_attachments)
            except TypeError as e:
                logger.error(f"Failed to serialize attachments to JSON: {e}")
                attachments_json = json.dumps([{"error": "Serialization failed"}])

        request_timestamp = datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware timestamp

        params = (model_name, request_prompt, attachments_json, api_key_id, request_timestamp)
        try:
            log_id = self._execute_query(query, params, return_id=True)
            logger.info(f"Logged Gemini request with ID: {log_id}")
            return log_id
        except psycopg2.Error as e:
            logger.error(f"Failed to log Gemini request: {e}")
            return None

    def update_gemini_log(self, log_id: int, response_text: Optional[str], response_xml: Optional[str], response_summary: Optional[str], error_message: Optional[str], elapsed_time_ms: Optional[int], token_count: Optional[int]):
        """Updates the Gemini API log record with response details."""
        if log_id is None:
            logger.error("Cannot update Gemini log: Invalid log_id provided.")
            return

        query = """
            UPDATE gemini_api_logs
            SET response_timestamp = %s,
                response_text = %s,
                response_xml = %s,
                response_summary = %s,
                error_message = %s,
                elapsed_time_ms = %s,
                token_count = %s
            WHERE id = %s;
        """
        response_timestamp = datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware timestamp
        params = (response_timestamp, response_text, response_xml, response_summary, error_message, elapsed_time_ms, token_count, log_id)

        try:
            affected_rows = self._execute_query(query, params)
            if affected_rows == 1:
                logger.info(f"Updated Gemini log record ID: {log_id}")
            else:
                 logger.warning(f"Attempted to update Gemini log ID: {log_id}, but no rows were affected (or more than 1).")
        except psycopg2.Error as e:
            logger.error(f"Failed to update Gemini log ID {log_id}: {e}")

    def cleanup_old_gemini_logs(self, days_to_keep: int = 7):
        """Deletes Gemini API log records older than the specified number of days."""
        if days_to_keep <= 0:
            logger.warning("Log cleanup skipped: days_to_keep must be positive.")
            return

        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_to_keep)
        query = """
            DELETE FROM gemini_api_logs
            WHERE request_timestamp < %s;
        """
        try:
            affected_rows = self._execute_query(query, (cutoff_date,))
            if affected_rows is not None and affected_rows > 0:
                logger.info(f"Cleaned up {affected_rows} old Gemini log records older than {cutoff_date.strftime('%Y-%m-%d')}.")
            else:
                logger.info("No old Gemini log records found to clean up.")
        except psycopg2.Error as e:
            logger.error(f"Failed to clean up old Gemini logs: {e}")


    # --- Methods for potential future use (Rate Limiting, API Key CRUD) ---
    # def get_model_rate_limit(self, model_name: str) -> Optional[Dict[str, Any]]: ...
    # def get_api_key_usage(self, api_key_id: int) -> Optional[Dict[str, Any]]: ...
    # def update_api_key_usage(...) -> bool: ...
    # def add_api_key(...) -> Optional[int]: ...
    # def update_api_key(...) -> bool: ...
    # def delete_api_key(...) -> bool: ...
    # def list_api_keys(...) -> List[Dict[str, Any]]: ...

    def __del__(self):
        """Ensure disconnection when the service object is destroyed."""
        self.disconnect()
