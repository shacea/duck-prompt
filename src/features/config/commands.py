"""Configuration feature commands"""
from typing import Optional, List, Dict, Any
from src.gateway.bus._base import Command


class LoadConfiguration(Command):
    """Command to load configuration from database"""
    profile_name: str = 'default'


class UpdateConfiguration(Command):
    """Command to update configuration settings"""
    settings: Dict[str, Any]
    profile_name: str = 'default'


class GetActiveGeminiKey(Command):
    """Command to get active Gemini API key"""
    pass


class SetUserSelectedGeminiKey(Command):
    """Command to set user-selected Gemini API key"""
    key_id: int


class GetAvailableGeminiKeys(Command):
    """Command to get all available Gemini API keys"""
    pass


class GetLastUsedGeminiKey(Command):
    """Command to get the last successfully used Gemini key"""
    pass


class UpdateGitignorePatterns(Command):
    """Command to update gitignore patterns"""
    patterns: List[str]


class GetGitignorePatterns(Command):
    """Command to get current gitignore patterns"""
    pass


class GetDefaultSystemPromptPath(Command):
    """Command to get the default system prompt path"""
    pass


class GetTemperatureSettings(Command):
    """Command to get temperature settings for Gemini"""
    pass


class GetTokenLimits(Command):
    """Command to get token limit settings"""
    pass