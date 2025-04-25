
import google.generativeai as genai
from langgraph.graph import StateGraph, END, START
from functools import partial
import logging
from typing import Optional, List # List 추가

from core.langgraph_state import GeminiGraphState
from core.services.config_service import ConfigService
# google.generativeai.types 임포트 유지
from google.generativeai import types
# google.api_core.exceptions 임포트 추가 (오류 처리 강화)
from google.api_core import exceptions as google_api_exceptions

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

    # 설정에서 모델명 및 API 파라미터 가져오기
    model_name = settings.gemini_default_model # settings.gemini_default_model 사용
    temperature = settings.gemini_temperature
    enable_thinking = settings.gemini_enable_thinking
    thinking_budget = settings.gemini_thinking_budget
    enable_search = settings.gemini_enable_search


    if not api_key:
        error_msg = "Gemini API Key not configured in config.yml."
        logger.error(error_msg)
        return {"error_message": error_msg, "gemini_response": "", "xml_output": "", "summary_output": ""} # 초기 상태 반환 보장
    if not model_name:
        error_msg = "Gemini default model name not configured in config.yml."
        logger.error(error_msg)
        return {"error_message": error_msg, "gemini_response": "", "xml_output": "", "summary_output": ""} # 초기 상태 반환 보장

    try:
        # API 키 설정 (호출 시마다 필요할 수 있음)
        genai.configure(api_key=api_key)
        # 모델 이름에 'models/' 접두사가 있으면 제거 (sdk 버전에 따라 다를 수 있음)
        effective_model_name = model_name.replace("models/", "")
        model = genai.GenerativeModel(effective_model_name)
        logger.info(f"Using Gemini model: {effective_model_name}")

        # --- GenerationConfig, ToolConfig, Tools 설정 분리 ---
        # 1. GenerationConfig 설정
        generation_config_params = {
            "temperature": temperature,
            "response_mime_type": "text/plain",
            # max_output_tokens, stop_sequences 등 필요시 추가
        }
        try:
            # 올바른 클래스명 사용: GenerationConfig
            generation_config = types.GenerationConfig(**generation_config_params)
            logger.info(f"Generation Config: {generation_config}")
        except AttributeError:
            logger.error("AttributeError: 'types' module has no attribute 'GenerationConfig'. Check google-generativeai library version.")
            return {"error_message": "Failed to create GenerationConfig due to AttributeError", "gemini_response": "", "xml_output": "", "summary_output": ""}
        except Exception as e:
            logger.error(f"Error creating GenerationConfig: {e}")
            return {"error_message": f"Error creating GenerationConfig: {e}", "gemini_response": "", "xml_output": "", "summary_output": ""}


        # 2. Tools 설정
        tools_list: Optional[List[types.Tool]] = None
        if enable_search:
            try:
                tools_list = [types.Tool(google_search=types.GoogleSearch())]
                logger.info("Google Search tool enabled.")
            except AttributeError:
                 logger.error("AttributeError: 'types' module has no attribute 'Tool' or 'GoogleSearch'. Check google-generativeai library version or usage.")
                 tools_list = None # 명시적으로 None 설정
            except Exception as e:
                 logger.error(f"Error creating GoogleSearch tool: {e}")
                 tools_list = None

        # 3. ToolConfig 설정 (Thinking 포함)
        tool_config_obj: Optional[types.ToolConfig] = None
        if enable_thinking:
            try:
                # thinking_config는 ToolConfig 내부에 설정
                thinking_config_obj = types.ThinkingConfig(thinking_budget=thinking_budget)
                tool_config_obj = types.ToolConfig(thinking_config=thinking_config_obj)
                logger.info(f"ThinkingConfig enabled with budget: {thinking_budget}")
            except AttributeError:
                 logger.error("AttributeError: 'types' module has no attribute 'ThinkingConfig' or 'ToolConfig'. Check google-generativeai library version.")
                 tool_config_obj = None # 명시적으로 None 설정
            except Exception as e:
                 logger.error(f"Error creating ThinkingConfig/ToolConfig: {e}")
                 tool_config_obj = None
        # --- 설정 분리 완료 ---


        logger.info(f"Sending prompt to Gemini model: {effective_model_name}")
        # 스트리밍 API 호출 (인자 구조 변경)
        response = model.generate_content(
            prompt,
            generation_config=generation_config, # GenerationConfig 전달
            tools=tools_list,                   # Tools 리스트 전달 (None 가능)
            tool_config=tool_config_obj,        # ToolConfig 전달 (None 가능)
            # safety_settings 등 다른 옵션 필요 시 추가
            stream=True # 스트리밍 활성화
        )

        # 스트림 응답을 모아서 처리
        gemini_response_text = ""
        for chunk in response:
            # chunk에 text 속성이 없을 수 있으므로 확인
            if hasattr(chunk, 'text'):
                gemini_response_text += chunk.text
            # TODO: chunk에서 오류나 차단 정보도 확인 가능 (예: chunk.candidates[0].finish_reason)

        # 응답 스트림 완료 후 오류 처리 확인
        if not gemini_response_text.strip():
             error_detail = "Unknown reason (empty response)"
             try:
                 # response 객체 또는 마지막 chunk에서 feedback 확인 (SDK 구조에 따라 다름)
                 # 예: if response.prompt_feedback.block_reason: error_detail = ...
                 pass # 실제 SDK 구조 확인 필요
             except Exception:
                 pass # 오류 정보 추출 실패 시 무시

             error_msg = f"Gemini API call returned empty response. Detail: {error_detail}"
             logger.warning(error_msg)
             return {"gemini_response": "", "error_message": error_msg, "xml_output": "", "summary_output": ""}


        logger.info("--- Gemini Response Received ---")
        # 성공 시 텍스트 추출
        return {"gemini_response": gemini_response_text, "error_message": None, "xml_output": "", "summary_output": ""} # 초기 상태 반환 보장

    except google_api_exceptions.PermissionDenied as e:
        error_msg = f"Gemini API Permission Denied: {str(e)}. Check API key and permissions."
        logger.error(error_msg)
        return {"gemini_response": "", "error_message": error_msg, "xml_output": "", "summary_output": ""}
    except google_api_exceptions.InvalidArgument as e:
        error_msg = f"Gemini API Invalid Argument: {str(e)}. Check model name ('{effective_model_name}') or parameters."
        logger.error(error_msg)
        return {"gemini_response": "", "error_message": error_msg, "xml_output": "", "summary_output": ""}
    except AttributeError as e:
        # types.ThinkingConfig 등 SDK 내부 구조 관련 오류
        error_msg = f"Gemini SDK AttributeError: {str(e)}. Check library version and code compatibility."
        logger.exception(error_msg) # 스택 트레이스 포함
        return {"gemini_response": "", "error_message": error_msg, "xml_output": "", "summary_output": ""}
    except Exception as e:
        error_msg = f"Error calling Gemini API: {str(e)}"
        logger.exception(error_msg) # 스택 트레이스 포함 로깅
        return {"gemini_response": "", "error_message": error_msg, "xml_output": "", "summary_output": ""}


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
    # process_response는 API 호출 성공 후 실행되므로, 여기서 error_message는 None으로 시작
    error_message = None # API 호출 성공 시 오류 없음

    try:
        if not gemini_response:
             logger.warning("Gemini response is empty, skipping processing.")
             # API 호출은 성공했으나 응답이 비어있는 경우, 오류 메시지 설정 가능
             error_message = "Gemini response was empty after successful API call."
             # 상태 반환 시 gemini_response 유지
             return {"xml_output": "", "summary_output": "", "error_message": error_message, "gemini_response": gemini_response}


        # 응답 문자열을 정리 (앞뒤 공백 제거)
        cleaned_response = gemini_response.strip()

        # 응답 끝에서부터 <summary> 태그 찾기
        summary_start_tag = "<summary>"
        summary_end_tag = "</summary>"
        summary_start_index = cleaned_response.rfind(summary_start_tag) # 오른쪽에서부터 찾기

        # <summary> 태그가 응답의 합리적인 위치(예: 끝 부분)에 있는지 확인
        is_valid_summary_position = (
            summary_start_index != -1 and
            summary_start_index > 0 and
            summary_start_index > len(cleaned_response) * 0.5
        )

        if is_valid_summary_position:
            xml_output = cleaned_response[:summary_start_index].strip()
            summary_part = cleaned_response[summary_start_index + len(summary_start_tag):]
            summary_end_index = summary_part.rfind(summary_end_tag)
            if summary_end_index != -1:
                 summary_output = summary_part[:summary_end_index].strip()
            else:
                 summary_output = summary_part.strip()
                 logger.warning("Summary end tag '</summary>' not found at the end of the summary part. Taking content after '<summary>'.")

            if xml_output.endswith(summary_end_tag):
                xml_output = xml_output[:-len(summary_end_tag)].strip()
                logger.warning("Removed trailing '</summary>' tag from the XML part.")

        else:
            xml_output = cleaned_response
            if summary_start_index == -1:
                summary_output = "Summary tag '<summary>' not found in response."
            else:
                summary_output = f"Summary tag '<summary>' found at index {summary_start_index}, which is considered too early. Treating entire response as XML."
            logger.warning(summary_output)

        logger.info("--- Response Processed ---")
        # 파싱 성공 시 오류 메시지는 None 유지, gemini_response 유지
        return {"xml_output": xml_output, "summary_output": summary_output, "error_message": None, "gemini_response": gemini_response}

    except Exception as e:
        error_msg = f"Error processing response: {str(e)}"
        logger.exception(error_msg)
        # 파싱 오류 발생 시 원본 응답을 XML로, 빈 Summary 반환, 오류 메시지 설정, gemini_response 유지
        return {"xml_output": gemini_response, "summary_output": "", "error_message": error_msg, "gemini_response": gemini_response}


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
