
from pydantic import BaseModel, Field, field_validator
from typing import List, Set, Any, Optional, Dict # Dict 추가

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
    gpt_default_model: str = "gpt-4o" # GPT 기본 모델명 추가 (필요시)

    # --- 사용 가능한 모델 목록 ---
    # config.yml에서 로드할 모델 목록
    gemini_available_models: List[str] = Field(default_factory=lambda: ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-1.0-pro"])
    claude_available_models: List[str] = Field(default_factory=lambda: ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"])
    gpt_available_models: List[str] = Field(default_factory=lambda: ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
    # --------------------------

    # API Keys (Optional, read from config.yml)
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    # openai_api_key: Optional[str] = None # 필요시 추가

    # --- Gemini Specific API Parameters ---
    gemini_temperature: float = Field(0.0, ge=0.0, le=2.0, description="Gemini generation temperature")
    gemini_enable_thinking: bool = Field(True, description="Enable Gemini ThinkingConfig")
    gemini_thinking_budget: int = Field(24576, ge=0, description="Gemini ThinkingConfig budget")
    gemini_enable_search: bool = Field(True, description="Enable Google Search tool for Gemini")
    # --------------------------------------


    @field_validator('allowed_extensions', 'excluded_dirs', mode='before')
    @classmethod
    def ensure_set_of_str(cls, v: Any):
        if v is None: # None 값 허용 (기본값 사용)
            return set()
        if isinstance(v, set) and all(isinstance(item, str) for item in v):
            return v
        if isinstance(v, (list, tuple)) and all(isinstance(item, str) for item in v):
            return set(v)
        # Allow comma or space separated string for allowed_extensions
        if isinstance(v, str):
             items = [item.strip() for item in v.replace(',', ' ').split() if item.strip()]
             return set(items)
        raise TypeError("allowed_extensions/excluded_dirs는 str의 집합(set) 또는 리스트/튜플 또는 구분자로 분리된 문자열이어야 합니다.")

    @field_validator('default_ignore_list', 'gemini_available_models', 'claude_available_models', 'gpt_available_models', mode='before')
    @classmethod
    def ensure_list_of_str(cls, v: Any):
         if v is None:
             return [] # Return empty list if None
         if isinstance(v, list) and all(isinstance(item, str) for item in v):
             return v
         if isinstance(v, (set, tuple)) and all(isinstance(item, str) for item in v):
             return list(v)
         raise TypeError("default_ignore_list 또는 available_models 필드는 str의 리스트여야 합니다.")


    class Config:
        validate_assignment = True
