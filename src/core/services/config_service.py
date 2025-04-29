import os
import logging
import random # 랜덤 선택을 위해 추가
from pydantic import ValidationError
from typing import Optional, List, Set, Dict, Any # Set, Dict, Any 추가

from core.pydantic_models.config_settings import ConfigSettings
from .db_service import DbService # DbService import

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, db_service: DbService, profile_name: str = 'default'):
        """
        Initializes ConfigService using a DbService instance.

        Args:
            db_service: An instance of DbService to interact with the database.
            profile_name: The configuration profile to load (default: 'default').
        """
        self.db_service = db_service
        self.profile_name = profile_name
        self._settings: ConfigSettings = self._load_config()
        self._user_selected_gemini_key_id: Optional[int] = None # 사용자가 명시적으로 선택한 키 ID (메모리 관리)
        self._last_used_gemini_key: Optional[str] = None # 마지막으로 성공적으로 사용된 키 문자열 (메모리 관리)

    def _load_config(self) -> ConfigSettings:
        """
        Loads configuration from the database.
        Initial active Gemini key is NOT selected here. Selection happens in gemini_service.
        """
        logger.info(f"Loading configuration from database for profile '{self.profile_name}'...")
        try:
            # 1. Fetch application config from DB
            config_data = self.db_service.get_application_config(self.profile_name)

            if not config_data:
                logger.critical(f"Failed to load configuration from database for profile '{self.profile_name}'. Application cannot proceed.")
                raise ValueError(f"Configuration profile '{self.profile_name}' not found in database.")

            # --- 로깅 추가: DB에서 로드된 설정 데이터 확인 ---
            logger.info(f"Raw config data loaded from DB for profile '{self.profile_name}':")
            # 중요 설정값만 로깅 (API 키 제외)
            logged_data = {k: v for k, v in config_data.items() if 'api_key' not in k}
            logger.info(f"{logged_data}")
            # ---------------------------------------------

            # 2. Fetch *active* API keys from DB (just to check availability, not select)
            # This check is mainly for logging warnings if no keys are available initially.
            active_gemini_keys = self.db_service.get_active_api_keys('google')
            active_anthropic_keys = self.db_service.get_active_api_keys('anthropic')

            # --- Initial Gemini Key Selection REMOVED ---
            if not active_gemini_keys:
                logger.warning("No active Gemini API key found in DB. API calls will likely fail until a key is added/activated.")
            else:
                logger.info(f"Found {len(active_gemini_keys)} active Gemini keys. Key selection will occur during API call.")

            # Use the first active Anthropic key if available
            anthropic_key = active_anthropic_keys[0]['api_key'] if active_anthropic_keys else None
            if not anthropic_key: logger.warning("No active Anthropic API key found in DB.")

            # 3. Add the API keys (set to None initially) to the config data dictionary
            config_data['gemini_api_key'] = None # Placeholder, always None initially
            config_data['anthropic_api_key'] = anthropic_key

            # 4. Validate and create ConfigSettings model
            settings = ConfigSettings(**config_data)
            logger.info(f"Configuration loaded successfully from database for profile '{self.profile_name}'.")
            # --- 로깅 추가: Pydantic 모델 생성 후 설정 값 확인 ---
            logger.info("Validated ConfigSettings object created:")
            logger.info(f"  gemini_temperature: {settings.gemini_temperature}")
            # ... other relevant settings ...
            logger.info(f"  Initial gemini_api_key in settings object: {settings.gemini_api_key}") # Should log None
            # -------------------------------------------------
            return settings

        except ValidationError as e:
            logger.critical(f"Database configuration validation error: {e}. Using default settings (or failing).", exc_info=True)
            raise ValueError(f"Configuration validation failed: {e}")
        except Exception as e:
            logger.critical(f"Unexpected error loading config from database: {e}", exc_info=True)
            raise ValueError(f"Failed to load configuration from database: {e}")

    def update_settings(self, updated_settings: ConfigSettings) -> bool:
        """
        Updates the application configuration in the database and in memory.
        API keys are NOT saved via this method. User-selected key preference is not saved to DB.

        Args:
            updated_settings: A ConfigSettings object with the updated values.

        Returns:
            True if the update was successful, False otherwise.
        """
        logger.info(f"Attempting to update configuration in database for profile '{self.profile_name}'...")
        try:
            # Convert Pydantic model to dictionary for DB service
            # Exclude API keys as they are managed separately
            config_dict_to_save = updated_settings.model_dump(exclude={'gemini_api_key', 'anthropic_api_key'})

            # --- 로깅 추가: DB에 저장될 설정 데이터 확인 ---
            logger.info(f"Data being saved to DB for profile '{self.profile_name}':")
            logger.info(f"{config_dict_to_save}")
            # ---------------------------------------------

            # Call DbService to save the configuration (excluding API keys)
            success = self.db_service.save_application_config(self.profile_name, config_dict_to_save)

            if success:
                # Update in-memory settings only if DB save was successful
                # Keep the currently loaded API keys AND the user selection in the in-memory object
                current_anthropic_key = self._settings.anthropic_api_key # Keep potentially updated Anthropic key
                # Create a fresh copy from the validated input, then restore keys/selection
                self._settings = updated_settings.model_copy(deep=True)
                self._settings.gemini_api_key = self._last_used_gemini_key # Restore last used key string
                self._settings.anthropic_api_key = current_anthropic_key
                # User selection (_user_selected_gemini_key_id) remains as it is in memory.
                logger.info(f"Configuration updated successfully in database and memory for profile '{self.profile_name}'.")
                return True
            else:
                logger.error(f"Failed to save configuration update to database for profile '{self.profile_name}'.")
                return False

        except ValidationError as e:
            logger.error(f"Configuration update validation error: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating configuration: {e}", exc_info=True)
            return False

    def get_settings(self) -> ConfigSettings:
        """Returns the current configuration settings."""
        if not self._settings:
             logger.error("Configuration settings are not loaded.")
             self._settings = self._load_config() # Attempt to reload
        return self._settings

    def get_default_model_name(self, llm_type: str) -> str:
        """Gets the default model name for a given LLM type from settings."""
        settings = self.get_settings()
        if llm_type == "Gemini": return settings.gemini_default_model
        elif llm_type == "Claude": return settings.claude_default_model
        elif llm_type == "GPT": return settings.gpt_default_model
        else: logger.warning(f"Unknown LLM type '{llm_type}' requested for default model."); return ""

    def get_available_models(self, llm_type: str) -> List[str]:
        """Gets the list of available model names for a given LLM type from settings."""
        settings = self.get_settings()
        models = []
        if llm_type == "Gemini": models = settings.gemini_available_models
        elif llm_type == "Claude": models = settings.claude_available_models
        elif llm_type == "GPT": models = settings.gpt_available_models
        else: logger.warning(f"Unknown LLM type '{llm_type}' requested for available models.")
        return models if models is not None else []

    # --- User Selected Key Management ---
    def set_user_selected_gemini_key(self, key_id: Optional[int]):
        """Sets the user's preferred Gemini API key ID (managed in memory)."""
        if self._user_selected_gemini_key_id != key_id:
            logger.info(f"Setting user-selected Gemini Key ID to: {key_id}")
            self._user_selected_gemini_key_id = key_id
            # Optionally clear the last used key if a new preference is set? No, keep last used.
        else:
             logger.debug(f"User selected Gemini key ID is already {key_id}.")

    def get_user_selected_gemini_key_id(self) -> Optional[int]:
        """Gets the user's preferred Gemini API key ID."""
        return self._user_selected_gemini_key_id

    # --- Last Used Key Management ---
    def update_last_used_gemini_key(self, key_string: str):
        """
        Updates the last successfully used Gemini API key string in memory
        and updates the placeholder in the settings object.
        Called by gemini_service after a successful API call.
        """
        if self._last_used_gemini_key != key_string:
            logger.info(f"Updating last successfully used Gemini API key string.")
            self._last_used_gemini_key = key_string
            if self._settings:
                # Update the placeholder in the settings object for consistency/display if needed
                self._settings.gemini_api_key = key_string
        else:
            logger.debug("Attempted to update last used Gemini key, but it's the same.")

    def get_last_used_gemini_key_id(self) -> Optional[int]:
        """Gets the database ID of the last successfully used Gemini API key."""
        if self._last_used_gemini_key:
            try:
                # Fetch the ID from the database using the key string
                key_id = self.db_service.get_api_key_id(self._last_used_gemini_key)
                logger.debug(f"Retrieved ID for last used Gemini key: {key_id}")
                return key_id
            except Exception as e:
                logger.error(f"Error getting ID for last used Gemini key '{self._last_used_gemini_key[:4]}...': {e}")
                return None
        else:
            # Log if no key has been successfully used yet
            logger.debug("Cannot get last used Gemini key ID: No key has been successfully used yet.")
            return None

    # Renamed for clarity (was get_current_gemini_key_id)
    # def get_current_gemini_key_id(self) -> Optional[int]:
    #     """Gets the database ID of the currently configured Gemini API key."""
    #     # ... (old logic based on settings.gemini_api_key) ...
    #     # Now replaced by get_last_used_gemini_key_id and get_user_selected_gemini_key_id

    # Renamed for clarity (was update_current_gemini_key)
    # def update_current_gemini_key(self, new_key: str):
    #      # Now replaced by update_last_used_gemini_key
