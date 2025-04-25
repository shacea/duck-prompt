
import os
import logging
from pydantic import ValidationError
from typing import Optional, List, Set, Dict, Any # Set, Dict, Any 추가

from core.pydantic_models.config_settings import ConfigSettings
from .db_service import DbService # DbService import
# from utils.helpers import get_project_root # 프로젝트 루트 더 이상 필요 없음

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
                # Consider raising an exception or returning a default ConfigSettings
                # For now, let's raise an error to make the failure explicit
                raise ValueError(f"Configuration profile '{self.profile_name}' not found in database.")

            # 2. Fetch API keys from DB
            gemini_key = self.db_service.get_active_api_key('google')
            anthropic_key = self.db_service.get_active_api_key('anthropic')

            # 3. Add API keys to the config data dictionary
            config_data['gemini_api_key'] = gemini_key
            config_data['anthropic_api_key'] = anthropic_key

            # 4. Validate and create ConfigSettings model
            # Pydantic should handle list/set conversion if DB returns lists for arrays
            settings = ConfigSettings(**config_data)
            logger.info(f"Configuration loaded successfully from database for profile '{self.profile_name}'.")
            return settings

        except ValidationError as e:
            logger.critical(f"Database configuration validation error: {e}. Using default settings (or failing).", exc_info=True)
            # Depending on requirements, either return default or raise error
            # Raising error is safer as config is critical
            raise ValueError(f"Configuration validation failed: {e}")
        except Exception as e:
            logger.critical(f"Unexpected error loading config from database: {e}", exc_info=True)
            raise ValueError(f"Failed to load configuration from database: {e}")

    def update_settings(self, updated_settings: ConfigSettings) -> bool:
        """
        Updates the application configuration in the database and in memory.

        Args:
            updated_settings: A ConfigSettings object with the updated values.

        Returns:
            True if the update was successful, False otherwise.
        """
        logger.info(f"Attempting to update configuration in database for profile '{self.profile_name}'...")
        try:
            # Convert Pydantic model to dictionary for DB service
            # Exclude API keys as they are managed separately (or not updated via this method)
            config_dict_to_save = updated_settings.model_dump(exclude={'gemini_api_key', 'anthropic_api_key'})

            # Call DbService to save the configuration
            success = self.db_service.save_application_config(self.profile_name, config_dict_to_save)

            if success:
                # Update in-memory settings only if DB save was successful
                # Reload from DB to ensure consistency or update directly? Update directly for now.
                # Need to re-add API keys to the in-memory object
                current_gemini_key = self._settings.gemini_api_key
                current_anthropic_key = self._settings.anthropic_api_key
                self._settings = updated_settings.model_copy() # Create a fresh copy
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
        # If settings need to be refreshed frequently, call _load_config() here.
        # For now, return the settings loaded at initialization or after update.
        if not self._settings:
             logger.error("Configuration settings are not loaded.")
             # Attempt to reload or raise error
             self._settings = self._load_config()
        return self._settings

    def get_default_model_name(self, llm_type: str) -> str:
        """Gets the default model name for a given LLM type from settings."""
        settings = self.get_settings()
        if llm_type == "Gemini":
            return settings.gemini_default_model
        elif llm_type == "Claude":
            return settings.claude_default_model
        elif llm_type == "GPT":
            return settings.gpt_default_model
        else:
            logger.warning(f"Unknown LLM type '{llm_type}' requested for default model.")
            return ""

    def get_available_models(self, llm_type: str) -> List[str]:
        """Gets the list of available model names for a given LLM type from settings."""
        settings = self.get_settings()
        models = []
        if llm_type == "Gemini":
            models = settings.gemini_available_models
        elif llm_type == "Claude":
            models = settings.claude_available_models
        elif llm_type == "GPT":
            models = settings.gpt_available_models
        else:
            logger.warning(f"Unknown LLM type '{llm_type}' requested for available models.")

        # Ensure it returns a list even if the DB field was null/empty
        return models if models is not None else []

    # --- Saving default model name is handled by update_settings ---
    # def save_default_model_name(self, llm_type: str, model_name: str): ...
