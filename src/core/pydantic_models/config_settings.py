from pydantic import BaseModel, Field, field_validator
from typing import List, Set, Any

class ConfigSettings(BaseModel):
    """
    Represents the application configuration settings loaded from config.yml.
    """
    allowed_extensions: Set[str] = Field(default_factory=set)
    excluded_dirs: Set[str] = Field(default_factory=set)
    default_ignore_list: List[str] = Field(default_factory=lambda: [
        "__pycache__/",
        ".git/",
        ".gitignore",
        ".windsurfrules",
        ".cursorrules"
    ])
    # 추가 설정 필드 정의 가능
    # e.g., default_theme: str = "Fusion"

    @field_validator('allowed_extensions', 'excluded_dirs', mode='before')
    @classmethod
    def ensure_set_of_str(cls, v: Any):
        if isinstance(v, set) and all(isinstance(item, str) for item in v):
            return v
        if isinstance(v, (list, tuple)) and all(isinstance(item, str) for item in v):
            return set(v)
        raise TypeError("allowed_extensions/excluded_dirs는 str의 집합(set)이어야 합니다.")

    class Config:
        validate_assignment = True
