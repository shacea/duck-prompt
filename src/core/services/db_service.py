
import psycopg2
import logging
from typing import Optional, Dict, Any, List, Tuple # Tuple 추가
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
            logger.debug(f"Executing query: {query} with params: {params}") # 쿼리 실행 로깅 강화
            cursor.execute(query, params)

            if return_id:
                # INSERT ... RETURNING id
                result = cursor.fetchone()
                self.connection.commit()
                logger.debug(f"Query returned ID: {result[0] if result else None}")
                return result[0] if result else None
            elif fetch_one:
                # SELECT single value or row
                result = cursor.fetchone()
                if result and cursor.description:
                    # Return as dict if columns are available
                    colnames = [desc[0] for desc in cursor.description]
                    row_dict = dict(zip(colnames, result))
                    logger.debug(f"Query fetched one row: {row_dict}")
                    return row_dict
                elif result:
                    # Return single value if only one column
                    logger.debug(f"Query fetched one value: {result[0]}")
                    return result[0]
                else:
                    logger.debug("Query fetched no results (fetch_one).")
                    return None # No result found
            elif fetch_all:
                 # SELECT multiple rows/columns
                if cursor.description:
                    colnames = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    results_list = [dict(zip(colnames, row)) for row in rows]
                    logger.debug(f"Query fetched {len(results_list)} rows.")
                    return results_list
                else:
                    logger.debug("Query fetched no results (fetch_all).")
                    return [] # No results for SELECT
            else:
                # For non-SELECT queries (UPDATE, DELETE, simple INSERT without RETURNING)
                affected_rows = cursor.rowcount
                self.connection.commit()
                logger.debug(f"Query executed successfully. Rows affected: {affected_rows}")
                return affected_rows # Return number of affected rows
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
        Handles data type conversions for DB compatibility. Excludes API keys.
        """
        logger.info(f"Attempting to save application configuration for profile '{profile_name}'...")

        # Prepare data for insertion/update, handling potential missing keys and types
        allowed_extensions = list(config_data.get('allowed_extensions', []))
        excluded_dirs = list(config_data.get('excluded_dirs', []))
        default_ignore_list = list(config_data.get('default_ignore_list', []))
        gemini_available_models = list(config_data.get('gemini_available_models', []))
        claude_available_models = list(config_data.get('claude_available_models', []))
        gpt_available_models = list(config_data.get('gpt_available_models', []))

        gemini_enable_thinking = bool(config_data.get('gemini_enable_thinking', True))
        gemini_enable_search = bool(config_data.get('gemini_enable_search', True))

        try: gemini_temperature = float(config_data.get('gemini_temperature', 0.0))
        except (ValueError, TypeError): gemini_temperature = 0.0
        try: gemini_thinking_budget = int(config_data.get('gemini_thinking_budget', 24576))
        except (ValueError, TypeError): gemini_thinking_budget = 24576

        # SQL query using ON CONFLICT for upsert (API keys excluded)
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
            profile_name, config_data.get('default_system_prompt'), allowed_extensions, excluded_dirs,
            default_ignore_list, config_data.get('gemini_default_model'), config_data.get('claude_default_model'),
            config_data.get('gpt_default_model'), gemini_available_models, claude_available_models,
            gpt_available_models, gemini_temperature, gemini_enable_thinking, gemini_thinking_budget,
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

    # --- API Key Management ---

    def get_active_api_key(self, provider: str) -> Optional[str]:
        """Fetches the first active API key string for a given provider."""
        keys = self.get_active_api_keys(provider)
        return keys[0]['api_key'] if keys else None

    def get_active_api_keys(self, provider: str) -> List[Dict[str, Any]]:
        """Fetches all active API keys for a given provider, ordered by ID."""
        query = """
            SELECT id, api_key, description, is_active FROM api_keys
            WHERE provider = %s AND is_active = TRUE
            ORDER BY id;
        """
        try:
            result = self._execute_query(query, (provider,), fetch_all=True)
            if result:
                logger.info(f"Found {len(result)} active API key(s) for provider '{provider}'.")
                return result
            else:
                logger.warning(f"No active API keys found for provider '{provider}'.")
                return []
        except psycopg2.Error as e:
             logger.error(f"Failed to get active API keys for provider '{provider}': {e}")
             return []

    def get_active_api_keys_with_usage(self, provider: str) -> List[Dict[str, Any]]:
        """
        Fetches all active API keys for a given provider along with their current daily usage,
        ordered by ID. Calculates effective daily usage considering the reset window.
        """
        query = """
            SELECT
                ak.id, ak.api_key, ak.description, ak.is_active,
                COALESCE(usage.calls_this_day, 0) AS raw_calls_this_day,
                usage.day_start_timestamp
            FROM api_keys ak
            LEFT JOIN api_key_usage usage ON ak.id = usage.api_key_id
            WHERE ak.provider = %s AND ak.is_active = TRUE
            ORDER BY ak.id;
        """
        try:
            results = self._execute_query(query, (provider,), fetch_all=True)
            if not results:
                logger.warning(f"No active API keys found for provider '{provider}'.")
                return []

            logger.info(f"Found {len(results)} active API key(s) with usage info for provider '{provider}'.")
            now = datetime.datetime.now(datetime.timezone.utc)
            current_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Calculate effective daily usage
            for key_info in results:
                raw_calls = key_info.get('raw_calls_this_day', 0)
                day_start = key_info.get('day_start_timestamp')

                # Ensure day_start is timezone-aware if it exists
                if day_start and day_start.tzinfo is None:
                    day_start = day_start.replace(tzinfo=datetime.timezone.utc)
                    key_info['day_start_timestamp'] = day_start # Update dict if needed

                # Calculate effective calls for today
                if day_start and day_start < current_day_start:
                    key_info['calls_this_day'] = 0 # Day has reset
                    logger.debug(f"Key ID {key_info['id']}: Day window reset. Effective calls_this_day = 0")
                else:
                    key_info['calls_this_day'] = raw_calls
                    logger.debug(f"Key ID {key_info['id']}: Within current day window. Effective calls_this_day = {raw_calls}")

                # Remove raw count if no longer needed
                # del key_info['raw_calls_this_day']

            return results

        except psycopg2.Error as e:
             logger.error(f"Failed to get active API keys with usage for provider '{provider}': {e}")
             return []
        except Exception as e:
            logger.error(f"Unexpected error getting active API keys with usage for '{provider}': {e}", exc_info=True)
            return []


    def list_api_keys(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all API keys, optionally filtered by provider."""
        if provider:
            query = "SELECT id, api_key, provider, description, is_active FROM api_keys WHERE provider = %s ORDER BY provider, id;"
            params = (provider,)
        else:
            query = "SELECT id, api_key, provider, description, is_active FROM api_keys ORDER BY provider, id;"
            params = None
        try:
            result = self._execute_query(query, params, fetch_all=True)
            logger.info(f"Listed {len(result)} API keys" + (f" for provider '{provider}'." if provider else "."))
            return result if result else []
        except psycopg2.Error as e:
            logger.error(f"Failed to list API keys: {e}")
            return []

    def add_api_key(self, provider: str, api_key: str, description: Optional[str] = None) -> Optional[int]:
        """Adds a new API key to the database."""
        if not provider or not api_key:
            logger.error("Cannot add API key: Provider and API key string are required.")
            return None
        query = """
            INSERT INTO api_keys (provider, api_key, description, is_active)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """
        params = (provider, api_key, description, True) # Add as active by default
        try:
            key_id = self._execute_query(query, params, return_id=True)
            logger.info(f"Added new API key with ID: {key_id} for provider '{provider}'.")
            return key_id
        except psycopg2.IntegrityError as e:
             logger.error(f"Failed to add API key for '{provider}': Key likely already exists. {e}")
             return None
        except psycopg2.Error as e:
            logger.error(f"Failed to add API key for '{provider}': {e}")
            return None

    def update_api_key(self, key_id: int, description: Optional[str] = None, is_active: Optional[bool] = None) -> bool:
        """Updates the description or active status of an API key."""
        if description is None and is_active is None:
            logger.warning(f"No update provided for API key ID {key_id}.")
            return False

        set_clauses = []
        params = []
        if description is not None:
            set_clauses.append("description = %s")
            params.append(description)
        if is_active is not None:
            set_clauses.append("is_active = %s")
            params.append(is_active)

        query = f"""
            UPDATE api_keys
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = %s;
        """
        params.append(key_id)

        try:
            affected_rows = self._execute_query(query, tuple(params))
            if affected_rows == 1:
                logger.info(f"API key ID {key_id} updated successfully.")
                return True
            else:
                logger.warning(f"API key ID {key_id} not found or no changes made.")
                return False
        except psycopg2.Error as e:
            logger.error(f"Failed to update API key ID {key_id}: {e}")
            return False

    def delete_api_key(self, key_id: int) -> bool:
        """Deletes an API key from the database."""
        query = "DELETE FROM api_keys WHERE id = %s;"
        try:
            affected_rows = self._execute_query(query, (key_id,))
            if affected_rows == 1:
                logger.info(f"API key ID {key_id} deleted successfully.")
                return True
            else:
                logger.warning(f"API key ID {key_id} not found for deletion.")
                return False
        except psycopg2.Error as e:
            logger.error(f"Failed to delete API key ID {key_id}: {e}")
            return False

    def get_api_key_id(self, api_key_string: str) -> Optional[int]:
        """Fetches the ID of a given API key string."""
        if not api_key_string: return None
        query = "SELECT id FROM api_keys WHERE api_key = %s;"
        try:
            result_dict = self._execute_query(query, (api_key_string,), fetch_one=True)
            return result_dict['id'] if result_dict and 'id' in result_dict else None
        except psycopg2.Error as e:
            logger.error(f"Failed to get API key ID: {e}")
            return None

    # --- Gemini Log Management ---

    def log_gemini_request(self, model_name: str, request_prompt: str, request_attachments: Optional[List[Dict[str, Any]]], api_key_id: Optional[int]) -> Optional[int]:
        """Logs the initial Gemini API request details and returns the log ID."""
        query = """
            INSERT INTO gemini_api_logs (model_name, request_prompt, request_attachments, api_key_id, request_timestamp)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """
        attachments_json = None
        if request_attachments:
            metadata_attachments = [{k: v for k, v in att.items() if k != 'data'} for att in request_attachments]
            try: attachments_json = json.dumps(metadata_attachments)
            except TypeError as e:
                logger.error(f"Failed to serialize attachments to JSON: {e}")
                attachments_json = json.dumps([{"error": "Serialization failed"}])

        request_timestamp = datetime.datetime.now(datetime.timezone.utc)
        params = (model_name, request_prompt, attachments_json, api_key_id, request_timestamp)
        try:
            log_id = self._execute_query(query, params, return_id=True)
            logger.info(f"Logged Gemini request with ID: {log_id}")
            return log_id
        except psycopg2.Error as e:
            logger.error(f"Failed to log Gemini request: {e}")
            return None

    def update_gemini_log(self, log_id: int, response_text: Optional[str] = None, response_xml: Optional[str] = None, response_summary: Optional[str] = None, error_message: Optional[str] = None, elapsed_time_ms: Optional[int] = None, token_count: Optional[int] = None):
        """Updates the Gemini API log record with response details. Only updates non-None fields."""
        if log_id is None:
            logger.error("Cannot update Gemini log: Invalid log_id provided.")
            return

        update_fields = []
        params = []

        if response_text is not None: update_fields.append("response_text = %s"); params.append(response_text)
        if response_xml is not None: update_fields.append("response_xml = %s"); params.append(response_xml)
        if response_summary is not None: update_fields.append("response_summary = %s"); params.append(response_summary)
        if error_message is not None: update_fields.append("error_message = %s"); params.append(error_message)
        if elapsed_time_ms is not None: update_fields.append("elapsed_time_ms = %s"); params.append(elapsed_time_ms)
        if token_count is not None: update_fields.append("token_count = %s"); params.append(token_count)

        if not update_fields:
            logger.info(f"No fields to update for Gemini log ID: {log_id}")
            return

        # Always update response_timestamp
        update_fields.append("response_timestamp = %s")
        params.append(datetime.datetime.now(datetime.timezone.utc))
        params.append(log_id) # Add log_id for WHERE clause

        query = f"""
            UPDATE gemini_api_logs
            SET {', '.join(update_fields)}
            WHERE id = %s;
        """

        try:
            affected_rows = self._execute_query(query, tuple(params))
            if affected_rows == 1: logger.info(f"Updated Gemini log record ID: {log_id}")
            else: logger.warning(f"Attempted to update Gemini log ID: {log_id}, but no rows were affected (or more than 1).")
        except psycopg2.Error as e:
            logger.error(f"Failed to update Gemini log ID {log_id}: {e}")

    def cleanup_old_gemini_logs(self, days_to_keep: int = 7):
        """Deletes Gemini API log records older than the specified number of days."""
        if days_to_keep <= 0:
            logger.warning("Log cleanup skipped: days_to_keep must be positive.")
            return

        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_to_keep)
        query = "DELETE FROM gemini_api_logs WHERE request_timestamp < %s;"
        try:
            affected_rows = self._execute_query(query, (cutoff_date,))
            if affected_rows is not None and affected_rows > 0:
                logger.info(f"Cleaned up {affected_rows} old Gemini log records older than {cutoff_date.strftime('%Y-%m-%d')}.")
            else: logger.info("No old Gemini log records found to clean up.")
        except psycopg2.Error as e:
            logger.error(f"Failed to clean up old Gemini logs: {e}")

    # --- Rate Limit and Usage Tracking ---

    def update_api_key_usage(self, api_key_id: int):
        """Updates the usage statistics for a given API key ID using UPSERT."""
        if api_key_id is None:
            logger.warning("Cannot update API key usage: api_key_id is None.")
            return

        logger.info(f"Updating API key usage for key ID: {api_key_id}")
        now = datetime.datetime.now(datetime.timezone.utc)
        current_minute_start = now.replace(second=0, microsecond=0)
        current_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # --- SQL Query using ON CONFLICT DO UPDATE ---
        # This query attempts to insert a new row or update an existing one based on api_key_id.
        # It correctly handles the logic for incrementing counts or resetting them
        # based on whether the current minute/day window has passed.
        query = """
            INSERT INTO api_key_usage (
                api_key_id,
                last_api_call_timestamp,
                minute_start_timestamp,
                calls_this_minute,
                day_start_timestamp,
                calls_this_day
            )
            VALUES (
                %(key_id)s, %(now)s, %(minute_start)s, 1, %(day_start)s, 1
            )
            ON CONFLICT (api_key_id) DO UPDATE SET
                last_api_call_timestamp = %(now)s,

                -- Update minute count and timestamp
                calls_this_minute = CASE
                    -- If the recorded minute start is before the current minute start, reset count to 1
                    WHEN api_key_usage.minute_start_timestamp IS NULL OR api_key_usage.minute_start_timestamp < %(minute_start)s THEN 1
                    -- Otherwise, increment the existing count for the current minute
                    ELSE api_key_usage.calls_this_minute + 1
                END,
                minute_start_timestamp = CASE
                    -- If the recorded minute start is before the current minute start, update timestamp
                    WHEN api_key_usage.minute_start_timestamp IS NULL OR api_key_usage.minute_start_timestamp < %(minute_start)s THEN %(minute_start)s
                    -- Otherwise, keep the existing timestamp for the current minute
                    ELSE api_key_usage.minute_start_timestamp
                END,

                -- Update day count and timestamp
                calls_this_day = CASE
                    -- If the recorded day start is before the current day start, reset count to 1
                    WHEN api_key_usage.day_start_timestamp IS NULL OR api_key_usage.day_start_timestamp < %(day_start)s THEN 1
                    -- Otherwise, increment the existing count for the current day
                    ELSE api_key_usage.calls_this_day + 1
                END,
                day_start_timestamp = CASE
                    -- If the recorded day start is before the current day start, update timestamp
                    WHEN api_key_usage.day_start_timestamp IS NULL OR api_key_usage.day_start_timestamp < %(day_start)s THEN %(day_start)s
                    -- Otherwise, keep the existing timestamp for the current day
                    ELSE api_key_usage.day_start_timestamp
                END,

                -- Always update the updated_at timestamp
                updated_at = NOW();
        """
        params = {
            'key_id': api_key_id,
            'now': now,
            'minute_start': current_minute_start,
            'day_start': current_day_start
        }

        try:
            affected_rows = self._execute_query(query, params)
            # UPSERT returns 1 if inserted, 2 if updated in some PostgreSQL versions,
            # or potentially 0 or 1 depending on exact behavior and version.
            # Checking for None or error is more reliable than specific row counts.
            if affected_rows is not None: # Check if query execution was successful (returned row count or None on error)
                logger.info(f"API key usage updated successfully for key ID: {api_key_id}. (Affected rows: {affected_rows})")
            else:
                 logger.error(f"API key usage update query might have failed for key ID {api_key_id} (returned None).")

        except psycopg2.Error as e:
            logger.error(f"Failed to update API key usage for key ID {api_key_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred during API key usage update for key ID {api_key_id}: {e}", exc_info=True)


    def get_model_rate_limit(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Fetches the default rate limit information for a specific model."""
        query = "SELECT rpm_limit, daily_limit FROM model_rate_limits WHERE model_name = %s;"
        try:
            result = self._execute_query(query, (model_name,), fetch_one=True)
            if result:
                logger.info(f"Rate limit found for model '{model_name}': RPM={result.get('rpm_limit')}, Daily={result.get('daily_limit')}")
                return result
            else:
                logger.warning(f"No rate limit information found for model '{model_name}'.")
                return None
        except psycopg2.Error as e:
            logger.error(f"Failed to get rate limit for model '{model_name}': {e}")
            return None

    def get_api_key_usage(self, api_key_id: int) -> Optional[Dict[str, Any]]:
        """Fetches the current usage statistics for a specific API key ID."""
        if api_key_id is None: return None
        query = """
            SELECT calls_this_minute, minute_start_timestamp, calls_this_day, day_start_timestamp
            FROM api_key_usage
            WHERE api_key_id = %s;
        """
        try:
            result = self._execute_query(query, (api_key_id,), fetch_one=True)
            if result:
                logger.info(f"Usage found for API key ID {api_key_id}.")
                # Ensure timestamps are timezone-aware if they aren't already
                if result.get('minute_start_timestamp') and result['minute_start_timestamp'].tzinfo is None:
                    result['minute_start_timestamp'] = result['minute_start_timestamp'].replace(tzinfo=datetime.timezone.utc)
                if result.get('day_start_timestamp') and result['day_start_timestamp'].tzinfo is None:
                    result['day_start_timestamp'] = result['day_start_timestamp'].replace(tzinfo=datetime.timezone.utc)
                return result
            else:
                logger.info(f"No usage record found for API key ID {api_key_id}. Assuming 0 usage.")
                # Return default zero usage if no record exists
                return {
                    'calls_this_minute': 0, 'minute_start_timestamp': None,
                    'calls_this_day': 0, 'day_start_timestamp': None
                }
        except psycopg2.Error as e:
            logger.error(f"Failed to get usage for API key ID {api_key_id}: {e}")
            return None

    def is_key_rate_limited(self, api_key_id: int, model_name: str) -> Tuple[bool, str]:
        """
        Checks if the API key is currently rate-limited for the given model.

        Returns:
            Tuple[bool, str]: (is_limited, reason_message)
                              is_limited is True if the key is rate-limited, False otherwise.
                              reason_message explains why it's limited if applicable.
        """
        if api_key_id is None:
            return True, "API Key ID is missing."

        try:
            # 1. Get model's default rate limits
            rate_limit_info = self.get_model_rate_limit(model_name)
            if not rate_limit_info:
                logger.warning(f"No rate limit info found for model '{model_name}'. Assuming not limited.")
                return False, "Rate limit info not found."
            rpm_limit = rate_limit_info.get('rpm_limit')
            daily_limit = rate_limit_info.get('daily_limit')

            # 2. Get current usage for the API key
            usage_info = self.get_api_key_usage(api_key_id)
            if not usage_info:
                logger.info(f"No usage info found for API key ID {api_key_id}. Assuming not limited.")
                return False, "No usage info found."

            calls_this_minute = usage_info.get('calls_this_minute', 0)
            minute_start = usage_info.get('minute_start_timestamp')
            calls_this_day = usage_info.get('calls_this_day', 0)
            day_start = usage_info.get('day_start_timestamp')
            now = datetime.datetime.now(datetime.timezone.utc)
            current_minute_start = now.replace(second=0, microsecond=0)
            current_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)


            # 3. Check RPM limit
            if rpm_limit is not None and rpm_limit > 0:
                # Check if the minute window has reset
                current_minute_call_count = calls_this_minute
                if minute_start and minute_start < current_minute_start:
                     current_minute_call_count = 0 # Minute window has passed, effective count for *next* call is 0
                     logger.debug(f"RPM Check: Minute window reset for key {api_key_id}. Current count considered 0.")

                # Check if adding one more call would exceed the limit
                if current_minute_call_count >= rpm_limit:
                    reason = f"RPM limit ({rpm_limit}) reached or exceeded (current minute calls: {current_minute_call_count})."
                    logger.warning(f"Rate limit check failed for key ID {api_key_id}: {reason}")
                    return True, reason

            # 4. Check Daily limit
            if daily_limit is not None and daily_limit > 0:
                # Check if the day window has reset
                current_day_call_count = calls_this_day
                if day_start and day_start < current_day_start:
                    current_day_call_count = 0 # Day window has passed, effective count for *next* call is 0
                    logger.debug(f"Daily Check: Day window reset for key {api_key_id}. Current count considered 0.")

                # Check if adding one more call would exceed the limit
                if current_day_call_count >= daily_limit:
                    reason = f"Daily limit ({daily_limit}) reached or exceeded (current day calls: {current_day_call_count})."
                    logger.warning(f"Rate limit check failed for key ID {api_key_id}: {reason}")
                    return True, reason

            logger.debug(f"Rate limit check passed for key ID {api_key_id} and model '{model_name}'.")
            return False, "Rate limit OK."

        except Exception as e:
            logger.error(f"Error checking rate limit for key ID {api_key_id}: {e}", exc_info=True)
            # Assume limited in case of error to be safe
            return True, f"Error during rate limit check: {e}"


    def __del__(self):
        """Ensure disconnection when the service object is destroyed."""
        self.disconnect()
