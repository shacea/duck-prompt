import os
import xml.etree.ElementTree as ET

def apply_changes_from_xml(xml_string: str, project_directory: str):
    root = ET.fromstring(xml_string.strip())

    changed_files_node = root.find('changed_files')
    if changed_files_node is None:
        print("No <changed_files> found in the provided XML.")
        return

    for file_node in changed_files_node.findall('file'):
        file_operation_node = file_node.find('file_operation')
        file_path_node = file_node.find('file_path')
        file_code_node = file_node.find('file_code')

        if file_operation_node is None or file_path_node is None:
            print("Invalid file entry: file_operation or file_path missing.")
            continue

        file_operation = file_operation_node.text.strip().upper()
        file_path = file_path_node.text.strip()
        target_path = os.path.join(project_directory, file_path.lstrip('/\\'))

        file_code = None
        if file_code_node is not None and file_code_node.text is not None:
            file_code = file_code_node.text

        if file_operation == "CREATE" or file_operation == "UPDATE":
            if file_code is None:
                print(f"No file_code provided for {file_operation} operation on {file_path}")
                continue
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(file_code)
            print(f"{file_operation}D file: {target_path}")

        elif file_operation == "DELETE":
            if os.path.exists(target_path):
                os.remove(target_path)
                print(f"DELETED file: {target_path}")
            else:
                print(f"File not found for deletion: {target_path}")
        else:
            print(f"Unknown file_operation: {file_operation} for file: {file_path}")
