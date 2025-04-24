from pydantic import BaseModel, Field, field_validator
from typing import List, Set, Any, Optional

class ConfigSettings(BaseModel):
    """
    Represents the application configuration settings loaded from config.yml.
    """
    default_system_prompt: Optional[str] = None # 기본 시스템 프롬프트 경로 (문자열 또는 None)
    allowed_extensions: Set[str] = Field(default_factory=set)
    excluded_dirs: Set[str] = Field(default_factory=set)
    default_ignore_list: List[str] = Field(default_factory=lambda: [
        "__pycache__/",
        ".git/",
        ".gitignore",
        ".windsurfrules",
        ".cursorrules"
    ])
    gemini_default_model: str = "gemini-1.5-pro-latest" # Gemini 기본 모델명
    claude_default_model: str = "claude-3-sonnet-20240229" # Claude 기본 모델명

    # API Keys (Optional, read from config.yml)
    # google_cloud_project: Optional[str] = None # Removed
    # google_cloud_location: Optional[str] = None # Removed
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None # Added for google-generativeai SDK
    # use_vertexai_for_gemini: bool = True # Removed

    @field_validator('allowed_extensions', 'excluded_dirs', mode='before')
    @classmethod
    def ensure_set_of_str(cls, v: Any):
        if v is None: # None 값 허용 (기본값 사용)
            return set()
        if isinstance(v, set) and all(isinstance(item, str) for item in v):
            return v
        if isinstance(v, (list, tuple)) and all(isinstance(item, str) for item in v):
            return set(v)
        raise TypeError("allowed_extensions/excluded_dirs는 str의 집합(set) 또는 리스트/튜플이어야 합니다.")

    class Config:
        validate_assignment = True
