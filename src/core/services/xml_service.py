import os
import xml.etree.ElementTree as ET
from typing import Dict, List
import logging # 로깅 추가

logger = logging.getLogger(__name__) # 로거 설정

class XmlService:
    def apply_changes_from_xml(self, xml_string: str, project_directory: str) -> Dict[str, List[str]]:
        """
        Parses XML string and applies file changes (CREATE, UPDATE, DELETE)
        within the specified project directory.
        Handles removing surrounding Markdown code block markers if present.
        Removes leading whitespace/newlines from file content before writing.
        Handles trailing Markdown code block markers (like ```)

        Returns a dictionary summarizing the results:
        {
            "created": [list of created file paths],
            "updated": [list of updated file paths],
            "deleted": [list of deleted file paths],
            "errors": [list of error messages]
        }
        """
        result = {
            "created": [],
            "updated": [],
            "deleted": [],
            "errors": []
        }

        if not project_directory or not os.path.isdir(project_directory):
            result["errors"].append(f"Invalid project directory: {project_directory}")
            return result

        if not xml_string or not xml_string.strip():
            result["errors"].append("XML input string is empty.")
            return result

        # --- Add logic to strip Markdown code block markers ---
        cleaned_xml_string = xml_string.strip()
        # 다양한 마커 형태 고려 (예: ```xml, ```, ````xml, ```` 등)
        markdown_markers = ["```xml", "```", "````xml", "````", '"""', "'''"] # 종료 마커 추가

        # 시작 마커 제거
        for marker in markdown_markers:
            if cleaned_xml_string.startswith(marker):
                # 마커 길이만큼 제거하고, 이후 공백/줄바꿈 제거
                cleaned_xml_string = cleaned_xml_string[len(marker):].lstrip()
                logger.debug(f"Removed starting marker: {marker}")
                break # 하나의 시작 마커만 처리

        # 끝 마커 제거 (수정: 여러 종류의 종료 마커 제거)
        temp_string = cleaned_xml_string.rstrip() # 끝 마커 확인 전 후행 공백/줄바꿈 제거
        marker_removed = False
        for marker in markdown_markers:
            if temp_string.endswith(marker):
                # 마커 길이만큼 제거하고, 이전 공백/줄바꿈 제거
                cleaned_xml_string = temp_string[:-len(marker)].rstrip()
                logger.debug(f"Removed ending marker: {marker}")
                marker_removed = True
                break # 하나의 끝 마커만 처리
        # 만약 마커 제거 후에도 마커가 남아있을 수 있는 경우(예: """\n```) 추가 처리
        if marker_removed:
            temp_string = cleaned_xml_string.rstrip()
            for marker in markdown_markers:
                 if temp_string.endswith(marker):
                      cleaned_xml_string = temp_string[:-len(marker)].rstrip()
                      logger.debug(f"Removed secondary ending marker: {marker}")
                      break

        if not cleaned_xml_string:
             result["errors"].append("XML input string became empty after removing potential Markdown markers.")
             logger.warning("XML input is empty after cleaning.")
             return result
        # --- End of Markdown marker stripping logic ---

        try:
            # XML 파싱 (정리된 문자열 사용)
            logger.info("Attempting to parse cleaned XML string...")
            root = ET.fromstring(cleaned_xml_string)
            logger.info(f"XML parsed successfully. Root element: <{root.tag}>")
        except ET.ParseError as e:
            error_msg = f"Invalid XML format after cleaning: {str(e)}"
            result["errors"].append(error_msg)
            # 파싱 실패 시 문제 문자열 일부 로깅
            context_length = 100 # 오류 주변 문자열 길이
            error_line = getattr(e, 'lineno', '?')
            error_pos = getattr(e, 'offset', '?') # position 속성이 없을 수 있음 (offset 사용)
            start = max(0, e.position[1] - context_length//2) if hasattr(e, 'position') else 0
            end = start + context_length
            problematic_xml_snippet = cleaned_xml_string[start:end]
            logger.error(f"XML ParseError: {e}, Line: {error_line}, Pos: {error_pos}. Problematic snippet near error: ...{problematic_xml_snippet}...")
            return result
        except Exception as e:
             # Catch other potential errors during fromstring
             error_msg = f"Error parsing XML string: {str(e)}"
             result["errors"].append(error_msg)
             logger.exception(f"Unexpected error during XML parsing: {e}") # 스택 트레이스 로깅
             return result


        changed_files_node = root.find('changed_files')
        if changed_files_node is None:
            # If <changed_files> is missing but parsing was successful, it might be an empty XML response.
            # Treat as no changes rather than an error, unless it's entirely empty or unexpected structure.
            # Let's check if the root tag itself is also unexpected.
            if root.tag not in ['code_changes', 'root', 'response']: # Add common root tags
                 result["errors"].append(f"No <changed_files> node found and unexpected root tag '{root.tag}' in XML.")
                 logger.warning(f"XML parsing successful but no <changed_files> node found and unexpected root tag: {root.tag}")
            else:
                 # Successful parse, but no changed_files node. Assume no changes.
                 logger.info("XML parsed successfully but no <changed_files> node found. Assuming no changes.") # 로깅 사용
            return result # Return with errors if any added, or empty result

        for file_node in changed_files_node.findall('file'):
            file_op_node = file_node.find('file_operation')
            file_path_node = file_node.find('file_path')
            file_code_node = file_node.find('file_code') # CDATA 내용 포함

            if file_op_node is None or file_path_node is None:
                result["errors"].append("Skipping file entry: missing file_operation or file_path.")
                logger.warning("Skipping file entry in XML: missing file_operation or file_path.")
                continue

            operation = file_op_node.text.strip().upper() if file_op_node.text else "UNKNOWN"
            relative_path = file_path_node.text.strip() if file_path_node.text else None

            if not relative_path:
                result["errors"].append(f"Skipping file entry: file_path is empty for operation {operation}.")
                logger.warning(f"Skipping file entry in XML: file_path is empty for operation {operation}.")
                continue

            # 보안: 경로 조작 방지 (상대 경로가 프로젝트 디렉토리를 벗어나지 않도록 확인)
            # 정규화된 경로 사용
            try:
                 target_path = os.path.abspath(os.path.join(project_directory, relative_path.lstrip('/\\')))
                 if not target_path.startswith(os.path.abspath(project_directory)):
                    result["errors"].append(f"Skipping potentially unsafe path: {relative_path}")
                    logger.error(f"Security risk: Attempted path traversal detected! Path: '{relative_path}', Target: '{target_path}', Project Root: '{os.path.abspath(project_directory)}'")
                    continue
            except Exception as path_e:
                 result["errors"].append(f"Error processing path '{relative_path}': {path_e}")
                 logger.error(f"Error processing path '{relative_path}': {path_e}", exc_info=True)
                 continue

            # Ensure path separator consistency if needed, but os.path.join handles this locally.
            # For comparison against input, maybe normalize relative_path too? Not critical for security check here.

            file_code = file_code_node.text if file_code_node is not None and file_code_node.text is not None else None

            try:
                if operation in ["CREATE", "UPDATE"]:
                    # Allow empty file_code for creating/updating empty files
                    # if file_code is None: # Changed: Allow None/empty string for file_code
                    #     result["errors"].append(f"Skipping {operation} for '{relative_path}': file_code is missing.")
                    #     continue

                    # Ensure directory exists
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    # Write file, handle None/empty file_code as empty content
                    # *** 수정: 파일 내용 앞쪽 공백/개행 제거 ***
                    with open(target_path, 'w', encoding='utf-8') as f:
                        # file_code가 None이 아니고, 문자열일 경우 앞쪽 공백/개행 제거
                        content_to_write = file_code.lstrip() if file_code is not None and isinstance(file_code, str) else ""
                        f.write(content_to_write)
                        logger.debug(f"Writing content (leading whitespace stripped) to: {target_path}") # 로깅 추가

                    if operation == "CREATE":
                        result["created"].append(target_path)
                        logger.info(f"File CREATED: {target_path}") # 로깅 사용
                    else: # UPDATE
                        result["updated"].append(target_path)
                        logger.info(f"File UPDATED: {target_path}") # 로깅 사용

                elif operation == "DELETE":
                    if os.path.exists(target_path):
                        if os.path.isfile(target_path):
                            os.remove(target_path)
                            result["deleted"].append(target_path)
                            logger.info(f"File DELETED: {target_path}") # 로깅 사용
                        elif os.path.isdir(target_path):
                             result["errors"].append(f"Skipping DELETE for '{relative_path}': It is a directory, not a file.")
                             logger.warning(f"Skipping DELETE for directory: {target_path}")
                        else:
                             result["errors"].append(f"Skipping DELETE for '{relative_path}': It is not a regular file.")
                             logger.warning(f"Skipping DELETE for non-file item: {target_path}")
                    else:
                        # 삭제할 파일이 없는 경우, 오류보다는 경고 또는 무시가 나을 수 있음
                        logger.warning(f"File not found for deletion (ignored): {target_path}") # 로깅 사용

                elif operation == "NONE":
                    # 수정 없음 처리 (로그 또는 아무 작업 안 함)
                    logger.debug(f"Operation NONE for: {target_path}") # Log level DEBUG
                    pass

                else:
                    result["errors"].append(f"Unknown file operation '{operation}' for file: {relative_path}")
                    logger.warning(f"Unknown file operation '{operation}' found in XML for path: {relative_path}")

            except OSError as e:
                 result["errors"].append(f"OS error during {operation} for '{relative_path}': {e}")
                 logger.error(f"OS error during {operation} for '{relative_path}': {e}", exc_info=True) # 로깅 추가
            except Exception as e:
                result["errors"].append(f"Unexpected error during {operation} for '{relative_path}': {str(e)}")
                logger.exception(f"Unexpected error during {operation} for '{relative_path}'") # 로깅 추가

        return result
