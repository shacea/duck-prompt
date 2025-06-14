"""Configuration service organism - manages all configuration operations"""
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from src.gateway import ServiceLocator
from src.features.config.pydantic_models.config_settings import ConfigSettings
from ..atoms.settings_validator import SettingsValidator
from ..molecules.api_key_selector import ApiKeySelector
from ..molecules.gitignore_manager import GitignoreManager

logger = logging.getLogger(__name__)


class ConfigurationService:
    """High-level configuration service"""
    
    def __init__(self, profile_name: str = 'default'):
        self.profile_name = profile_name
        self._settings: Optional[ConfigSettings] = None
        self.api_key_selector = ApiKeySelector()
        self.gitignore_manager = GitignoreManager()
        self.validator = SettingsValidator()
    
    async def load_configuration(self) -> ConfigSettings:
        """Load configuration from database"""
        try:
            # Get database service from ServiceLocator
            db_service = ServiceLocator.get("database")
            
            # Load application config
            config_data = self._get_application_config(db_service)
            
            if not config_data:
                raise ValueError(f"Configuration profile '{self.profile_name}' not found in database")
            
            # Check for available API keys
            self._check_api_keys(db_service)
            
            # Add API key placeholders
            config_data['gemini_api_key'] = None  # Selected on demand
            config_data['anthropic_api_key'] = self._get_anthropic_key(db_service)
            
            # Validate and create settings
            self._settings = self.validator.validate(config_data)
            
            # Load gitignore patterns from the config object itself
            patterns = self._settings.default_ignore_list or []
            self.gitignore_manager.load_from_database(patterns)
            
            logger.info(f"Configuration loaded successfully for profile '{self.profile_name}'")
            return self._settings
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def update_configuration(self, settings_dict: Dict[str, Any]) -> bool:
        """Update configuration in database"""
        try:
            if not self._settings:
                raise ValueError("Configuration not loaded")
            
            # Validate update
            updated_settings = self.validator.validate_partial(settings_dict, self._settings)
            
            # Save to database (excluding API keys)
            db_service = ServiceLocator.get("database")
            config_dict = updated_settings.model_dump(exclude={'gemini_api_key', 'anthropic_api_key'})
            
            success = self._save_application_config(db_service, config_dict)
            
            if success:
                self._settings = updated_settings
                logger.info("Configuration updated successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
    
    def get_active_gemini_key(self) -> Optional[str]:
        """Get active Gemini API key with selection logic"""
        try:
            db_service = ServiceLocator.get("database")
            available_keys = self._get_available_gemini_keys(db_service)
            
            if not available_keys:
                logger.warning("No active Gemini API keys available")
                return None
            
            selected_key = self.api_key_selector.select_key(available_keys)
            return selected_key
            
        except Exception as e:
            logger.error(f"Failed to get active Gemini key: {e}")
            return None
    
    def get_settings(self) -> Optional[ConfigSettings]:
        """Get current configuration settings"""
        return self._settings
    
    def get_default_system_prompt_path(self) -> Optional[str]:
        """Get default system prompt path from settings"""
        if self._settings:
            return self._settings.default_system_prompt_path
        return None
    
    def get_temperature_settings(self) -> Dict[str, float]:
        """Get temperature settings for Gemini"""
        if not self._settings:
            return {"temperature": 0.7, "top_p": 0.95, "top_k": 40}
        
        return {
            "temperature": self._settings.gemini_temperature,
            "top_p": self._settings.gemini_top_p,
            "top_k": self._settings.gemini_top_k
        }
    
    def get_token_limits(self) -> Dict[str, int]:
        """Get token limit settings"""
        if not self._settings:
            return {"max_output_tokens": 8192}
        
        return {
            "max_output_tokens": self._settings.gemini_max_output_tokens
        }
    
    # Private helper methods for database operations
    def _get_application_config(self, db_service) -> Dict[str, Any]:
        """Get application config from database"""
        configs_list = db_service.config_manager.get_all_configs()

        # Find the dictionary for the current profile_name
        for config_profile in configs_list:
            if config_profile.get('profile_name') == self.profile_name:
                logger.debug(f"Found configuration profile: {self.profile_name}")
                return config_profile
        
        logger.warning(f"Configuration profile '{self.profile_name}' not found in database.")
        return {}
    
    def _save_application_config(self, db_service, config_dict: Dict[str, Any]) -> bool:
        """Save application config to database"""
        db_service.config_manager.update_profile_config(self.profile_name, config_dict)
        return True
    
    def _get_available_gemini_keys(self, db_service) -> List[Dict[str, Any]]:
        """Get available Gemini API keys"""
        query = "SELECT * FROM api_keys WHERE provider = 'google' AND is_active = true"
        return db_service.execute_query(query=query, fetch_all=True)
    
    def _get_anthropic_key(self, db_service) -> Optional[str]:
        """Get active Anthropic API key"""
        return db_service.api_key_manager.get_active_api_key(provider='anthropic')
    
    def _check_api_keys(self, db_service) -> None:
        """Check availability of API keys"""
        gemini_keys = self._get_available_gemini_keys(db_service)
        if not gemini_keys:
            logger.warning("No active Gemini API keys found in database")
        else:
            logger.info(f"Found {len(gemini_keys)} active Gemini API keys")
