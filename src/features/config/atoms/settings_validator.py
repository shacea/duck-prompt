"""Settings validator atom - validates configuration settings"""
import logging
from typing import Dict, Any
from pydantic import ValidationError
from src.features.config.pydantic_models.config_settings import ConfigSettings

logger = logging.getLogger(__name__)


class SettingsValidator:
    """Validates configuration settings using Pydantic models"""
    
    @staticmethod
    def validate(settings_dict: Dict[str, Any]) -> ConfigSettings:
        """Validate settings dictionary and return ConfigSettings model"""
        try:
            settings = ConfigSettings(**settings_dict)
            logger.debug("Settings validation successful")
            return settings
        except ValidationError as e:
            logger.error(f"Settings validation failed: {e}")
            raise ValueError(f"Invalid configuration settings: {e}")
    
    @staticmethod
    def validate_partial(settings_dict: Dict[str, Any], existing_settings: ConfigSettings) -> ConfigSettings:
        """Validate partial settings update against existing settings"""
        try:
            # Merge with existing settings
            current_dict = existing_settings.model_dump()
            current_dict.update(settings_dict)
            
            # Validate merged settings
            updated_settings = ConfigSettings(**current_dict)
            logger.debug("Partial settings validation successful")
            return updated_settings
        except ValidationError as e:
            logger.error(f"Partial settings validation failed: {e}")
            raise ValueError(f"Invalid configuration update: {e}")

