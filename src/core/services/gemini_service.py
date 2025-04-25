
import google.generativeai as genai
from langgraph.graph import StateGraph, END, START
from functools import partial
import logging
from typing import Optional, List, Dict, Any, Union
import base64
import mimetypes
import os
import datetime # datetime 모듈 임포트
import time # 시간 측정용

from core.langgraph_state import GeminiGraphState
from core.services.config_service import ConfigService
from core.services.db_service import DbService # DbService 임포트
from google.generativeai import types
from google.api_core import exceptions as google_api_exceptions

logger = logging.getLogger(__name__)

# --- LangGraph 노드 함수 ---

def call_gemini(state: GeminiGraphState, config_service: ConfigService) -> GeminiGraphState:
    """
    Gemini API를 호출하는 노드 (멀티모달 지원)
    'types.Part' 오류를 피하기 위해 contents를 문자열과 딕셔너리 리스트로 구성합니다.
    API 키 및 파라미터는 ConfigService를 통해 로드합니다.
    API 호출 시작 시간과 경과 시간을 로깅하고, DB에 로그를 기록합니다.
    """
    print("--- Calling Gemini API (Multimodal) ---")
    logger.info("Calling Gemini API node (Multimodal)")
    start_time_mono = time.monotonic() # 경과 시간 측정용 (monotonic clock)
    request_timestamp = datetime.datetime.now(datetime.timezone.utc) # DB 기록용 타임스탬프
    logger.info(f"Gemini API 호출 시작 시간: {request_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    text_prompt = state['input_prompt']
    attachments = state.get('input_attachments', [])
    settings = config_service.get_settings() # Get settings from DB via service
    db_service: DbService = config_service.db_service # DbService 인스턴스 가져오기

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

    # --- DB 로깅 준비 ---
    log_id: Optional[int] = None
    api_key_id: Optional[int] = None
    if db_service:
        try:
            api_key_id = db_service.get_api_key_id(api_key)
            log_id = db_service.log_gemini_request(
                model_name=model_name,
                request_prompt=text_prompt,
                request_attachments=attachments,
                api_key_id=api_key_id
            )
        except Exception as db_err:
            logger.error(f"Failed to log Gemini request to DB: {db_err}", exc_info=True)
            # DB 로깅 실패가 API 호출을 막아서는 안 됨
    # --- DB 로깅 준비 완료 ---

    if not api_key:
        error_msg = "Gemini API Key not found in database configuration."
        logger.error(error_msg)
        default_return_state["error_message"] = error_msg
        # DB 로그 업데이트 (오류)
        if db_service and log_id is not None:
            elapsed_ms = int((time.monotonic() - start_time_mono) * 1000)
            db_service.update_gemini_log(log_id, None, None, None, error_msg, elapsed_ms, None)
        return default_return_state
    if not model_name:
        error_msg = "Gemini model name not provided or configured in database."
        logger.error(error_msg)
        default_return_state["error_message"] = error_msg
        # DB 로그 업데이트 (오류)
        if db_service and log_id is not None:
            elapsed_ms = int((time.monotonic() - start_time_mono) * 1000)
            db_service.update_gemini_log(log_id, None, None, None, error_msg, elapsed_ms, None)
        return default_return_state

    effective_model_name = ""
    gemini_response_text = "" # 응답 텍스트 초기화
    api_error_message: Optional[str] = None # API 호출 결과 오류 메시지

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
            api_error_message = "Failed to create GenerationConfig due to AttributeError"
            logger.error("AttributeError: 'types' module has no attribute 'GenerationConfig'. Check google-generativeai library version.")
            raise ValueError(api_error_message) # Raise to be caught by outer try-except
        except Exception as e:
            api_error_message = f"Error creating GenerationConfig: {e}"
            logger.error(api_error_message)
            raise ValueError(api_error_message) # Raise to be caught by outer try-except

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
             api_error_message = "No content (text or attachments) to send to Gemini."
             logger.error(api_error_message)
             raise ValueError(api_error_message) # Raise to be caught by outer try-except
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
             api_error_message = user_error_msg + "\n세부 정보:" + error_details
             logger.warning(f"Gemini stream processing encountered issues. Returning potentially partial response. Details: {error_details}")
             # 오류가 발생했지만 부분 응답은 있을 수 있으므로, 오류 메시지만 설정하고 반환
             default_return_state["error_message"] = api_error_message
             default_return_state["gemini_response"] = gemini_response_text # 부분 응답 저장
             # DB 로그 업데이트 (오류 포함) - finally 블록에서 처리

        elif not gemini_response_text.strip():
             error_detail = "Unknown reason (empty response after stream)"
             try:
                 prompt_feedback = response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'
                 error_detail = f"Prompt Feedback: {prompt_feedback}"
             except Exception as e:
                 logger.warning(f"Could not get additional details for empty response: {e}")

             api_error_message = f"Gemini API 호출은 성공했으나 빈 응답을 반환했습니다. 세부 정보: {error_detail}"
             logger.warning(api_error_message)
             default_return_state["gemini_response"] = ""
             default_return_state["error_message"] = api_error_message
             # DB 로그 업데이트 (오류 포함) - finally 블록에서 처리

        else:
            logger.info("--- Gemini Response Received Successfully ---")
            default_return_state["gemini_response"] = gemini_response_text
            default_return_state["error_message"] = None # 성공 시 오류 없음
            # DB 로그 업데이트 (성공) - finally 블록에서 처리

        return default_return_state

    except google_api_exceptions.PermissionDenied as e:
        api_error_message = f"Gemini API 권한 거부: {str(e)}. API 키와 권한을 확인하세요."
        logger.error(api_error_message, exc_info=True)
        default_return_state["error_message"] = api_error_message
        return default_return_state
    except google_api_exceptions.InvalidArgument as e:
        api_error_message = f"Gemini API 잘못된 인수: {str(e)}. 모델 이름('{effective_model_name}'), 파라미터, 또는 콘텐츠 타입/구조를 확인하세요."
        logger.error(api_error_message, exc_info=True)
        default_return_state["error_message"] = api_error_message
        return default_return_state
    except google_api_exceptions.ResourceExhausted as e:
        api_error_message = f"Gemini API Rate Limit 초과 또는 리소스 부족: {str(e)}."
        logger.error(api_error_message, exc_info=True)
        default_return_state["error_message"] = api_error_message
        return default_return_state
    except AttributeError as e:
        api_error_message = f"Gemini SDK 속성 오류: {str(e)}. 라이브러리 버전과 코드 호환성을 확인하세요."
        logger.exception(api_error_message)
        default_return_state["error_message"] = api_error_message
        return default_return_state
    except ValueError as e: # Catch specific ValueErrors raised internally
        api_error_message = str(e) # Use the error message from the raised exception
        logger.error(f"Gemini API call pre-check failed: {api_error_message}")
        default_return_state["error_message"] = api_error_message
        return default_return_state
    except Exception as e:
        api_error_message = f"Gemini API 호출 중 오류 발생: {str(e)}"
        logger.exception(api_error_message)
        default_return_state["error_message"] = api_error_message
        return default_return_state
    finally:
        # API 호출 완료 시간 기록 및 경과 시간 계산/출력
        end_time_mono = time.monotonic()
        elapsed_ms = int((end_time_mono - start_time_mono) * 1000)
        response_timestamp = datetime.datetime.now(datetime.timezone.utc)
        elapsed_time_str = str(datetime.timedelta(milliseconds=elapsed_ms)).split('.')[0]
        logger.info(f"Gemini API 호출 종료 시간: {response_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}, 총 경과 시간: {elapsed_time_str}")

        # --- DB 로그 업데이트 (성공/오류 모두) ---
        if db_service and log_id is not None:
            try:
                # process_response 노드에서 파싱된 xml/summary는 아직 없으므로 None 전달
                # 토큰 카운트도 여기서 직접 알 수 없으므로 None 전달
                db_service.update_gemini_log(
                    log_id=log_id,
                    response_text=gemini_response_text, # 원시 응답 저장
                    response_xml=None, # 파싱 전
                    response_summary=None, # 파싱 전
                    error_message=api_error_message, # 최종 오류 메시지
                    elapsed_time_ms=elapsed_ms,
                    token_count=None # 토큰 카운트 정보 없음
                )
            except Exception as db_err:
                logger.error(f"Failed to update Gemini log ID {log_id} in DB: {db_err}", exc_info=True)
        # --- DB 로그 업데이트 완료 ---


def process_response(state: GeminiGraphState) -> GeminiGraphState:
    """
    Gemini 응답을 XML과 Summary로 파싱하는 노드.
    응답 끝 부분의 <summary> 태그를 기준으로 분리하여 코드 내 문자열과의 혼동을 줄입니다.
    (DB 로깅은 call_gemini 노드에서 처리하므로 여기서는 파싱만 수행)
    """
    print("--- Processing Gemini Response ---")
    logger.info("Processing Gemini Response node")
    gemini_response = state.get('gemini_response', '')
    xml_output = ""
    summary_output = ""
    error_message = state.get('error_message') # 이전 노드의 오류 메시지 유지

    new_state = state.copy()

    try:
        # 이전 노드에서 심각한 오류가 발생했다면 (부분 응답 오류 제외) 처리 건너뛰기
        if error_message and "Gemini API 응답 문제 발생" not in error_message:
             logger.warning(f"Skipping response processing due to previous critical error: {error_message}")
             new_state["xml_output"] = ""
             new_state["summary_output"] = ""
             return new_state
        elif error_message:
             logger.warning(f"Processing potentially partial response due to stream error: {error_message}")

        if not gemini_response:
             logger.warning("Gemini response is empty, skipping processing.")
             # 이전 노드에서 오류가 없었는데 응답이 비었다면 새로운 오류 메시지 설정
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
            # summary 태그가 응답 끝 부분에 있는지 좀 더 관대하게 확인 (약간의 후행 공백 허용)
            summary_end_index >= len(cleaned_response) - len(summary_end_tag) - 10 # Allow for some trailing whitespace/newlines
        )

        if is_valid_summary:
            xml_output = cleaned_response[:summary_start_index].strip()
            summary_output = cleaned_response[summary_start_index + len(summary_start_tag):summary_end_index].strip()
            logger.info("Successfully parsed XML and Summary parts.")
        else:
            # summary 태그가 없거나 잘못된 위치에 있으면 전체를 xml로 간주
            xml_output = cleaned_response
            summary_output = "Summary tag not found or improperly placed in the response."
            logger.warning(summary_output)
            # 이 경우를 오류로 처리할지 여부 결정 (현재는 경고만)
            # if not error_message: # 이전 오류가 없었다면 파싱 실패를 오류로 설정 가능
            #     new_state["error_message"] = summary_output

        logger.info("--- Response Processed ---")
        new_state["xml_output"] = xml_output
        new_state["summary_output"] = summary_output
        # 스트림 오류가 있었지만 파싱이 성공적으로 완료되었다면, 해당 오류 메시지는 유지하거나 제거할 수 있음
        # 여기서는 유지하여 사용자에게 알림 (심각하지 않은 오류로 간주)
        # if error_message and "Gemini API 응답 문제 발생" in error_message:
        #      new_state["error_message"] = None # Clear non-critical stream error after processing

        # TODO: 파싱된 XML/Summary 결과를 DB 로그에 업데이트? (현재는 call_gemini에서 원시 응답만 저장)
        # 만약 업데이트하려면 log_id를 state에 포함시켜 전달해야 함.

        return new_state

    except Exception as e:
        error_msg = f"Error processing response: {str(e)}"
        logger.exception(error_msg)
        new_state["xml_output"] = gemini_response # Return raw response in XML field on error
        new_state["summary_output"] = f"응답 처리 오류: {e}" # Put error in summary
        # 기존 오류 메시지에 처리 오류 추가
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
            