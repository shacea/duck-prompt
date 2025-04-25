from typing import TypedDict, Optional

class GeminiGraphState(TypedDict):
    """
    LangGraph 상태 정의: Gemini API 호출 및 결과 처리를 위한 상태 관리
    """
    input_prompt: str             # Gemini API에 전달될 최종 프롬프트
    gemini_response: str          # Gemini API의 원시 응답
    xml_output: str               # 파싱된 XML 부분
    summary_output: str           # 파싱된 Summary 부분
    error_message: Optional[str] = None # 오류 발생 시 메시지 저장 (선택적)