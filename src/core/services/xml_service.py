import os
import xml.etree.ElementTree as ET
from typing import Dict, List

class XmlService:
    def apply_changes_from_xml(self, xml_string: str, project_directory: str) -> Dict[str, List[str]]:
        """
        Parses XML string and applies file changes (CREATE, UPDATE, DELETE)
        within the specified project directory.
        Handles removing surrounding Markdown code block markers if present.

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
        markdown_markers = ["```xml", "```", "`````xml", "`````"] # Add any other common markers if needed

        # Check and remove starting marker
        for marker in markdown_markers:
            if cleaned_xml_string.startswith(marker):
                cleaned_xml_string = cleaned_xml_string[len(marker):].lstrip() # Remove marker and leading whitespace/newline
                break # Assume only one starting marker

        # Check and remove ending marker
        for marker in markdown_markers: # Check for both ```` and ```xml` at the end
            if cleaned_xml_string.endswith(marker):
                 # Use rstrip() before checking endswith to handle trailing whitespace/newline
                 temp_string = cleaned_xml_string.rstrip()
                 if temp_string.endswith(marker):
                    cleaned_xml_string = temp_string[:-len(marker)].rstrip() # Remove marker and trailing whitespace/newline
                 break # Assume only one ending marker

        if not cleaned_xml_string:
             result["errors"].append("XML input string became empty after removing potential Markdown markers.")
             return result
        # --- End of Markdown marker stripping logic ---

        try:
            # XML 파싱
            root = ET.fromstring(cleaned_xml_string) # Use the cleaned string
        except ET.ParseError as e:
            result["errors"].append(f"Invalid XML format after cleaning: {str(e)}")
            return result
        except Exception as e:
             # Catch other potential errors during fromstring
             result["errors"].append(f"Error parsing XML string: {str(e)}")
             return result


        changed_files_node = root.find('changed_files')
        if changed_files_node is None:
            # If <changed_files> is missing but parsing was successful, it might be an empty XML response.
            # Treat as no changes rather than an error, unless it's entirely empty or unexpected structure.
            # Let's check if the root tag itself is also unexpected.
            if root.tag not in ['code_changes', 'root', 'response']: # Add common root tags
                 result["errors"].append(f"No <changed_files> node found and unexpected root tag '{root.tag}' in XML.")
            else:
                 # Successful parse, but no changed_files node. Assume no changes.
                 print("XML parsed successfully but no <changed_files> node found. Assuming no changes.")
            return result # Return with errors if any added, or empty result

        for file_node in changed_files_node.findall('file'):
            file_op_node = file_node.find('file_operation')
            file_path_node = file_node.find('file_path')
            file_code_node = file_node.find('file_code') # CDATA 내용 포함

            if file_op_node is None or file_path_node is None:
                result["errors"].append("Skipping file entry: missing file_operation or file_path.")
                continue

            operation = file_op_node.text.strip().upper() if file_op_node.text else "UNKNOWN"
            relative_path = file_path_node.text.strip() if file_path_node.text else None

            if not relative_path:
                result["errors"].append(f"Skipping file entry: file_path is empty for operation {operation}.")
                continue

            # 보안: 경로 조작 방지 (상대 경로가 프로젝트 디렉토리를 벗어나지 않도록 확인)
            # 정규화된 경로 사용
            target_path = os.path.abspath(os.path.join(project_directory, relative_path.lstrip('/\\')))
            if not target_path.startswith(os.path.abspath(project_directory)):
                result["errors"].append(f"Skipping potentially unsafe path: {relative_path}")
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
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(file_code if file_code is not None else "") # Write empty string if file_code is None

                    if operation == "CREATE":
                        result["created"].append(target_path)
                        print(f"File CREATED: {target_path}")
                    else: # UPDATE
                        result["updated"].append(target_path)
                        print(f"File UPDATED: {target_path}")

                elif operation == "DELETE":
                    if os.path.exists(target_path):
                        if os.path.isfile(target_path):
                            os.remove(target_path)
                            result["deleted"].append(target_path)
                            print(f"File DELETED: {target_path}")
                        else:
                             result["errors"].append(f"Skipping DELETE for '{relative_path}': It is a directory, not a file.")
                    else:
                        # 삭제할 파일이 없는 경우, 오류보다는 경고 또는 무시가 나을 수 있음
                        print(f"File not found for deletion (ignored): {target_path}")

                elif operation == "NONE":
                    # 수정 없음 처리 (로그 또는 아무 작업 안 함)
                    # print(f"Operation NONE for: {target_path}") # Suppress this frequent log
                    pass

                else:
                    result["errors"].append(f"Unknown file operation '{operation}' for file: {relative_path}")

            except OSError as e:
                 result["errors"].append(f"OS error during {operation} for '{relative_path}': {e}")
            except Exception as e:
                result["errors"].append(f"Unexpected error during {operation} for '{relative_path}': {str(e)}")

        return result