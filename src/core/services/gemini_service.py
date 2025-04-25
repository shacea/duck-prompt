
import google.generativeai as genai
from langgraph.graph import StateGraph, END, START
from functools import partial
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
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

# --- Rate Limit Check Helper (이제 DbService.is_key_rate_limited 사용) ---
# def check_rate_limit(db_service: DbService, api_key_id: int, model_name: str) -> Tuple[bool, str]:
#     """ (사용 안 함) Checks if the API key is within the rate limits for the given model. """
#     # ... (이전 로직 제거) ...


# --- LangGraph 노드 함수 ---

def call_gemini(state: GeminiGraphState, config_service: ConfigService) -> GeminiGraphState:
    """
    Gemini API를 호출하는 노드 (멀티모달 지원).
    Rate Limit을 체크하고, 초과 시 다른 활성 키로 전환을 시도합니다.
    성공 시 사용된 키를 ConfigService에 업데이트합니다.
    """
    print("--- Calling Gemini API (Multimodal) ---")
    logger.info("Calling Gemini API node (Multimodal)")
    start_time_mono = time.monotonic()
    request_timestamp = datetime.datetime.now(datetime.timezone.utc)
    logger.info(f"Gemini API 호출 시작 시간: {request_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    text_prompt = state['input_prompt']
    attachments = state.get('input_attachments', [])
    settings = config_service.get_settings()
    db_service: DbService = config_service.db_service

    # 설정에서 모델명 가져오기 (API 키는 루프 안에서 결정)
    model_name = state.get('selected_model_name', settings.gemini_default_model)
    temperature = settings.gemini_temperature
    enable_thinking = settings.gemini_enable_thinking
    thinking_budget = settings.gemini_thinking_budget
    enable_search = settings.gemini_enable_search

    # 초기 상태 반환용 기본값
    default_return_state: GeminiGraphState = {
        "input_prompt": text_prompt, "input_attachments": attachments,
        "selected_model_name": model_name, "gemini_response": "",
        "xml_output": "", "summary_output": "", "error_message": None, "log_id": None
    }

    if not model_name:
        error_msg = "Gemini model name not provided or configured."
        logger.error(error_msg)
        default_return_state["error_message"] = error_msg
        return default_return_state

    # --- API 키 순환 및 Rate Limit 체크 루프 ---
    active_keys = db_service.get_active_api_keys('google')
    if not active_keys:
        error_msg = "No active Gemini API Keys found in database configuration."
        logger.error(error_msg)
        default_return_state["error_message"] = error_msg
        return default_return_state

    # 시작 인덱스 결정: 현재 ConfigService에 설정된 키가 있다면 그 키부터 시도
    current_key_id_in_config = config_service.get_current_gemini_key_id()
    start_index = 0
    if current_key_id_in_config:
        for idx, key_info in enumerate(active_keys):
            if key_info['id'] == current_key_id_in_config:
                start_index = idx
                logger.info(f"Starting key check from currently configured Key ID: {current_key_id_in_config} (Index: {start_index})")
                break

    current_key_index = start_index
    selected_key_info: Optional[Dict[str, Any]] = None
    api_key_id: Optional[int] = None
    log_id: Optional[int] = None
    final_error_message: Optional[str] = None
    api_call_successful = False # API 호출 성공 여부 플래그

    for i in range(len(active_keys)):
        # 순환 인덱스 계산
        check_index = (start_index + i) % len(active_keys)
        selected_key_info = active_keys[check_index]
        api_key = selected_key_info['api_key']
        api_key_id = selected_key_info['id']
        logger.info(f"Attempting to use Gemini API Key ID: {api_key_id} (Index: {check_index})")

        # Rate Limit 체크 (DbService 사용)
        is_limited, reason = db_service.is_key_rate_limited(api_key_id, model_name)
        if is_limited:
            logger.warning(f"Rate limit check failed for key ID {api_key_id}: {reason}")
            final_error_message = f"Rate limit exceeded for key ID {api_key_id}: {reason}"
            # 다음 키 시도 (루프 계속)
            continue

        # Rate Limit 통과, 이 키로 API 호출 시도
        logger.info(f"Rate limit check passed for key ID {api_key_id}. Proceeding with API call.")

        # --- DB 로깅 준비 (선택된 키 사용) ---
        try:
            log_id = db_service.log_gemini_request(
                model_name=model_name, request_prompt=text_prompt,
                request_attachments=attachments, api_key_id=api_key_id
            )
            default_return_state["log_id"] = log_id # 생성된 log_id를 상태에 저장
        except Exception as db_err:
            logger.error(f"Failed to log Gemini request to DB for key ID {api_key_id}: {db_err}", exc_info=True)
            log_id = None # 로깅 실패 시에도 API 호출은 계속 시도
        # --- DB 로깅 준비 완료 ---

        effective_model_name = ""
        gemini_response_text = ""
        api_error_message: Optional[str] = None
        # api_call_successful 플래그는 루프 시작 시 False로 초기화됨

        try:
            genai.configure(api_key=api_key)
            effective_model_name = model_name.replace("models/", "")
            model = genai.GenerativeModel(effective_model_name)
            logger.info(f"Using Gemini model: {effective_model_name} with key ID: {api_key_id}")

            # GenerationConfig, ToolConfig, Tools 설정 (이전과 동일)
            generation_config_params = {"temperature": temperature, "response_mime_type": "text/plain"}
            try: generation_config = types.GenerationConfig(**generation_config_params)
            except AttributeError: raise ValueError("Failed to create GenerationConfig (AttributeError)")
            except Exception as e: raise ValueError(f"Error creating GenerationConfig: {e}")

            tools_list: Optional[List[types.Tool]] = None
            if enable_search:
                try: tools_list = [types.Tool(google_search=types.GoogleSearch())]
                except AttributeError: logger.warning("Search tool creation failed (AttributeError)")
                except Exception as e: logger.error(f"Error creating GoogleSearch tool: {e}")

            tool_config_obj: Optional[types.ToolConfig] = None
            if enable_thinking:
                try:
                    thinking_config_obj = types.ThinkingConfig(thinking_budget=thinking_budget)
                    tool_config_obj = types.ToolConfig(thinking_config=thinking_config_obj)
                except AttributeError: logger.warning("Thinking config creation failed (AttributeError)")
                except Exception as e: logger.error(f"Error creating ThinkingConfig/ToolConfig: {e}")

            # Contents 구성 (이전과 동일)
            contents_list: List[Union[str, Dict[str, Any]]] = []
            if text_prompt: contents_list.append(text_prompt)
            if attachments:
                for attachment in attachments:
                    item_type = attachment.get('type'); item_name = attachment.get('name', 'unknown')
                    item_data = attachment.get('data'); item_path = attachment.get('path')
                    if not item_data and item_path and os.path.exists(item_path):
                        try:
                            with open(item_path, 'rb') as f: item_data = f.read()
                        except Exception as e: logger.error(f"Failed to read attachment {item_path}: {e}"); continue
                    if not item_data: logger.warning(f"Skipping attachment '{item_name}': No data."); continue
                    mime_type = None
                    if item_type == 'image':
                        if item_name.lower().endswith('.png'): mime_type = 'image/png'
                        elif item_name.lower().endswith(('.jpg', '.jpeg')): mime_type = 'image/jpeg'
                        elif item_name.lower().endswith('.webp'): mime_type = 'image/webp'
                        else: mime_type = 'application/octet-stream'
                        contents_list.append({"mime_type": mime_type, "data": item_data})
                    elif item_type == 'file':
                        mime_type, _ = mimetypes.guess_type(item_name)
                        if not mime_type: mime_type = 'application/octet-stream'
                        contents_list.append({"mime_type": mime_type, "data": item_data})

            if not contents_list: raise ValueError("No content (text or attachments) to send.")

            # API 호출 (스트림)
            logger.info(f"Sending {len(contents_list)} parts to Gemini model: {effective_model_name} (using key ID: {api_key_id})")
            response = model.generate_content(
                contents=contents_list, generation_config=generation_config,
                tools=tools_list, tool_config=tool_config_obj, stream=True
            )

            # 스트림 응답 처리 (이전과 동일)
            specific_error_occurred = False; error_details = ""
            for chunk in response:
                try: gemini_response_text += chunk.text
                except ValueError as e:
                    if "response.text` quick accessor" in str(e) or "candidate.text`" in str(e):
                        func_calls = getattr(chunk, 'function_calls', None)
                        msg = f"Function Call ignored: {func_calls}" if func_calls else f"Chunk text access error: {e}"
                        logger.warning(msg); error_details += f"\n- {msg}"; specific_error_occurred = True; continue
                    else: raise
                except Exception as e: logger.exception(f"Unexpected chunk error: {e}"); error_details += f"\n- Chunk error: {e}"; specific_error_occurred = True; continue

            # 결과 처리
            if specific_error_occurred:
                api_error_message = "Gemini API 응답 문제 발생. 일부 내용 누락 또는 Function Call 포함 가능." + "\n세부 정보:" + error_details
                logger.warning(f"Gemini stream processing issues. Details: {error_details}")
                default_return_state["error_message"] = api_error_message
                default_return_state["gemini_response"] = gemini_response_text # 부분 응답 저장
                # 오류가 있었지만 API 호출 자체는 성공했을 수 있음 (Rate Limit 오류 아님)
                api_call_successful = True # 부분 성공으로 간주하여 사용량 업데이트
                break # 루프 종료 (오류 발생 시 다른 키 시도 안 함)

            elif not gemini_response_text.strip():
                error_detail = "Unknown reason (empty response)"
                try: error_detail = f"Prompt Feedback: {response.prompt_feedback}"
                except Exception: pass
                api_error_message = f"Gemini API 호출 성공했으나 빈 응답 반환. 세부 정보: {error_detail}"
                logger.warning(api_error_message)
                default_return_state["gemini_response"] = ""
                default_return_state["error_message"] = api_error_message
                api_call_successful = True # 빈 응답도 성공으로 간주하여 사용량 업데이트
                break # 루프 종료

            else:
                logger.info("--- Gemini Response Received Successfully ---")
                api_call_successful = True
                default_return_state["gemini_response"] = gemini_response_text
                default_return_state["error_message"] = None # 성공 시 오류 없음
                # --- 성공 시 현재 사용한 키를 ConfigService에 업데이트 ---
                if config_service and api_key:
                    config_service.update_current_gemini_key(api_key) # Use the dedicated method
                    logger.info(f"Successfully used API key ID {api_key_id}. Updated in-memory config via ConfigService.")
                # ----------------------------------------------------
                break # 성공했으므로 루프 종료

        except google_api_exceptions.ResourceExhausted as e:
            # Rate Limit 오류 발생 시 다음 키 시도
            api_error_message = f"Gemini API Rate Limit 초과 (Key ID: {api_key_id}): {str(e)}."
            logger.error(api_error_message, exc_info=False) # 스택 트레이스 제외
            final_error_message = api_error_message # 최종 오류 메시지 업데이트
            # 다음 키 시도 (루프 계속)
            continue

        except (google_api_exceptions.PermissionDenied, google_api_exceptions.InvalidArgument, AttributeError, ValueError) as e:
            # 복구 불가능한 오류 (키 문제, 모델 문제, SDK 문제 등) -> 루프 중단
            error_type = type(e).__name__
            api_error_message = f"Gemini API 오류 ({error_type} - Key ID: {api_key_id}): {str(e)}. 중단합니다."
            logger.error(api_error_message, exc_info=True)
            default_return_state["error_message"] = api_error_message
            api_call_successful = False # 호출 실패
            break # 루프 중단

        except Exception as e:
            # 기타 예외 -> 루프 중단
            api_error_message = f"Gemini API 호출 중 예상치 못한 오류 (Key ID: {api_key_id}): {str(e)}. 중단합니다."
            logger.exception(api_error_message)
            default_return_state["error_message"] = api_error_message
            api_call_successful = False # 호출 실패
            break # 루프 중단

        finally:
            # API 호출 성공 시 사용량 업데이트 (Rate Limit 오류 제외)
            if api_call_successful and db_service and api_key_id is not None:
                try: db_service.update_api_key_usage(api_key_id)
                except Exception as usage_err: logger.error(f"Failed to update usage for key ID {api_key_id}: {usage_err}", exc_info=True)

            # DB 로그 업데이트 (성공/오류 모두, 현재 시도에 대한 로그)
            end_time_mono = time.monotonic()
            elapsed_ms = int((end_time_mono - start_time_mono) * 1000)
            if db_service and log_id is not None:
                try:
                    db_service.update_gemini_log(
                        log_id=log_id, response_text=gemini_response_text,
                        error_message=api_error_message, elapsed_time_ms=elapsed_ms
                    )
                except Exception as db_err: logger.error(f"Failed to update Gemini log ID {log_id}: {db_err}", exc_info=True)
    # --- 루프 종료 ---

    # 모든 키를 시도했지만 실패한 경우
    if not api_call_successful:
        error_msg = final_error_message or "모든 활성 Gemini API 키를 시도했지만 호출에 실패했습니다."
        logger.error(error_msg)
        default_return_state["error_message"] = error_msg

    # 최종 경과 시간 로깅
    total_elapsed_ms = int((time.monotonic() - start_time_mono) * 1000)
    response_timestamp = datetime.datetime.now(datetime.timezone.utc)
    elapsed_time_str = str(datetime.timedelta(milliseconds=total_elapsed_ms)).split('.')[0]
    logger.info(f"Gemini API 호출 노드 종료 시간: {response_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}, 총 경과 시간: {elapsed_time_str}")

    return default_return_state


def process_response(state: GeminiGraphState, config_service: ConfigService) -> GeminiGraphState:
    """
    Gemini 응답을 XML과 Summary로 파싱하는 노드.
    응답 끝 부분의 <summary> 태그를 기준으로 분리하여 코드 내 문자열과의 혼동을 줄입니다.
    파싱된 결과를 DB 로그에 업데이트합니다.
    """
    print("--- Processing Gemini Response ---")
    logger.info("Processing Gemini Response node")
    gemini_response = state.get('gemini_response', '')
    xml_output = ""
    summary_output = ""
    error_message = state.get('error_message') # 이전 노드의 오류 메시지 유지
    log_id = state.get('log_id') # 상태에서 log_id 가져오기
    db_service: Optional[DbService] = config_service.db_service if config_service else None

    new_state = state.copy()

    try:
        # 이전 노드에서 심각한 오류가 발생했다면 처리 건너뛰기
        if error_message and "Gemini API 응답 문제 발생" not in error_message:
             logger.warning(f"Skipping response processing due to previous critical error: {error_message}")
             new_state["xml_output"] = ""
             new_state["summary_output"] = ""
             # DB 로그에 최종 오류 메시지 업데이트 시도
             if db_service and log_id is not None:
                 db_service.update_gemini_log(log_id=log_id, error_message=error_message)
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
             # DB 로그 업데이트 (오류)
             if db_service and log_id is not None:
                 db_service.update_gemini_log(log_id=log_id, error_message=error_message)
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
            summary_end_index >= len(cleaned_response) - len(summary_end_tag) - 10
        )

        if is_valid_summary:
            xml_output = cleaned_response[:summary_start_index].strip()
            summary_output = cleaned_response[summary_start_index + len(summary_start_tag):summary_end_index].strip()
            logger.info("Successfully parsed XML and Summary parts.")
        else:
            xml_output = cleaned_response
            summary_output = "Summary tag not found or improperly placed in the response."
            logger.warning(summary_output)
            # if not error_message: new_state["error_message"] = summary_output # 파싱 실패를 오류로 설정 가능

        logger.info("--- Response Processed ---")
        new_state["xml_output"] = xml_output
        new_state["summary_output"] = summary_output

        # 파싱된 XML/Summary 결과를 DB 로그에 업데이트
        if db_service and log_id is not None:
            try:
                logger.info(f"Updating DB log ID {log_id} with parsed XML and Summary.")
                db_service.update_gemini_log(
                    log_id=log_id, response_xml=xml_output, response_summary=summary_output
                )
            except Exception as db_err:
                logger.error(f"Failed to update Gemini log ID {log_id} with parsed results: {db_err}", exc_info=True)

        return new_state

    except Exception as e:
        error_msg = f"Error processing response: {str(e)}"
        logger.exception(error_msg)
        new_state["xml_output"] = gemini_response
        new_state["summary_output"] = f"응답 처리 오류: {e}"
        new_state["error_message"] = (error_message + "\n" + error_msg) if error_message else error_msg
        # DB 로그 업데이트 (처리 오류)
        if db_service and log_id is not None:
            db_service.update_gemini_log(log_id=log_id, error_message=new_state["error_message"])
        return new_state


def build_gemini_graph(config_service: ConfigService) -> StateGraph:
    """
    Gemini API 호출 및 처리 LangGraph를 빌드합니다.
    ConfigService를 주입받아 노드에서 사용합니다.
    """
    workflow = StateGraph(GeminiGraphState)

    bound_call_gemini = partial(call_gemini, config_service=config_service)
    bound_process_response = partial(process_response, config_service=config_service)

    workflow.add_node("call_gemini", bound_call_gemini)
    workflow.add_node("process_response", bound_process_response)

    workflow.add_edge(START, "call_gemini")
    workflow.add_edge("call_gemini", "process_response")
    workflow.add_edge("process_response", END)

    app = workflow.compile()
    logger.info("Gemini LangGraph compiled successfully.")
    return app

            