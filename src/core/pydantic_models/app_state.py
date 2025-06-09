from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any # Dict, Any 추가

class AppState(BaseModel):
    """
    Represents the application state.
    저장/로드 시 특정 필드만 사용될 수 있음 (예: 이전 작업 불러오기).
    """
    # --- 이전 작업 저장/로드 대상 필드 ---
    project_folder: Optional[str] = None # 프로젝트 폴더 경로
    checked_files: List[str] = Field(default_factory=list) # 체크된 파일/폴더 경로 목록
    user_prompt: str = "" # 사용자 탭 내용
    attached_items: List[Dict[str, Any]] = Field(default_factory=list) # 첨부 파일/이미지 메타데이터 목록

    # --- 기타 상태 필드 (전체 상태 저장/로드 시 사용) ---
    system_prompt: str = "" # 시스템 탭 내용 (기본값 로드 로직 있음)
    selected_llm: str = "Gemini" # 선택된 LLM
    selected_model_name: str = "" # 선택된 모델명

    # Gemini 파라미터는 config.yml에서 관리하므로 AppState에서 제거
    # gemini_temperature: float = 0.0
    # gemini_enable_thinking: bool = True
    # gemini_thinking_budget: int = 24576
    # gemini_enable_search: bool = True

    class Config:
        validate_assignment = True
