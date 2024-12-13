import os
from datetime import datetime

def get_top_level_structure(path: str, allowed_extensions, excluded_dirs) -> list[str]:
    structure = []
    if not path or not os.path.isdir(path):
        return structure

    structure.append(f"📁 {os.path.basename(path)}/")
    try:
        entries = sorted(os.listdir(path))
        dirs = []
        files = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path) and entry not in excluded_dirs:
                dirs.append(entry)
            else:
                ext = os.path.splitext(entry)[1].lower()
                if os.path.isfile(full_path) and ((len(allowed_extensions) == 0) or (ext in allowed_extensions)):
                    files.append(entry)

        for d in dirs:
            structure.append(f"  📁 {d}/")
        for f in files:
            file_path = os.path.join(path, f)
            file_size = os.path.getsize(file_path)
            structure.append(f"  📄 {f} ({file_size:,} bytes)")
    except Exception as e:
        structure.append(f"Error reading directory: {str(e)}")

    return structure

def generate_final_prompt(system_text, user_text, dev_text, file_contents, root_dir, allowed_extensions, excluded_dirs, selected_folder=None, add_tree=True):
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
        final_prompt_parts.append(f"\n--- {os.path.basename(path)} ---\n{content}\n")

    if add_tree and root_dir and os.path.isdir(root_dir):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_prompt_parts.extend([
            "\n" + "="*80,
            f"Directory structure (as of {current_time}):",
            f"Working Directory: {root_dir}",
            "=" * 80
        ])

        top_level = get_top_level_structure(root_dir, allowed_extensions, excluded_dirs)
        final_prompt_parts.extend(top_level)

        if selected_folder and os.path.isdir(selected_folder) and selected_folder != root_dir:
            final_prompt_parts.append(f"Sub-folder: {os.path.basename(selected_folder)}")
            sub_top = get_top_level_structure(selected_folder, allowed_extensions, excluded_dirs)
            sub_top = ["  " + line for line in sub_top[1:]] if len(sub_top) > 1 else []
            final_prompt_parts.extend(sub_top)

        final_prompt_parts.append("=" * 80)

    return "\n".join(final_prompt_parts)
