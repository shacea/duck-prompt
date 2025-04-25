
import google.generativeai as genai
from langgraph.graph import StateGraph, END, START
from functools import partial
import logging

from core.langgraph_state import GeminiGraphState
from core.services.config_service import ConfigService

logger = logging.getLogger(__name__)

# --- LangGraph 노드 함수 ---

def call_gemini(state: GeminiGraphState, config_service: ConfigService) -> GeminiGraphState:
    """
    Gemini API를 호출하는 노드
    """
    print("--- Calling Gemini API ---")
    logger.info("Calling Gemini API node")
    prompt = state['input_prompt']
    settings = config_service.get_settings()
    api_key = settings.gemini_api_key
    # 설정에서 모델명 가져오기 (config_service에 해당 메서드 필요)
    model_name = config_service.get_default_model_name("Gemini")

    if not api_key:
        error_msg = "Gemini API Key not configured in config.yml."
        logger.error(error_msg)
        return {"error_message": error_msg}
    if not model_name:
        error_msg = "Gemini default model name not configured in config.yml."
        logger.error(error_msg)
        return {"error_message": error_msg}

    try:
        # API 키 설정 (호출 시마다 필요할 수 있음)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        # TODO: Gemini API 호출 시 필요한 추가 설정 (safety_settings 등) 고려
        # generation_config = genai.types.GenerationConfig(
        #     # candidate_count=1, # 기본값
        #     # stop_sequences=['...'],
        #     # max_output_tokens=...,
        #     # temperature=...,
        # )
        # safety_settings = [ ... ] # 필요 시 안전 설정 추가

        logger.info(f"Sending prompt to Gemini model: {model_name}")
        response = model.generate_content(prompt) #, generation_config=generation_config, safety_settings=safety_settings)

        # 오류 처리 확인 (response.prompt_feedback 등)
        # response.candidates가 비어있는지 또는 prompt_feedback에 block reason이 있는지 확인
        if not response.candidates or (hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason):
             block_reason = response.prompt_feedback.block_reason if hasattr(response, 'prompt_feedback') else "Unknown"
             safety_ratings = response.prompt_feedback.safety_ratings if hasattr(response, 'prompt_feedback') else "N/A"
             error_msg = f"Gemini API call failed. Block Reason: {block_reason}, Safety Ratings: {safety_ratings}"
             logger.error(error_msg)
             # 빈 응답과 오류 메시지 반환
             return {"gemini_response": "", "error_message": error_msg}

        # 성공 시 텍스트 추출
        # response.text 는 가장 가능성 높은 candidate의 text를 반환
        gemini_response_text = response.text
        logger.info("--- Gemini Response Received ---")
        return {"gemini_response": gemini_response_text, "error_message": None}

    except Exception as e:
        error_msg = f"Error calling Gemini API: {str(e)}"
        logger.exception(error_msg) # 스택 트레이스 포함 로깅
        return {"gemini_response": "", "error_message": error_msg}


