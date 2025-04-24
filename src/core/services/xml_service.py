import os
import xml.etree.ElementTree as ET
from typing import Dict, List

class XmlService:
    def apply_changes_from_xml(self, xml_string: str, project_directory: str) -> Dict[str, List[str]]:
        """
        Parses XML string and applies file changes (CREATE, UPDATE, DELETE)
        within the specified project directory.

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

        try:
            # XML 파싱 시 공백 제거
            root = ET.fromstring(xml_string.strip())
        except ET.ParseError as e:
            result["errors"].append(f"Invalid XML format: {str(e)}")
            return result

        changed_files_node = root.find('changed_files')
        if changed_files_node is None:
            result["errors"].append("No <changed_files> node found in XML.")
            return result

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
            target_path = os.path.abspath(os.path.join(project_directory, relative_path.lstrip('/\\')))
            if not target_path.startswith(os.path.abspath(project_directory)):
                result["errors"].append(f"Skipping potentially unsafe path: {relative_path}")
                continue

            file_code = file_code_node.text if file_code_node is not None and file_code_node.text is not None else None

            try:
                if operation in ["CREATE", "UPDATE"]:
                    if file_code is None: # 빈 파일 생성/수정을 허용할지 결정 필요 (현재는 오류)
                        result["errors"].append(f"Skipping {operation} for '{relative_path}': file_code is missing.")
                        continue

                    # 파일 코드 앞뒤 공백/개행 제거 (필요에 따라 조정)
                    file_code = file_code.strip()
                    # 첫 줄 공백 방지를 위해 선행 개행만 제거
                    # file_code = file_code.lstrip('\r\n')

                    # 디렉토리 생성
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    # 파일 쓰기
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(file_code)

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
                    print(f"Operation NONE for: {target_path}")
                    pass

                else:
                    result["errors"].append(f"Unknown file operation '{operation}' for file: {relative_path}")

            except OSError as e:
                 result["errors"].append(f"OS error during {operation} for '{relative_path}': {e}")
            except Exception as e:
                result["errors"].append(f"Unexpected error during {operation} for '{relative_path}': {str(e)}")

        return result