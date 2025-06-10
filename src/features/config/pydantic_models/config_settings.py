"""Pydantic model for application configuration settings."""
from pydantic import BaseModel, Field
from typing import List, Optional

class ConfigSettings(BaseModel):
    """Defines the structure for application configuration settings."""
    profile_name: str = 'default'
    default_system_prompt_path: Optional[str] = Field(None, alias='default_system_prompt')
    allowed_extensions: Optional[List[str]] = []
    excluded_dirs: Optional[List[str]] = []
    default_ignore_list: Optional[List[str]] = []
    
    gemini_default_model: Optional[str] = None
    claude_default_model: Optional[str] = None
    gpt_default_model: Optional[str] = None
    
    gemini_available_models: Optional[List[str]] = []
    claude_available_models: Optional[List[str]] = []
    gpt_available_models: Optional[List[str]] = []
    
    gemini_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    gemini_enable_thinking: bool = True
    gemini_thinking_budget: int = 24576
    gemini_enable_search: bool = True
    
    # API keys are added dynamically by the service, not loaded from DB config table
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    class Config:
        populate_by_name = True
        # This allows 'default_system_prompt' from DB to map to 'default_system_prompt_path'
