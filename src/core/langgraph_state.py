
from typing import TypedDict, Optional, List, Dict, Any # List, Dict, Any 추가

class GeminiGraphState(TypedDict):
    """
    LangGraph 상태 정의: Gemini API 호출 및 결과 처리를 위한 상태 관리
    """
    input_prompt: str             # Gemini API에 전달될 최종 텍스트 프롬프트
    input_attachments: List[Dict[str, Any]] # 첨부된 파일/이미지 데이터 목록 (멀티모달용)
    selected_model_name: str      # LangGraph 실행 시 선택된 모델명 (추가)
    gemini_response: str          # Gemini API의 원시 응답
    xml_output: str               # 파싱된 XML 부분
    summary_output: str           # 파싱된 Summary 부분
    error_message: Optional[str] = None # 오류 발생 시 메시지 저장 (선택적)
    log_id: Optional[int] = None  # DB 로그 ID 저장 (추가)