def process_response(state: GeminiGraphState) -> GeminiGraphState:
    """
    Gemini 응답을 XML과 Summary로 파싱하는 노드.
    응답 끝 부분의 <summary> 태그를 기준으로 분리하여 코드 내 문자열과의 혼동을 줄입니다.
    """
    print("--- Processing Gemini Response ---")
    logger.info("Processing Gemini Response node")
    gemini_response = state.get('gemini_response', '') # 기본값 '' 추가
    xml_output = ""
    summary_output = ""
    error_message = state.get('error_message') # 기존 오류 메시지 유지 시도

    try:
        if not gemini_response:
             logger.warning("Gemini response is empty, skipping processing.")
             if not error_message:
                 error_message = "Gemini response was empty."
             return {"xml_output": "", "summary_output": "", "error_message": error_message}

        # 응답 문자열을 정리 (앞뒤 공백 제거)
        cleaned_response = gemini_response.strip()

        # 응답 끝에서부터 <summary> 태그 찾기
        summary_start_tag = "<summary>"
        summary_end_tag = "</summary>"
        summary_start_index = cleaned_response.rfind(summary_start_tag) # 오른쪽에서부터 찾기

        # <summary> 태그가 응답의 합리적인 위치(예: 끝 부분)에 있는지 확인
        # 너무 앞쪽에 있다면 코드 내 문자열일 가능성이 높음
        # 예를 들어, 전체 길이의 절반 이후에 나타나는 경우만 유효한 태그로 간주 (조정 가능)
        # 또한, 시작 태그가 문자열 시작 부분에 오는 극단적인 경우도 배제 (예: index > 0)
        is_valid_summary_position = (
            summary_start_index != -1 and
            summary_start_index > 0 and # 시작 부분에 바로 오는 경우 제외
            summary_start_index > len(cleaned_response) * 0.5 # 응답의 후반부에 위치하는지 확인 (50% 지점 이후)
        )

        if is_valid_summary_position:
            xml_output = cleaned_response[:summary_start_index].strip()
            # <summary> 태그 이후의 부분을 summary_part로 추출
            summary_part = cleaned_response[summary_start_index + len(summary_start_tag):]

            # summary_part 끝에서 </summary> 태그 찾기
            summary_end_index = summary_part.rfind(summary_end_tag)
            if summary_end_index != -1:
                 # 종료 태그 이전까지의 내용을 summary로 간주
                 summary_output = summary_part[:summary_end_index].strip()
            else:
                 # 종료 태그가 없으면 시작 태그 이후 모든 것을 summary로 간주 (기존 로직 유지)
                 # 이 경우, summary_part 전체가 summary 내용이 됨
                 summary_output = summary_part.strip()
                 logger.warning("Summary end tag '</summary>' not found at the end of the summary part. Taking content after '<summary>'.")

            # XML 부분 끝에 실수로 </summary>가 포함된 경우 제거 (선택적 보강)
            if xml_output.endswith(summary_end_tag):
                xml_output = xml_output[:-len(summary_end_tag)].strip()
                logger.warning("Removed trailing '</summary>' tag from the XML part.")

        else:
            # Summary 태그가 없거나 유효한 위치에 없는 경우, 전체를 XML로 간주
            xml_output = cleaned_response
            if summary_start_index == -1:
                summary_output = "Summary tag '<summary>' not found in response."
            else:
                summary_output = f"Summary tag '<summary>' found at index {summary_start_index}, which is considered too early. Treating entire response as XML."
            logger.warning(summary_output)

        logger.info("--- Response Processed ---")
        # 파싱 성공 시 오류 메시지는 None으로 설정 (기존 오류 덮어쓰기)
        return {"xml_output": xml_output, "summary_output": summary_output, "error_message": None}

    except Exception as e:
        error_msg = f"Error processing response: {str(e)}"
        logger.exception(error_msg)
        # 오류 발생 시 원본 응답을 XML로, 빈 Summary 반환
        return {"xml_output": gemini_response, "summary_output": "", "error_message": error_msg}


def build_gemini_graph(config_service: ConfigService) -> StateGraph:
    """
    Gemini API 호출 및 처리 LangGraph를 빌드합니다.
    ConfigService를 주입받아 노드에서 사용합니다.
    """
    workflow = StateGraph(GeminiGraphState)

    # ConfigService를 call_gemini 노드 함수에 바인딩
    bound_call_gemini = partial(call_gemini, config_service=config_service)

    # 노드 추가
    workflow.add_node("call_gemini", bound_call_gemini)
    workflow.add_node("process_response", process_response)

    # 엣지 연결: START -> call_gemini -> process_response -> END
    workflow.add_edge(START, "call_gemini")
    workflow.add_edge("call_gemini", "process_response")
    workflow.add_edge("process_response", END)

    # 컴파일
    # checkpointer는 필요 시 추가 (예: 메모리 기능)
    app = workflow.compile()
    logger.info("Gemini LangGraph compiled successfully.")
    return app
