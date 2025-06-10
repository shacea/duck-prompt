"""Database feature command handlers"""
import logging
from src.gateway.bus.database_command_bus import DatabaseCommandBus
from src.gateway import EventBus, Event, ServiceLocator
from .commands import (
    ConnectDatabase, DisconnectDatabase, ExecuteQuery,
    GetApiKey, GetActiveApiKey, SaveApiKey,
    GetConfig, SaveConfig, GetAllConfigs, GetModelConfigs,
    SaveGeminiLog, GetGeminiLogs,
    GetIgnoredPatterns, SaveIgnoredPatterns,
    CheckDatabaseConnection
)
from .organisms.database_service import DatabaseService

logger = logging.getLogger(__name__)


# Database connection events
class DatabaseConnectedEvent(Event):
    """Event emitted when database is connected"""
    pass


class DatabaseDisconnectedEvent(Event):
    """Event emitted when database is disconnected"""
    pass


# Initialize database service and register with ServiceLocator
db_service = DatabaseService()
ServiceLocator.provide("database", db_service)


@DatabaseCommandBus.register(ConnectDatabase)
async def handle_connect_database(cmd: ConnectDatabase):
    """Handle database connection command"""
    db_service = ServiceLocator.get("database")
    db_service.connect()
    EventBus.emit(DatabaseConnectedEvent())
    return {"status": "connected"}


@DatabaseCommandBus.register(DisconnectDatabase)
async def handle_disconnect_database(cmd: DisconnectDatabase):
    """Handle database disconnection command"""
    db_service = ServiceLocator.get("database")
    db_service.disconnect()
    EventBus.emit(DatabaseDisconnectedEvent())
    return {"status": "disconnected"}


@DatabaseCommandBus.register(CheckDatabaseConnection)
async def handle_check_connection(cmd: CheckDatabaseConnection):
    """Check if database is connected"""
    db_service = ServiceLocator.get("database")
    return {"connected": db_service.is_connected()}


@DatabaseCommandBus.register(ExecuteQuery)
async def handle_execute_query(cmd: ExecuteQuery):
    """Execute a raw SQL query"""
    db_service = ServiceLocator.get("database")
    result = db_service.execute_query(
        cmd.query, 
        cmd.params, 
        cmd.fetch_one, 
        cmd.fetch_all, 
        cmd.return_id
    )
    return result


@DatabaseCommandBus.register(GetApiKey)
async def handle_get_api_key(cmd: GetApiKey):
    """Get an API key for a service"""
    db_service = ServiceLocator.get("database")
    return db_service.api_key_manager.get_api_key(cmd.service_name)


@DatabaseCommandBus.register(GetActiveApiKey)
async def handle_get_active_api_key(cmd: GetActiveApiKey):
    """Get the active API key for a service"""
    db_service = ServiceLocator.get("database")
    return db_service.api_key_manager.get_active_api_key(cmd.service_name)


@DatabaseCommandBus.register(SaveApiKey)
async def handle_save_api_key(cmd: SaveApiKey):
    """Save or update an API key"""
    db_service = ServiceLocator.get("database")
    rows_affected = db_service.api_key_manager.save_api_key(
        cmd.service_name, 
        cmd.api_key, 
        cmd.is_active
    )
    return {"rows_affected": rows_affected}


@DatabaseCommandBus.register(GetConfig)
async def handle_get_config(cmd: GetConfig):
    """Get a configuration value"""
    db_service = ServiceLocator.get("database")
    return db_service.config_manager.get_config(cmd.key)


@DatabaseCommandBus.register(SaveConfig)
async def handle_save_config(cmd: SaveConfig):
    """Save a configuration value"""
    db_service = ServiceLocator.get("database")
    rows_affected = db_service.config_manager.save_config(cmd.key, cmd.value)
    return {"rows_affected": rows_affected}


@DatabaseCommandBus.register(GetAllConfigs)
async def handle_get_all_configs(cmd: GetAllConfigs):
    """Get all configuration values"""
    db_service = ServiceLocator.get("database")
    return db_service.config_manager.get_all_configs()


@DatabaseCommandBus.register(GetModelConfigs)
async def handle_get_model_configs(cmd: GetModelConfigs):
    """Get model configurations"""
    db_service = ServiceLocator.get("database")
    return db_service.config_manager.get_model_configs()


@DatabaseCommandBus.register(SaveGeminiLog)
async def handle_save_gemini_log(cmd: SaveGeminiLog):
    """Save a Gemini API log entry"""
    db_service = ServiceLocator.get("database")
    log_id = db_service.gemini_log_manager.save_log(
        cmd.model_name,
        cmd.prompt_tokens,
        cmd.response_tokens,
        cmd.total_tokens,
        cmd.response_text,
        cmd.response_summary
    )
    return {"log_id": log_id}


@DatabaseCommandBus.register(GetGeminiLogs)
async def handle_get_gemini_logs(cmd: GetGeminiLogs):
    """Get Gemini API logs"""
    db_service = ServiceLocator.get("database")
    return db_service.gemini_log_manager.get_logs(cmd.limit, cmd.offset)


@DatabaseCommandBus.register(GetIgnoredPatterns)
async def handle_get_ignored_patterns(cmd: GetIgnoredPatterns):
    """Get ignored file patterns"""
    db_service = ServiceLocator.get("database")
    return db_service.get_ignored_patterns()


@DatabaseCommandBus.register(SaveIgnoredPatterns)
async def handle_save_ignored_patterns(cmd: SaveIgnoredPatterns):
    """Save ignored file patterns"""
    db_service = ServiceLocator.get("database")
    db_service.save_ignored_patterns(cmd.patterns)
    return {"status": "saved", "count": len(cmd.patterns)}
