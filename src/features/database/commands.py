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
    provider: str


class GetActiveApiKey(Command):
    """Command to get an active API key for a service"""
    provider: str


class SaveApiKey(Command):
    """Command to save or update an API key"""
    provider: str
    api_key: str
    is_active: bool = True


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
    response_text: Optional[str] = None
    response_summary: Optional[str] = None


class GetGeminiLogs(Command):
    """Command to retrieve Gemini logs"""
    limit: int = 100
    offset: int = 0


class CheckDatabaseConnection(Command):
    """Command to check if database connection is active"""
    pass
