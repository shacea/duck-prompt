
import os
import xml.etree.ElementTree as ET
from termcolor import colored

def apply_changes_from_xml(xml_string: str, project_directory: str) -> dict:
    """
    XML에 따른 파일 변경 작업을 수행하고 결과를 딕셔너리 형태로 반환.
    """
    result = {
        "status": "success",
        "created": [],
        "updated": [],
        "deleted": [],
        "errors": []
    }

    # XML 파싱
    try:
        root = ET.fromstring(xml_string.strip())
    except ET.ParseError as e:
        result["status"] = "fail"
        result["errors"].append(f"Invalid XML input: {str(e)}")
        return result

    changed_files_node = root.find('changed_files')
    if changed_files_node is None:
        result["status"] = "fail"
        result["errors"].append("No <changed_files> node found in the provided XML.")
        return result

    # 파일 변경 처리
    for file_node in changed_files_node.findall('file'):
        file_operation_node = file_node.find('file_operation')
        file_path_node = file_node.find('file_path')
        file_code_node = file_node.find('file_code')

        if file_operation_node is None or file_path_node is None:
            result["errors"].append("Invalid file entry: file_operation or file_path missing.")
            continue

        file_operation = file_operation_node.text.strip().upper()
        file_path = file_path_node.text.strip()
        target_path = os.path.join(project_directory, file_path.lstrip('/\\'))

        file_code = file_code_node.text if (file_code_node is not None and file_code_node.text is not None) else None

        if file_operation in ["CREATE", "UPDATE"]:
            if not file_code:
                result["errors"].append(f"No file_code provided for {file_operation} operation on {file_path}")
                continue
            try:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(file_code)
                if file_operation == "CREATE":
                    result["created"].append(target_path)
                else:
                    result["updated"].append(target_path)
            except Exception as e:
                result["errors"].append(f"Error {file_operation} file '{target_path}': {str(e)}")

        elif file_operation == "DELETE":
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                    result["deleted"].append(target_path)
                except Exception as e:
                    result["errors"].append(f"Error deleting file '{target_path}': {str(e)}")
            else:
                result["errors"].append(f"File not found for deletion: {target_path}")

        elif file_operation == "NONE":
            # 수정 없음 처리
            pass

        else:
            result["errors"].append(f"Unknown file_operation: {file_operation} for file: {file_path}")

    return result
