import google.generativeai as genai
from langgraph.graph import StateGraph, END, START
from functools import partial
import logging
from typing import Optional, List, Dict, Any, Union, Tuple, Set
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
    Gemini API를 호출하는 노드 (멀티모달 지원).
    1. 사용자가 선택한 키를 먼저 시도합니다. (활성 상태 및 Rate Limit 체크 후)
    2. 사용자 선택 키가 없거나 실패(Rate Limit, PermissionDenied 등)하면, DB에서 활성 키 목록을 조회하여
       일일 사용량이 가장 적은 키부터 순서대로 시도합니다. (이미 시도한 키 제외)
    3. Rate Limit, PermissionDenied, InvalidArgument 에러 발생 시 다음 키로 자동 전환하여 재시도합니다.
    4. 성공 시 사용된 키 정보를 ConfigService에 업데이트합니다.
    """
    logger.info("Calling Gemini API node (Multimodal, with key rotation)")
    start_time_mono = time.monotonic()
    request_timestamp = datetime.datetime.now(datetime.timezone.utc)
    logger.info(f"Gemini API 호출 시작 시간: {request_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    text_prompt = state['input_prompt']
    attachments = state.get('input_attachments', [])
    settings = config_service.get_settings()
    db_service: DbService = config_service.db_service

    # 설정에서 모델명 가져오기
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

    # --- API 키 선택 및 시도 로직 (개선) ---
    tried_key_ids: Set[int] = set() # 이미 시도한 키 ID 추적
    api_key_id: Optional[int] = None
    log_id: Optional[int] = None
    final_error_message: Optional[str] = None
    api_call_successful = False # API 호출 성공 여부 플래그
    successfully_used_key_string: Optional[str] = None # 성공적으로 사용된 키 문자열
    successfully_used_key_id: Optional[int] = None # 성공적으로 사용된 키 ID

    # 1. 사용자 지정 키 먼저 시도
    user_selected_key_id = config_service.get_user_selected_gemini_key_id()
    user_key_info: Optional[Dict[str, Any]] = None

    if user_selected_key_id is not None:
        logger.info(f"User has selected Gemini Key ID: {user_selected_key_id}. Attempting to use it first.")
        try:
            # DB에서 해당 키의 상세 정보와 최신 사용량 조회 (get_active_api_keys_with_usage 필터링 방식 유지)
            temp_keys_usage = db_service.get_active_api_keys_with_usage('google')
            user_key_info = next((k for k in temp_keys_usage if k['id'] == user_selected_key_id), None)

            if user_key_info:
                logger.info(f"Found details for user-selected key ID {user_selected_key_id}.")
                # Rate Limit 체크
                is_limited, reason = db_service.is_key_rate_limited(user_selected_key_id, model_name)
                if is_limited:
                    logger.warning(f"User-selected key ID {user_selected_key_id} is rate-limited: {reason}. Will try other keys.")
                    final_error_message = f"User-selected key ID {user_selected_key_id} is rate-limited: {reason}"
                    tried_key_ids.add(user_selected_key_id) # 시도한 것으로 간주
                    user_key_info = None # 사용 불가 처리
                else:
                    logger.info(f"User-selected key ID {user_selected_key_id} passed rate limit check.")
                    # 사용자 선택 키를 첫 번째 시도 대상으로 설정
            else:
                logger.warning(f"User-selected key ID {user_selected_key_id} not found among active keys or failed to get usage. Will try other keys.")
                tried_key_ids.add(user_selected_key_id) # 시도한 것으로 간주 (찾을 수 없으므로)

        except Exception as e:
            logger.error(f"Error retrieving/checking user-selected key ID {user_selected_key_id}: {e}", exc_info=True)
            tried_key_ids.add(user_selected_key_id) # 오류 발생 시 시도한 것으로 간주
            user_key_info = None # 사용 불가 처리

    # --- API 키 시도 루프 ---
    keys_to_attempt: List[Dict[str, Any]] = []
    if user_key_info:
        keys_to_attempt.append(user_key_info) # 사용자 선택 키를 맨 앞에 추가

    # 사용자 키가 없거나 실패할 경우 다른 활성 키 목록 가져오기
    if not user_key_info: # 사용자 키가 없거나, Rate Limit 걸렸거나, 조회 실패한 경우
        logger.info("Fetching other active Gemini keys sorted by daily usage...")
        try:
            active_keys_usage = db_service.get_active_api_keys_with_usage('google')
            active_keys_usage.sort(key=lambda x: x['calls_this_day']) # 일일 사용량 기준 오름차순 정렬
            # 이미 시도한 사용자 선택 키 제외하고 추가
            added_count = 0
            for key_info in active_keys_usage:
                if key_info['id'] not in tried_key_ids:
                    keys_to_attempt.append(key_info)
                    added_count += 1
            logger.info(f"Found {added_count} other active keys to try.")
        except Exception as e:
            error_msg = f"Failed to retrieve other active Gemini keys with usage from DB: {e}"
            logger.error(error_msg, exc_info=True)
            # 다른 키 조회 실패 시, 사용자 키도 없으면 완전 실패
            if not user_key_info:
                default_return_state["error_message"] = final_error_message or error_msg # 사용자 키 Rate Limit 메시지 또는 DB 오류 메시지
                return default_return_state
            # 사용자 키는 있었지만 Rate Limit 걸린 경우, 다른 키 조회 실패했으므로 여기서 종료
            elif user_selected_key_id in tried_key_ids:
                 default_return_state["error_message"] = final_error_message or "Failed to find alternative keys."
                 return default_return_state

    if not keys_to_attempt:
        error_msg = final_error_message or "No usable Gemini API Keys found (neither selected nor active/available in DB)."
        logger.error(error_msg)
        default_return_state["error_message"] = error_msg
        return default_return_state

    logger.info(f"Total keys to try in order: {[k['id'] for k in keys_to_attempt]}")

    # --- API 키 순차 시도 ---
    for key_info in keys_to_attempt:
        api_key = key_info['api_key']
        current_key_id = key_info['id'] # 현재 시도하는 키 ID
        daily_usage = key_info.get('calls_this_day', 'N/A')
        logger.info(f"Attempting to use Gemini API Key ID: {current_key_id} (Daily Usage: {daily_usage})")

        # 이미 시도한 키는 건너뛰기 (중복 방지)
        if current_key_id in tried_key_ids:
            logger.debug(f"Skipping already tried key ID: {current_key_id}")
            continue

        # Rate Limit 체크 (사용자 키는 이미 체크했으므로, 다른 키만 체크)
        if current_key_id != user_selected_key_id:
            is_limited, reason = db_service.is_key_rate_limited(current_key_id, model_name)
            if is_limited:
                logger.warning(f"Pre-check failed: Rate limit reached for key ID {current_key_id}. Reason: {reason}. Skipping.")
                final_error_message = f"Rate limit exceeded for key ID {current_key_id}: {reason}" # 마지막 실패 사유 업데이트
                tried_key_ids.add(current_key_id) # 시도한 것으로 간주
                continue # 다음 키 시도
            logger.info(f"Rate limit pre-check passed for key ID {current_key_id}.")

        # --- DB 로깅 준비 ---
        current_log_id = log_id # 이전 시도의 log_id (실패 시)
        if current_log_id is None: # 첫 시도인 경우에만 새 로그 생성
            try:
                current_log_id = db_service.log_gemini_request(
                    model_name=model_name, request_prompt=text_prompt,
                    request_attachments=attachments, api_key_id=current_key_id # 현재 시도하는 키 ID 사용
                )
                if current_log_id:
                     log_id = current_log_id # 성공적으로 생성된 log_id 저장
                     default_return_state["log_id"] = log_id # 상태에도 반영
                else:
                     logger.error(f"Failed to create initial Gemini log entry for key ID {current_key_id}.")
            except Exception as db_err:
                logger.error(f"Failed to log Gemini request to DB for key ID {current_key_id}: {db_err}", exc_info=True)
        # --- DB 로깅 준비 완료 ---

        effective_model_name = ""
        gemini_response_text = ""
        api_error_message: Optional[str] = None
        # api_call_successful 플래그는 루프 시작 시 False로 초기화됨

        try:
            genai.configure(api_key=api_key)
            effective_model_name = model_name.replace("models/", "")
            model = genai.GenerativeModel(effective_model_name)
            logger.info(f"Using Gemini model: {effective_model_name} with key ID: {current_key_id}")

            # GenerationConfig, ToolConfig, Tools 설정
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

            # Contents 구성
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
            logger.info(f"Sending {len(contents_list)} parts to Gemini model: {effective_model_name} (using key ID: {current_key_id})")
            response = model.generate_content(
                contents=contents_list, generation_config=generation_config,
                tools=tools_list, tool_config=tool_config_obj, stream=True
            )

            # 스트림 응답 처리
            specific_error_occurred = False; error_details = ""
            for chunk in response:
                try: gemini_response_text += chunk.text
                except ValueError as e:
                    if "response.text` quick accessor" in str(e) or "candidate.text`" in str(e):
                        func_calls = getattr(chunk, 'function_calls', None)
                        finish_reason = getattr(getattr(chunk, 'candidates', [None])[0], 'finish_reason', 'unknown') if hasattr(chunk, 'candidates') else 'unknown'
                        msg = (f"Function Call ignored: {func_calls}" if func_calls
                               else f"Chunk text access error (Finish Reason: {finish_reason}): {e}")
                        logger.warning(msg)
                        error_details += f"\n- {msg}"
                        specific_error_occurred = True
                        continue
                    else: raise
                except Exception as e: logger.exception(f"Unexpected chunk error: {e}"); error_details += f"\n- Chunk error: {e}"; specific_error_occurred = True; continue

            # 결과 처리
            if specific_error_occurred:
                api_error_message = f"Gemini API 응답 문제 발생 (Key ID: {current_key_id}). 일부 내용 누락 또는 Function Call 포함 가능." + "\n세부 정보:" + error_details
                logger.warning(f"Gemini stream processing issues for key ID {current_key_id}. Details: {error_details}")
                default_return_state["error_message"] = api_error_message
                default_return_state["gemini_response"] = gemini_response_text # 부분 응답 저장
                api_call_successful = True # 부분 성공으로 간주하여 사용량 업데이트
                successfully_used_key_string = api_key
                successfully_used_key_id = current_key_id
                break # 루프 종료 (오류 발생 시 다른 키 시도 안 함)

            elif not gemini_response_text.strip():
                error_detail = "Unknown reason (empty response)"
                try: error_detail = f"Prompt Feedback: {response.prompt_feedback}"
                except Exception: pass
                api_error_message = f"Gemini API 호출 성공했으나 빈 응답 반환 (Key ID: {current_key_id}). 세부 정보: {error_detail}"
                logger.warning(api_error_message)
                default_return_state["gemini_response"] = ""
                default_return_state["error_message"] = api_error_message
                api_call_successful = True # 빈 응답도 성공으로 간주
                successfully_used_key_string = api_key
                successfully_used_key_id = current_key_id
                break # 루프 종료

            else:
                logger.info(f"--- Gemini Response Received Successfully using Key ID: {current_key_id} ---")
                api_call_successful = True
                successfully_used_key_string = api_key
                successfully_used_key_id = current_key_id
                default_return_state["gemini_response"] = gemini_response_text
                default_return_state["error_message"] = None # 성공 시 오류 없음
                break # 성공했으므로 루프 종료

        except google_api_exceptions.ResourceExhausted as e:
            api_error_message = f"Gemini API Rate Limit 초과 (Key ID: {current_key_id}): {str(e)}. 다음 키로 재시도합니다."
            logger.error(api_error_message, exc_info=False)
            final_error_message = api_error_message
            tried_key_ids.add(current_key_id) # 시도한 것으로 간주
            if db_service and log_id is not None:
                end_time_mono_err = time.monotonic(); elapsed_ms_err = int((end_time_mono_err - start_time_mono) * 1000)
                db_service.update_gemini_log(log_id=log_id, error_message=f"Rate Limit Error: {e}", elapsed_time_ms=elapsed_ms_err)
            continue # 다음 키 시도

        except google_api_exceptions.PermissionDenied as e:
            api_error_message = f"Gemini API 권한 오류 (Key ID: {current_key_id}): {str(e)}. 다음 키로 재시도합니다."
            logger.error(api_error_message, exc_info=False)
            final_error_message = api_error_message
            tried_key_ids.add(current_key_id) # 시도한 것으로 간주
            if db_service and log_id is not None:
                end_time_mono_err = time.monotonic(); elapsed_ms_err = int((end_time_mono_err - start_time_mono) * 1000)
                db_service.update_gemini_log(log_id=log_id, error_message=f"Permission Denied: {e}", elapsed_time_ms=elapsed_ms_err)
            continue # 다음 키 시도

        except google_api_exceptions.InvalidArgument as e:
            api_error_message = f"Gemini API 잘못된 인수 오류 (Key ID: {current_key_id}): {str(e)}. 다음 키로 재시도합니다. (문제가 키 관련이 아닐 수 있음)"
            logger.error(api_error_message, exc_info=False)
            final_error_message = api_error_message
            tried_key_ids.add(current_key_id) # 시도한 것으로 간주
            if db_service and log_id is not None:
                end_time_mono_err = time.monotonic(); elapsed_ms_err = int((end_time_mono_err - start_time_mono) * 1000)
                db_service.update_gemini_log(log_id=log_id, error_message=f"Invalid Argument: {e}", elapsed_time_ms=elapsed_ms_err)
            continue # 다음 키 시도

        except (AttributeError, ValueError) as e:
            error_type = type(e).__name__
            api_error_message = f"Gemini API 오류 ({error_type} - Key ID: {current_key_id}): {str(e)}. 중단합니다."
            logger.error(api_error_message, exc_info=True)
            default_return_state["error_message"] = api_error_message
            api_call_successful = False
            tried_key_ids.add(current_key_id) # 시도한 것으로 간주
            break # 루프 중단

        except Exception as e:
            api_error_message = f"Gemini API 호출 중 예상치 못한 오류 (Key ID: {current_key_id}): {str(e)}. 중단합니다."
            logger.exception(api_error_message)
            default_return_state["error_message"] = api_error_message
            api_call_successful = False
            tried_key_ids.add(current_key_id) # 시도한 것으로 간주
            break # 루프 중단

        finally:
            # finally 블록은 Rate Limit/Permission/Argument 오류로 continue 할 때도 실행됨
            # 성공했거나, 복구 불가능한 오류로 중단되었거나, 스트림 처리 오류 발생 시 로그 업데이트
            if api_call_successful or (api_error_message and "다음 키로 재시도합니다" not in api_error_message):
                 # 사용량 업데이트는 성공 시에만
                 if api_call_successful and db_service and current_key_id is not None:
                    try: db_service.update_api_key_usage(current_key_id)
                    except Exception as usage_err: logger.error(f"Failed to update usage for key ID {current_key_id}: {usage_err}", exc_info=True)

                 # DB 로그 업데이트 (성공/오류 모두, log_id가 생성된 경우)
                 if db_service and log_id is not None:
                    end_time_mono = time.monotonic(); elapsed_ms = int((end_time_mono - start_time_mono) * 1000)
                    try:
                        db_service.update_gemini_log(
                            log_id=log_id, response_text=gemini_response_text,
                            error_message=api_error_message, elapsed_time_ms=elapsed_ms
                        )
                    except Exception as db_err: logger.error(f"Failed to update Gemini log ID {log_id}: {db_err}", exc_info=True)
            # Rate Limit/Permission/Argument 발생 시에는 finally 블록에서 별도 처리 없음 (except 블록에서 로그 업데이트)
    # --- 루프 종료 ---

    # --- 성공 시 사용된 키를 ConfigService에 업데이트 ---
    if api_call_successful and successfully_used_key_string and successfully_used_key_id is not None:
        if config_service:
            config_service.update_last_used_gemini_key(successfully_used_key_string)
            logger.info(f"Successfully used API key ID {successfully_used_key_id}. Updated in-memory config via ConfigService.")
            # 사용자가 선택한 키와 다른 키가 사용되었을 경우, 사용자 선택 해제
            if user_selected_key_id is not None and user_selected_key_id != successfully_used_key_id:
                 logger.info(f"Successfully used key ID {successfully_used_key_id} is different from user-selected key ID {user_selected_key_id}. Clearing user selection.")
                 config_service.set_user_selected_gemini_key(None)
        else:
            logger.warning("ConfigService not available to update the last used key.")
    # ----------------------------------------------------

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
        if error_message and "Gemini API 응답 문제 발생" not in error_message and "빈 응답 반환" not in error_message: # 빈 응답은 처리 시도
             logger.warning(f"Skipping response processing due to previous critical error: {error_message}")
             new_state["xml_output"] = ""
             new_state["summary_output"] = ""
             # DB 로그에 최종 오류 메시지 업데이트 시도 (call_gemini에서 이미 했을 수 있음)
             # if db_service and log_id is not None:
             #     db_service.update_gemini_log(log_id=log_id, error_message=error_message)
             return new_state
        elif error_message:
             logger.warning(f"Processing potentially partial or empty response due to previous issue: {error_message}")

        if not gemini_response or not gemini_response.strip(): # 빈 문자열 또는 공백만 있는 경우
             logger.warning("Gemini response is empty, skipping processing.")
             if not error_message: # 이전 오류가 없었다면 빈 응답 오류 설정
                 error_message = "Gemini response was empty after successful API call."
                 new_state["error_message"] = error_message
             new_state["xml_output"] = ""
             new_state["summary_output"] = ""
             # DB 로그 업데이트 (오류 - 빈 응답)
             if db_service and log_id is not None:
                 db_service.update_gemini_log(log_id=log_id, error_message=new_state["error_message"])
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
            # 끝부분에 있는지 좀 더 관대하게 확인 (약간의 후행 공백 허용)
            summary_end_index >= len(cleaned_response) - len(summary_end_tag) - 20 # 허용 범위 약간 늘림
        )

        if is_valid_summary:
            xml_output = cleaned_response[:summary_start_index].strip()
            summary_output = cleaned_response[summary_start_index + len(summary_start_tag):summary_end_index].strip()
            logger.info("Successfully parsed XML and Summary parts.")
            # 성공적으로 파싱되었으므로, 이전 오류 메시지(빈 응답 등)는 지울 수 있음 (선택적)
            if "빈 응답 반환" in (error_message or ""):
                new_state["error_message"] = None # 빈 응답 오류는 해소된 것으로 간주
        else:
            xml_output = cleaned_response
            summary_output = "Summary tag not found or improperly placed in the response."
            logger.warning(summary_output)
            # 파싱 실패를 오류로 설정 (이전 오류가 없었을 경우)
            if not error_message: new_state["error_message"] = summary_output

        logger.info("--- Response Processed ---")
        new_state["xml_output"] = xml_output
        new_state["summary_output"] = summary_output

        # 파싱된 XML/Summary 결과를 DB 로그에 업데이트
        if db_service and log_id is not None:
            try:
                logger.info(f"Updating DB log ID {log_id} with parsed XML and Summary.")
                db_service.update_gemini_log(
                    log_id=log_id, response_xml=xml_output, response_summary=summary_output,
                    # 오류 메시지도 업데이트 (파싱 실패 또는 이전 오류 유지)
                    error_message=new_state["error_message"]
                )
            except Exception as db_err:
                logger.error(f"Failed to update Gemini log ID {log_id} with parsed results: {db_err}", exc_info=True)

        return new_state

    except Exception as e:
        error_msg = f"Error processing response: {str(e)}"
        logger.exception(error_msg)
        new_state["xml_output"] = gemini_response # 원본 응답 유지
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
