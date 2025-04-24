import os
from typing import List, Tuple

class PromptService:
    def generate_code_enhancer_prompt(
        self,
        system_text: str,
        user_text: str,
        file_contents: List[Tuple[str, str]], # List of (path, content)
        root_dir: str,
        dir_structure_content: str = ""
    ) -> str:
        """Generates the final prompt for the Code Enhancer mode."""
        final_prompt_parts = [
            "===SYSTEM===",
            system_text,
            "",
            "===USER===",
            user_text,
            "",
            "===FILES CONTENTS===",
        ]

        if not root_dir:
             print("Warning: root_dir is not set for relative path calculation.")
             # root_dir이 없으면 절대 경로 사용 또는 오류 처리
             for path, content in file_contents:
                 final_prompt_parts.append(f"\n======== {path} ========\n{content}\n")
        else:
            for path, content in file_contents:
                try:
                    # 절대 경로를 상대 경로로 변환
                    relative_path = os.path.relpath(path, root_dir)
                except ValueError:
                    # 다른 드라이브 등 상대 경로 계산 불가 시 절대 경로 사용
                    relative_path = path
                final_prompt_parts.append(f"\n======== {relative_path} ========\n{content}\n")

        # 디렉토리 구조 추가 (존재하는 경우)
        if dir_structure_content and dir_structure_content.strip():
            final_prompt_parts.append("")
            final_prompt_parts.append(dir_structure_content)

        return "\n".join(final_prompt_parts)

    def generate_meta_prompt(
        self,
        meta_template: str,
        meta_user_input: str
    ) -> str:
        """Generates the prompt for the Meta Prompt Builder mode."""
        # 단순 치환 방식
        final_output = meta_template.replace("{{user-input}}", meta_user_input)
        # [[var]] 형태의 변수 치환 로직은 필요시 추가 구현
        return final_output

    def generate_final_meta_prompt(
        self,
        meta_prompt_content: str,
        user_prompt_content: str,
        variables: dict # Dictionary of variable names and their content
    ) -> str:
        """Generates the final prompt by replacing variables in the meta prompt."""
        final_prompt = meta_prompt_content.replace("[[user-prompt]]", user_prompt_content)

        for k, v in variables.items():
            if k != "user-prompt": # 이미 처리됨
                final_prompt = final_prompt.replace(f"[[{k}]]", v)

        return final_prompt

