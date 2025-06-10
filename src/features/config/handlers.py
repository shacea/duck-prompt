"""Configuration feature command handlers"""
import logging
from src.gateway.bus.config_command_bus import ConfigCommandBus
from src.gateway.event_bus import EventBus, Event
from src.gateway.service_locator import ServiceLocator
from .commands import (
    LoadConfiguration, UpdateConfiguration,
    GetActiveGeminiKey, SetUserSelectedGeminiKey,
    GetAvailableGeminiKeys, GetLastUsedGeminiKey,
    UpdateGitignorePatterns, GetGitignorePatterns,
    GetDefaultSystemPromptPath, GetTemperatureSettings,
    GetTokenLimits
)
from .organisms.config_service import ConfigurationService

logger = logging.getLogger(__name__)


# Configuration events
class ConfigurationLoadedEvent(Event):
    """Event emitted when configuration is loaded"""
    def __init__(self, profile_name: str):
        self.profile_name = profile_name


class ConfigurationUpdatedEvent(Event):
    """Event emitted when configuration is updated"""
    def __init__(self, profile_name: str):
        self.profile_name = profile_name


# Initialize configuration service and register with ServiceLocator
config_service = ConfigurationService()
ServiceLocator.provide("config", config_service)


@ConfigCommandBus.register(LoadConfiguration)
async def handle_load_configuration(cmd: LoadConfiguration):
    """Load configuration from database"""
    config_service = ServiceLocator.get("config")
    config_service.profile_name = cmd.profile_name
    
    settings = await config_service.load_configuration()
    EventBus.emit(ConfigurationLoadedEvent(profile_name=cmd.profile_name))
    
    return {
        "status": "loaded",
        "profile": cmd.profile_name,
        "settings": settings.model_dump()
    }


@ConfigCommandBus.register(UpdateConfiguration)
async def handle_update_configuration(cmd: UpdateConfiguration):
    """Update configuration settings"""
    config_service = ServiceLocator.get("config")
    
    success = await config_service.update_configuration(cmd.settings)
    
    if success:
        EventBus.emit(ConfigurationUpdatedEvent(profile_name=cmd.profile_name))
    
    return {"success": success}


@ConfigCommandBus.register(GetActiveGeminiKey)
async def handle_get_active_gemini_key(cmd: GetActiveGeminiKey):
    """Get active Gemini API key"""
    config_service = ServiceLocator.get("config")
    key = await config_service.get_active_gemini_key()
    return {"api_key": key}


@ConfigCommandBus.register(SetUserSelectedGeminiKey)
async def handle_set_user_selected_key(cmd: SetUserSelectedGeminiKey):
    """Set user-selected Gemini key preference"""
    config_service = ServiceLocator.get("config")
    config_service.api_key_selector.set_user_selected_key(cmd.key_id)
    return {"status": "set", "key_id": cmd.key_id}


@ConfigCommandBus.register(GetAvailableGeminiKeys)
async def handle_get_available_keys(cmd: GetAvailableGeminiKeys):
    """Get all available Gemini API keys"""
    db_service = ServiceLocator.get("database")
    from src.features.database.commands import ExecuteQuery
    
    query = "SELECT id, service_name, is_active FROM api_keys WHERE service_name = 'google' AND is_active = true"
    keys = await db_service.handle(ExecuteQuery(query=query, fetch_all=True))
    
    return {"keys": keys}


@ConfigCommandBus.register(GetLastUsedGeminiKey)
async def handle_get_last_used_key(cmd: GetLastUsedGeminiKey):
    """Get the last successfully used Gemini key"""
    config_service = ServiceLocator.get("config")
    key = config_service.api_key_selector.get_last_used_key()
    return {"api_key": key}


@ConfigCommandBus.register(UpdateGitignorePatterns)
async def handle_update_gitignore(cmd: UpdateGitignorePatterns):
    """Update gitignore patterns in database"""
    db_service = ServiceLocator.get("database")
    config_service = ServiceLocator.get("config")
    
    from src.features.database.commands import SaveIgnoredPatterns
    await db_service.handle(SaveIgnoredPatterns(patterns=cmd.patterns))
    
    # Update in-memory patterns
    config_service.gitignore_manager.update_database_patterns(cmd.patterns)
    
    return {"status": "updated", "count": len(cmd.patterns)}


@ConfigCommandBus.register(GetGitignorePatterns)
async def handle_get_gitignore(cmd: GetGitignorePatterns):
    """Get current gitignore patterns"""
    config_service = ServiceLocator.get("config")
    patterns = config_service.gitignore_manager.get_all_patterns()
    
    return {
        "patterns": patterns,
        "db_patterns": config_service.gitignore_manager.get_database_patterns(),
        "file_patterns": config_service.gitignore_manager.get_file_patterns()
    }


@ConfigCommandBus.register(GetDefaultSystemPromptPath)
async def handle_get_default_prompt_path(cmd: GetDefaultSystemPromptPath):
    """Get default system prompt path"""
    config_service = ServiceLocator.get("config")
    path = config_service.get_default_system_prompt_path()
    return {"path": path}


@ConfigCommandBus.register(GetTemperatureSettings)
async def handle_get_temperature(cmd: GetTemperatureSettings):
    """Get temperature settings for Gemini"""
    config_service = ServiceLocator.get("config")
    settings = config_service.get_temperature_settings()
    return settings


@ConfigCommandBus.register(GetTokenLimits)
async def handle_get_token_limits(cmd: GetTokenLimits):
    """Get token limit settings"""
    config_service = ServiceLocator.get("config")
    limits = config_service.get_token_limits()
    return limits