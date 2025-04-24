from pydantic import BaseModel, Field, field_validator, FilePath, DirectoryPath # FilePath, DirectoryPath 추가 (선택적)
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
        # .env는 제거됨
    ])
    # 추가 설정 필드 정의 가능
    # e.g., default_theme: str = "Fusion"

    # 경로 유효성 검사기 (선택적)
    # @field_validator('default_system_prompt')
    # @classmethod
    # def check_prompt_path(cls, v: Optional[str]):
    #     if v is not None and not os.path.exists(v): # 실제 파일 존재 여부 확인 (로드 시점에 하는 것이 더 나을 수 있음)
    #         # 경고 로깅 또는 예외 발생
    #         print(f"Warning: Default system prompt path does not exist: {v}")
    #         # raise ValueError(f"Default system prompt path does not exist: {v}")
    #     return v

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
