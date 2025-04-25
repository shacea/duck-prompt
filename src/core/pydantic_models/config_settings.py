
from pydantic import BaseModel, Field, field_validator, FieldValidationInfo
from typing import List, Set, Any, Optional, Dict

class ConfigSettings(BaseModel):
    """
    Represents the application configuration settings loaded from the database.
    """
    # --- Fields loaded from application_config table ---
    profile_name: str = 'default' # Included for completeness, usually 'default'
    default_system_prompt: Optional[str] = None
    allowed_extensions: Set[str] = Field(default_factory=set)
    excluded_dirs: Set[str] = Field(default_factory=set)
    default_ignore_list: List[str] = Field(default_factory=list)
    gemini_default_model: str = "gemini-1.5-pro-latest" # Default if DB is missing
    claude_default_model: str = "claude-3-sonnet-20240229"
    gpt_default_model: str = "gpt-4o"
    gemini_available_models: List[str] = Field(default_factory=list)
    claude_available_models: List[str] = Field(default_factory=list)
    gpt_available_models: List[str] = Field(default_factory=list)
    gemini_temperature: float = Field(0.0, ge=0.0, le=2.0)
    gemini_enable_thinking: bool = Field(True)
    gemini_thinking_budget: int = Field(24576, ge=0)
    gemini_enable_search: bool = Field(True)
    # created_at, updated_at are in DB but not needed in the model for app logic

    # --- Fields loaded separately from api_keys table ---
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    # openai_api_key: Optional[str] = None # If needed

    @field_validator('allowed_extensions', 'excluded_dirs', mode='before')
    @classmethod
    def ensure_set_from_list_or_none(cls, v: Any, info: FieldValidationInfo):
        """Converts list (from DB array) or None to a set of strings."""
        if v is None:
            return set()
        if isinstance(v, (list, tuple, set)):
            # Ensure all items are strings
            if all(isinstance(item, str) for item in v):
                return set(v)
            else:
                raise TypeError(f"{info.field_name} must be a list/set of strings")
        # Allow comma or space separated string as fallback (though DB should provide list)
        if isinstance(v, str):
             items = {item.strip() for item in v.replace(',', ' ').split() if item.strip()}
             return items
        raise TypeError(f"{info.field_name} must be a list, set, or None (received {type(v)})")

    @field_validator('default_ignore_list', 'gemini_available_models', 'claude_available_models', 'gpt_available_models', mode='before')
    @classmethod
    def ensure_list_from_list_or_none(cls, v: Any, info: FieldValidationInfo):
        """Ensures the value is a list of strings, accepting None."""
        if v is None:
            return []
        if isinstance(v, (list, tuple, set)):
             # Ensure all items are strings
            if all(isinstance(item, str) for item in v):
                return list(v)
            else:
                raise TypeError(f"{info.field_name} must be a list/set of strings")
        raise TypeError(f"{info.field_name} must be a list, set, or None (received {type(v)})")

    class Config:
        validate_assignment = True
        # If loading directly from DB dict, extra fields might exist (id, created_at etc.)
        extra = 'ignore' # Ignore extra fields from DB query result

