import os
from typing import List, Tuple, Dict, Any # Dict, Any 추가

class PromptService:
    def generate_code_enhancer_prompt(
        self,
        system_text: str,
        user_text: str,
        file_contents: List[Tuple[str, str]], # List of (path, content)
        root_dir: str,
        dir_structure_content: str = "",
        attached_items: List[Dict[str, Any]] = [] # 첨부 파일 목록 추가
    ) -> str:
        """
        Generates the final text prompt for the Code Enhancer mode.
        Includes markers for attached files/images.
        """
        final_prompt_parts = [
            "===SYSTEM===",
            system_text,
            "",
            "===USER===",
            user_text,
            "",
        ]

        # 첨부 파일/이미지 정보 추가 (마커 사용)
        if attached_items:
            final_prompt_parts.append("===ATTACHMENTS===")
            for i, item in enumerate(attached_items):
                item_type = item.get('type', 'unknown')
                item_name = item.get('name', f'attachment_{i+1}')
                if item_type == 'image':
                    final_prompt_parts.append(f"- Image: {item_name} (Data provided separately)")
                elif item_type == 'file':
                    # 파일 내용을 프롬프트에 포함할지 여부 결정 (여기서는 마커만 사용)
                    # file_data = item.get('data')
                    # content_preview = "(Content provided separately)"
                    # if file_data:
                    #     try:
                    #         # 간단한 텍스트 미리보기 (옵션)
                    #         preview = file_data[:100].decode('utf-8', errors='ignore') + ('...' if len(file_data) > 100 else '')
                    #         content_preview = f"(Content starts with: {preview})"
                    #     except: pass
                    final_prompt_parts.append(f"- File: {item_name} (Content provided separately)")
                else:
                    final_prompt_parts.append(f"- Unknown Attachment: {item_name}")
            final_prompt_parts.append("") # 구분선

        # 선택된 파일 내용 추가
        final_prompt_parts.append("===FILES CONTENTS===")
        if not root_dir:
             print("Warning: root_dir is not set for relative path calculation.")
             for path, content in file_contents:
                 final_prompt_parts.append(f"\n======== {path} ========\n{content}\n")
        else:
            for path, content in file_contents:
                try:
                    relative_path = os.path.relpath(path, root_dir)
                except ValueError:
                    relative_path = path
                final_prompt_parts.append(f"\n======== {relative_path} ========\n{content}\n")

        # 디렉토리 구조 추가
        if dir_structure_content and dir_structure_content.strip():
            final_prompt_parts.append("")
            final_prompt_parts.append(dir_structure_content)

        return "\n".join(final_prompt_parts)
