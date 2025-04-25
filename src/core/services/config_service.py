
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

    # --- Saving/Updating configuration to DB is NOT implemented in this version ---
    # def _save_config(self, settings: ConfigSettings):
    #     """Saves the current configuration to the database (Not Implemented)."""
    #     logger.warning("Saving configuration to database is not implemented in this version.")
    #     # Implementation would involve calling db_service.save_application_config
    #     pass

    # def update_settings(self, **kwargs):
    #     """Updates specific configuration settings and saves them (Not Implemented)."""
    #     logger.warning("Updating configuration in database is not implemented in this version.")
    #     # Implementation would involve updating self._settings and calling _save_config
    #     # For now, just update the in-memory settings if needed, but they won't persist
    #     try:
    #         updated_data = self._settings.model_copy(update=kwargs).model_dump()
    #         self._settings = ConfigSettings(**updated_data) # Update in-memory only
    #         print("In-memory configuration updated (database not modified).")
    #     except ValidationError as e:
    #         print(f"Configuration update validation error: {e}")
    #     except Exception as e:
    #         print(f"Error updating in-memory configuration: {e}")
    # --- End of Non-Implemented Saving Logic ---

    def get_settings(self) -> ConfigSettings:
        """Returns the current configuration settings loaded from the database."""
        # If settings need to be refreshed frequently, call _load_config() here.
        # For now, return the settings loaded at initialization.
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

    # --- Saving default model name is NOT implemented for DB ---
    # def save_default_model_name(self, llm_type: str, model_name: str):
    #     """Saves the default model name for a given LLM type to settings (Not Implemented for DB)."""
    #     logger.warning("Saving default model name to database is not implemented.")
    #     # update_dict = {}
    #     # if llm_type == "Gemini":
    #     #     update_dict["gemini_default_model"] = model_name
    #     # elif llm_type == "Claude":
    #     #     update_dict["claude_default_model"] = model_name
    #     # elif llm_type == "GPT":
    #     #     update_dict["gpt_default_model"] = model_name
    #     #
    #     # if update_dict:
    #     #     self.update_settings(**update_dict) # This would need DB update logic
    #     # else:
    #     #     print(f"Warning: Cannot save default model for unknown LLM type: {llm_type}")
    # --- End of Non-Implemented Saving Logic ---

