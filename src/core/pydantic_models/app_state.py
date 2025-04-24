from pydantic import BaseModel, Field
from typing import List, Optional

class AppState(BaseModel):
    """
    Represents the application state.
    """
    mode: str = "Code Enhancer Prompt Builder"
    project_folder: Optional[str] = None
    system_prompt: str = ""
    user_prompt: str = ""
    # last_generated_prompt는 UI 상태에 가까우므로 제외하거나 필요시 추가
    # last_generated_prompt: str = ""
    checked_files: List[str] = Field(default_factory=list)
    # 추가적인 상태 필드 정의 가능
    # e.g., window_geometry: Optional[bytes] = None

    class Config:
        validate_assignment = True # 필드 값 변경 시 유효성 검사
