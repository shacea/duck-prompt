
import google.generativeai as genai
from langgraph.graph import StateGraph, END, START
from functools import partial
import logging
from typing import Optional, List, Dict, Any, Union
import base64
import mimetypes
import os
import datetime # datetime 모듈 임포트

from core.langgraph_state import GeminiGraphState
from core.services.config_service import ConfigService
from google.generativeai import types
from google.api_core import exceptions as google_api_exceptions

logger = logging.getLogger(__name__)

# --- LangGraph 노드 함수 ---

def call_gemini(state: GeminiGraphState, config_service: ConfigService) -> GeminiGraphState:
    """
    Gemini API를 호출하는 노드 (멀티모달 지원)
    'types.Part' 오류를 피하기 위해 contents를 문자열과 딕셔너리 리스트로 구성합니다.
    API 키 및 파라미터는 ConfigService를 통해 로드합니다.
    API 호출 시작 시간과 경과 시간을 로깅합니다.
    """
    print("--- Calling Gemini API (Multimodal) ---")
    logger.info("Calling Gemini API node (Multimodal)")
    start_time = datetime.datetime.now() # API 호출 시작 시간 기록
    logger.info(f"Gemini API 호출 시작 시간: {start_time.strftime('%H:%M:%S')}")

    text_prompt = state['input_prompt']
    attachments = state.get('input_attachments', [])
    settings = config_service.get_settings() # Get settings from DB via service

    # API 키는 settings 객체에서 직접 가져옴
    api_key = settings.gemini_api_key

    # 설정에서 모델명 및 API 파라미터 가져오기
    model_name = state.get('selected_model_name', settings.gemini_default_model)
    temperature = settings.gemini_temperature
    enable_thinking = settings.gemini_enable_thinking
    thinking_budget = settings.gemini_thinking_budget
    enable_search = settings.gemini_enable_search

    # 초기 상태 반환 보장용 기본값
    default_return_state: GeminiGraphState = {
        "input_prompt": text_prompt,
        "input_attachments": attachments,
        "selected_model_name": model_name,
        "gemini_response": "",
        "xml_output": "",
        "summary_output": "",
        "error_message": None
    }

    if not api_key:
        error_msg = "Gemini API Key not found in database configuration."
        logger.error(error_msg)
        default_return_state["error_message"] = error_msg
        return default_return_state
    if not model_name:
        error_msg = "Gemini model name not provided or configured in database."
        logger.error(error_msg)
        default_return_state["error_message"] = error_msg
        return default_return_state

    effective_model_name = ""
    gemini_response_text = "" # 응답 텍스트 초기화
    try:
        # API 키 설정 (호출 시마다 설정하는 것이 안전할 수 있음)
        genai.configure(api_key=api_key)
        effective_model_name = model_name.replace("models/", "")
        model = genai.GenerativeModel(effective_model_name)
        logger.info(f"Using Gemini model: {effective_model_name}")

        # --- GenerationConfig, ToolConfig, Tools 설정 분리 ---
        generation_config_params = {
            "temperature": temperature,
            "response_mime_type": "text/plain",
        }
        try:
            generation_config = types.GenerationConfig(**generation_config_params)
            logger.info(f"Generation Config: {generation_config}")
        except AttributeError:
            logger.error("AttributeError: 'types' module has no attribute 'GenerationConfig'. Check google-generativeai library version.")
            default_return_state["error_message"] = "Failed to create GenerationConfig due to AttributeError"
            return default_return_state
        except Exception as e:
            logger.error(f"Error creating GenerationConfig: {e}")
            default_return_state["error_message"] = f"Error creating GenerationConfig: {e}"
            return default_return_state

        tools_list: Optional[List[types.Tool]] = None
        if enable_search:
            try:
                 tools_list = [types.Tool(google_search=types.GoogleSearch())]
                 logger.info("Attempting to enable Google Search tool.")
            except AttributeError:
                 logger.warning("AttributeError: 'types' module might lack 'Tool' or 'GoogleSearch'. Search might not work.")
                 tools_list = None
            except Exception as e:
                 logger.error(f"Error creating GoogleSearch tool: {e}")
                 tools_list = None

        tool_config_obj: Optional[types.ToolConfig] = None
        if enable_thinking:
            try:
                thinking_config_obj = types.ThinkingConfig(thinking_budget=thinking_budget)
                tool_config_obj = types.ToolConfig(thinking_config=thinking_config_obj)
                logger.info(f"ThinkingConfig enabled with budget: {thinking_budget}")
            except AttributeError:
                 logger.warning("AttributeError: 'types' module might lack 'ThinkingConfig' or 'ToolConfig'. Thinking feature might not work.")
                 tool_config_obj = None
            except Exception as e:
                 logger.error(f"Error creating ThinkingConfig/ToolConfig: {e}")
                 tool_config_obj = None
        # --- 설정 분리 완료 ---

        # --- Contents 구성 (텍스트 + 첨부 파일/이미지) ---
        contents_list: List[Union[str, Dict[str, Any]]] = []
        if text_prompt:
            contents_list.append(text_prompt)
            logger.info(f"Added text prompt part (length: {len(text_prompt)}).")

        if attachments:
            for attachment in attachments:
                item_type = attachment.get('type')
                item_name = attachment.get('name', 'unknown')
                item_data = attachment.get('data')
                item_path = attachment.get('path')

                if not item_data and item_path and os.path.exists(item_path):
                    try:
                        with open(item_path, 'rb') as f:
                            item_data = f.read()
                        logger.info(f"Read data from attachment path: {item_path}")
                    except Exception as e:
                        logger.error(f"Failed to read attachment data from path {item_path}: {e}")
                        continue

                if not item_data:
                    logger.warning(f"Skipping attachment '{item_name}': No data found.")
                    continue

                mime_type = None
                if item_type == 'image':
                    if item_name.lower().endswith('.png'): mime_type = 'image/png'
                    elif item_name.lower().endswith(('.jpg', '.jpeg')): mime_type = 'image/jpeg'
                    elif item_name.lower().endswith('.webp'): mime_type = 'image/webp'
                    elif item_name.lower().endswith('.gif'): mime_type = 'image/gif'
                    else: mime_type = 'application/octet-stream'
                    logger.info(f"Adding image attachment as dict: {item_name} (MIME: {mime_type}, Size: {len(item_data)} bytes)")
                    contents_list.append({"mime_type": mime_type, "data": item_data})
                elif item_type == 'file':
                    mime_type, _ = mimetypes.guess_type(item_name)
                    if not mime_type: mime_type = 'application/octet-stream'
                    logger.info(f"Adding file attachment as dict: {item_name} (MIME: {mime_type}, Size: {len(item_data)} bytes)")
                    contents_list.append({"mime_type": mime_type, "data": item_data})
                else:
                    logger.warning(f"Unknown attachment type '{item_type}' for item '{item_name}'. Skipping.")

        if not contents_list:
             error_msg = "No content (text or attachments) to send to Gemini."
             logger.error(error_msg)
             default_return_state["error_message"] = error_msg
             return default_return_state
        # --- Contents 구성 완료 ---


        logger.info(f"Sending {len(contents_list)} parts to Gemini model: {effective_model_name} (using direct list)")
        response = model.generate_content(
            contents=contents_list,
            generation_config=generation_config,
            tools=tools_list,
            tool_config=tool_config_obj,
            stream=True
        )

        # --- 스트림 응답 처리 ---
        # gemini_response_text = "" # 위에서 초기화
        specific_error_occurred = False
        error_details = ""
        for chunk in response:
            try:
                gemini_response_text += chunk.text
            except ValueError as e:
                if "response.text` quick accessor" in str(e) or "candidate.text`" in str(e):
                    func_calls = getattr(chunk, 'function_calls', None)
                    if func_calls:
                        error_msg = f"Gemini API 응답 처리 중 Function Call 발생 (무시됨): {func_calls}"
                        logger.warning(error_msg)
                        error_details += f"\n- Function Call 무시: {func_calls}"
                    else:
                        error_msg = f"Gemini API 응답 처리 오류 (chunk.text 접근 불가): {str(e)}"
                        logger.warning(error_msg)
                        error_details += f"\n- 청크 오류: {e}"
                    specific_error_occurred = True
                    continue
                else:
                    logger.exception(f"Unexpected ValueError processing chunk: {e}")
                    error_details += f"\n- 예상치 못한 청크 값 오류: {e}"
                    specific_error_occurred = True
                    continue
            except Exception as e:
                 logger.exception(f"Unexpected error processing chunk: {e}")
                 error_details += f"\n- 예상치 못한 청크 처리 오류: {e}"
                 specific_error_occurred = True
                 continue
        # --- 스트림 처리 완료 ---

        if specific_error_occurred:
             user_error_msg = "Gemini API 응답 문제 발생. 일부 내용이 누락되었거나 Function Call이 포함되었을 수 있습니다."
             detailed_error_msg = user_error_msg + "\n세부 정보:" + error_details
             default_return_state["error_message"] = detailed_error_msg
             default_return_state["gemini_response"] = gemini_response_text
             logger.warning(f"Gemini stream processing encountered issues. Returning potentially partial response. Details: {error_details}")
             return default_return_state

        if not gemini_response_text.strip():
             error_detail = "Unknown reason (empty response after stream)"
             try:
                 prompt_feedback = response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'
                 error_detail = f"Prompt Feedback: {prompt_feedback}"
             except Exception as e:
                 logger.warning(f"Could not get additional details for empty response: {e}")

             error_msg = f"Gemini API 호출은 성공했으나 빈 응답을 반환했습니다. 세부 정보: {error_detail}"
             logger.warning(error_msg)
             default_return_state["gemini_response"] = ""
             default_return_state["error_message"] = error_msg
             return default_return_state

        logger.info("--- Gemini Response Received Successfully ---")
        default_return_state["gemini_response"] = gemini_response_text
        default_return_state["error_message"] = None
        return default_return_state

    except google_api_exceptions.PermissionDenied as e:
        error_msg = f"Gemini API 권한 거부: {str(e)}. API 키와 권한을 확인하세요."
        logger.error(error_msg, exc_info=True)
        default_return_state["error_message"] = error_msg
        return default_return_state
    except google_api_exceptions.InvalidArgument as e:
        error_msg = f"Gemini API 잘못된 인수: {str(e)}. 모델 이름('{effective_model_name}'), 파라미터, 또는 콘텐츠 타입/구조를 확인하세요."
        logger.error(error_msg, exc_info=True)
        default_return_state["error_message"] = error_msg
        return default_return_state
    except google_api_exceptions.ResourceExhausted as e:
        error_msg = f"Gemini API Rate Limit 초과 또는 리소스 부족: {str(e)}."
        logger.error(error_msg, exc_info=True)
        default_return_state["error_message"] = error_msg
        return default_return_state
    except AttributeError as e:
        error_msg = f"Gemini SDK 속성 오류: {str(e)}. 라이브러리 버전과 코드 호환성을 확인하세요."
        logger.exception(error_msg)
        default_return_state["error_message"] = error_msg
        return default_return_state
    except Exception as e:
        error_msg = f"Gemini API 호출 중 오류 발생: {str(e)}"
        logger.exception(error_msg)
        default_return_state["error_message"] = error_msg
        return default_return_state
    finally:
        # API 호출 완료 시간 기록 및 경과 시간 계산/출력
        end_time = datetime.datetime.now()
        elapsed_time = end_time - start_time
        # timedelta를 HH:MM:SS 형식으로 변환 (소수점 이하 제거)
        elapsed_time_str = str(elapsed_time).split('.')[0]
        logger.info(f"Gemini API 호출 종료 시간: {end_time.strftime('%H:%M:%S')}, 총 경과 시간: {elapsed_time_str}")


