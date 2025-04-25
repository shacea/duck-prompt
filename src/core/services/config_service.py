
import os
import logging
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

    def _load_config(self) -> ConfigSettings:
        """Loads configuration from the database."""
        logger.info(f"Loading configuration from database for profile '{self.profile_name}'...")
        try:
            # 1. Fetch application config from DB
            config_data = self.db_service.get_application_config(self.profile_name)

            if not config_data:
                logger.critical(f"Failed to load configuration from database for profile '{self.profile_name}'. Application cannot proceed.")
                raise ValueError(f"Configuration profile '{self.profile_name}' not found in database.")

            # 2. Fetch *active* API keys from DB (get the first active one for now)
            gemini_keys = self.db_service.get_active_api_keys('google')
            anthropic_keys = self.db_service.get_active_api_keys('anthropic')

            # Use the first active key if available
            gemini_key = gemini_keys[0]['api_key'] if gemini_keys else None
            anthropic_key = anthropic_keys[0]['api_key'] if anthropic_keys else None

            if not gemini_key: logger.warning("No active Gemini API key found in DB.")
            if not anthropic_key: logger.warning("No active Anthropic API key found in DB.")

            # 3. Add the selected API keys to the config data dictionary
            config_data['gemini_api_key'] = gemini_key
            config_data['anthropic_api_key'] = anthropic_key

            # 4. Validate and create ConfigSettings model
            settings = ConfigSettings(**config_data)
            logger.info(f"Configuration loaded successfully from database for profile '{self.profile_name}'.")
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
        API keys are NOT saved via this method.

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

            # Call DbService to save the configuration (excluding API keys)
            success = self.db_service.save_application_config(self.profile_name, config_dict_to_save)

            if success:
                # Update in-memory settings only if DB save was successful
                # Keep the currently loaded API keys in the in-memory object
                current_gemini_key = self._settings.gemini_api_key
                current_anthropic_key = self._settings.anthropic_api_key
                # Create a fresh copy from the validated input, then restore keys
                self._settings = updated_settings.model_copy(deep=True)
                self._settings.gemini_api_key = current_gemini_key
                self._settings.anthropic_api_key = current_anthropic_key
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
        """Returns the current configuration settings loaded from the database."""
        if not self._settings:
             logger.error("Configuration settings are not loaded.")
             self._settings = self._load_config() # Attempt to reload if not loaded
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

    # --- Method to update the in-memory API key if changed by gemini_service ---
    # This might be needed if gemini_service successfully switches keys
    def update_current_gemini_key(self, new_key: str):
        """Updates the currently active Gemini API key in the in-memory settings."""
        if self._settings:
            if self._settings.gemini_api_key != new_key:
                 logger.info(f"Updating in-memory Gemini API key.")
                 self._settings.gemini_api_key = new_key
            # Optionally, re-initialize clients in other services if needed
            # e.g., self.token_service._init_clients()
        else:
            logger.warning("Cannot update Gemini key: Settings not loaded.")

