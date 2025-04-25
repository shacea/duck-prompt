import os
from typing import List

# 변경된 경로에서 import
from utils.helpers import get_resource_path

class TemplateService:
    def __init__(self, base_resource_path: str = "resources"):
        pass

    def _get_full_path(self, relative_path: str) -> str:
        """Constructs the full path using get_resource_path."""
        # 예: relative_path = "prompts/system/my_template.md"
        return get_resource_path(relative_path)

    def list_templates(self, directory: str) -> List[str]:
        """Lists Markdown templates in a given directory relative to resources."""
        # directory 예: "prompts/system"
        full_dir_path = self._get_full_path(directory)
        if not os.path.exists(full_dir_path) or not os.path.isdir(full_dir_path):
            print(f"Template directory not found: {full_dir_path}")
            return []
        try:
            files = os.listdir(full_dir_path)
            # .md 파일만 필터링
            return [f for f in files if f.lower().endswith(".md")]
        except Exception as e:
            print(f"Error listing templates in {full_dir_path}: {e}")
            return []

    def load_template(self, file_path: str) -> str:
        """Loads content from a template file relative to resources."""
        # file_path 예: "prompts/user/example.md"
        full_file_path = self._get_full_path(file_path)
        if not os.path.exists(full_file_path):
            print(f"Template file not found: {full_file_path}")
            return "" # 파일 없으면 빈 문자열 반환
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Template loaded successfully from {full_file_path}")
            return content
        except Exception as e:
            print(f"Error loading template {full_file_path}: {str(e)}")
            return "" # 오류 시 빈 문자열 반환

    def save_template(self, file_path: str, content: str) -> bool:
        """Saves content to a template file relative to resources."""
        # file_path 예: "prompts/system/new_template.md"
        full_file_path = self._get_full_path(file_path)
        try:
            # 디렉토리 생성 (필요한 경우)
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Template saved successfully to {full_file_path}")
            return True
        except Exception as e:
            print(f"Error saving template to {full_file_path}: {str(e)}")
            return False

    def delete_template(self, file_path: str) -> bool:
        """Deletes a template file relative to resources."""
        # file_path 예: "prompts/system/old_template.md"
        full_file_path = self._get_full_path(file_path)
        if os.path.exists(full_file_path):
            try:
                os.remove(full_file_path)
                print(f"Deleted template file: {full_file_path}")
                return True
            except Exception as e:
                print(f"Error deleting template file {full_file_path}: {e}")
                return False
        else:
            print(f"Template file not found for deletion: {full_file_path}")
            return False