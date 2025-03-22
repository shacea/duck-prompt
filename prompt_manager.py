import os
from datetime import datetime

def generate_final_prompt(system_text, user_text, dev_text, file_contents, root_dir, allowed_extensions, excluded_dirs, selected_folder=None, add_tree=True, dir_structure_content=""):
    final_prompt_parts = [
        "===SYSTEM===",
        system_text,
        "",
        "===USER===",
        user_text,
        "",
        "===FILES CONTENTS===",
    ]

    for path, content in file_contents:
        # 절대 경로를 상대 경로로 변환
        relative_path = os.path.relpath(path, root_dir)
        final_prompt_parts.append(f"\n======== {relative_path} ========\n{content}\n")

    # 수정: add_tree가 True일 경우, 외부에서 받은 dir_structure_content 사용
    if add_tree and dir_structure_content.strip():
        final_prompt_parts.append("")
        final_prompt_parts.append(dir_structure_content)

    return "\n".join(final_prompt_parts)
