"""Database feature commands"""
from typing import Optional, Dict, Any, List
from src.gateway.bus._base import Command


class ConnectDatabase(Command):
    """Command to establish database connection"""
    pass


class DisconnectDatabase(Command):
    """Command to close database connection"""
    pass


class ExecuteQuery(Command):
    """Command to execute a database query"""
    query: str
    params: Optional[tuple] = None
    fetch_one: bool = False
    fetch_all: bool = False
    return_id: bool = False


class GetApiKey(Command):
    """Command to get an API key from database"""
    service_name: str


class GetActiveApiKey(Command):
    """Command to get an active API key for a service"""
    service_name: str


class SaveApiKey(Command):
    """Command to save or update an API key"""
    service_name: str
    api_key: str
    is_active: bool = True


class GetConfig(Command):
    """Command to get a configuration value"""
    key: str


class SaveConfig(Command):
    """Command to save a configuration value"""
    key: str
    value: str


class GetAllConfigs(Command):
    """Command to get all configuration values"""
    pass


class GetModelConfigs(Command):
    """Command to get model configurations"""
    pass


class SaveGeminiLog(Command):
    """Command to save a Gemini API log entry"""
    model_name: str
    prompt_tokens: int
    response_tokens: int
    total_tokens: int
    prompt_cost: float
    response_cost: float
    total_cost: float
    response_text: Optional[str] = None
    response_summary: Optional[str] = None


class GetGeminiLogs(Command):
    """Command to retrieve Gemini logs"""
    limit: int = 100
    offset: int = 0


class GetIgnoredPatterns(Command):
    """Command to get ignored file patterns"""
    pass


class SaveIgnoredPatterns(Command):
    """Command to save ignored file patterns"""
    patterns: List[str]


class CheckDatabaseConnection(Command):
    """Command to check if database connection is active"""
    pass