def process_response(state: GeminiGraphState) -> GeminiGraphState:
    """
    Gemini 응답을 XML과 Summary로 파싱하는 노드.
    응답 끝 부분의 <summary> 태그를 기준으로 분리하여 코드 내 문자열과의 혼동을 줄입니다.
    """
    print("--- Processing Gemini Response ---")
    logger.info("Processing Gemini Response node")
    gemini_response = state.get('gemini_response', '')
    xml_output = ""
    summary_output = ""
    error_message = state.get('error_message') # 이전 노드의 오류 메시지 유지

    new_state = state.copy()

    try:
        if error_message and "Gemini API 응답 문제 발생" not in error_message:
             logger.warning(f"Skipping response processing due to previous critical error: {error_message}")
             new_state["xml_output"] = ""
             new_state["summary_output"] = ""
             return new_state
        elif error_message:
             logger.warning(f"Processing potentially partial response due to stream error: {error_message}")

        if not gemini_response:
             logger.warning("Gemini response is empty, skipping processing.")
             if not error_message:
                 error_message = "Gemini response was empty after successful API call."
                 new_state["error_message"] = error_message
             new_state["xml_output"] = ""
             new_state["summary_output"] = ""
             return new_state


        cleaned_response = gemini_response.strip()
        summary_start_tag = "<summary>"
        summary_end_tag = "</summary>"
        summary_start_index = cleaned_response.rfind(summary_start_tag)
        summary_end_index = cleaned_response.rfind(summary_end_tag)

        is_valid_summary = (
            summary_start_index != -1 and
            summary_end_index != -1 and
            summary_start_index < summary_end_index and
            summary_end_index >= len(cleaned_response) - len(summary_end_tag) - 5
        )

        if is_valid_summary:
            xml_output = cleaned_response[:summary_start_index].strip()
            summary_output = cleaned_response[summary_start_index + len(summary_start_tag):summary_end_index].strip()
            logger.info("Successfully parsed XML and Summary parts.")
        else:
            xml_output = cleaned_response
            summary_output = "Summary tag not found or improperly placed in the response."
            logger.warning(summary_output)

        logger.info("--- Response Processed ---")
        new_state["xml_output"] = xml_output
        new_state["summary_output"] = summary_output
        # Clear error message if processing was successful despite earlier stream warnings
        if error_message and "Gemini API 응답 문제 발생" in error_message:
             new_state["error_message"] = None # Clear non-critical stream error after processing
        return new_state

    except Exception as e:
        error_msg = f"Error processing response: {str(e)}"
        logger.exception(error_msg)
        new_state["xml_output"] = gemini_response # Return raw response in XML field on error
        new_state["summary_output"] = f"응답 처리 오류: {e}" # Put error in summary
        new_state["error_message"] = (error_message + "\n" + error_msg) if error_message else error_msg
        return new_state


def build_gemini_graph(config_service: ConfigService) -> StateGraph:
    """
    Gemini API 호출 및 처리 LangGraph를 빌드합니다.
    ConfigService를 주입받아 노드에서 사용합니다.
    """
    workflow = StateGraph(GeminiGraphState)

    # Bind the config_service to the node function
    bound_call_gemini = partial(call_gemini, config_service=config_service)

    workflow.add_node("call_gemini", bound_call_gemini)
    workflow.add_node("process_response", process_response)

    workflow.add_edge(START, "call_gemini")
    workflow.add_edge("call_gemini", "process_response")
    workflow.add_edge("process_response", END)

    app = workflow.compile()
    logger.info("Gemini LangGraph compiled successfully.")
    return app

