
import os
import json
from termcolor import colored
import shutil
from datetime import datetime

def save_state(state: dict, filename: str) -> bool:
    try:
        os.makedirs("resources/status", exist_ok=True)
        file_path = os.path.join("resources", "status", filename + ".json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
        print(colored(f"State saved to {file_path}", "green"))
        return True
    except Exception as e:
        print(colored(f"Error saving state: {str(e)}", "red"))
        return False

def load_state(filename: str) -> dict:
    try:
        file_path = os.path.join("resources", "status", filename + ".json")
        if not os.path.exists(file_path):
            print(colored(f"No state file found at {file_path}", "yellow"))
            # 수정: 기본값 반환
            return {
                "mode": "Code Enhancer Prompt Builder",
                "project_folder": None,
                "system_prompt": "",
                "user_prompt": "",
                "last_generated_prompt": "",
                "checked_files": []
            }
        with open(file_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(colored(f"State loaded from {file_path}", "green"))
        return state
    except Exception as e:
        print(colored(f"Error loading state: {str(e)}", "red"))
        # 오류 시에도 기본값 반환
        return {
            "mode": "Code Enhancer Prompt Builder",
            "project_folder": None,
            "system_prompt": "",
            "user_prompt": "",
            "last_generated_prompt": "",
            "checked_files": []
        }

def import_state_from_file(path: str) -> dict:
    try:
        if not os.path.exists(path):
            print(colored(f"No state file found at {path}", "yellow"))
            return {
                "mode": "Code Enhancer Prompt Builder",
                "project_folder": None,
                "system_prompt": "",
                "user_prompt": "",
                "last_generated_prompt": "",
                "checked_files": []
            }
        with open(path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(colored(f"State imported from {path}", "green"))
        return state
    except Exception as e:
        print(colored(f"Error importing state: {str(e)}", "red"))
        return {
            "mode": "Code Enhancer Prompt Builder",
            "project_folder": None,
            "system_prompt": "",
            "user_prompt": "",
            "last_generated_prompt": "",
            "checked_files": []
        }

def export_state_to_file(state: dict, path: str) -> bool:
    try:
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
        print(colored(f"State exported to {path}", "green"))
        return True
    except Exception as e:
        print(colored(f"Error exporting state: {str(e)}", "red"))
        return False

def list_states() -> list:
    states_dir = "resources/status"
    if not os.path.exists(states_dir):
        return []
    files = os.listdir(states_dir)
    return [f for f in files if f.lower().endswith(".json")]

def delete_state(filename: str) -> bool:
    file_path = os.path.join("resources", "status", filename + ".json")
    if os.path.exists(file_path):
        os.remove(file_path)
        print(colored(f"Deleted state: {file_path}", "green"))
        return True
    else:
        print(colored(f"State not found: {file_path}", "red"))
        return False

def backup_all_states(backup_path: str) -> bool:
    try:
        states_dir = "resources/status"
        if not os.path.isdir(states_dir):
            print(colored("No states directory to backup.", "yellow"))
            return False
        
        # 수정: .zip 처리를 명확하게
        if not backup_path.lower().endswith(".zip"):
            backup_path += ".zip"
        base_dir = os.path.dirname(backup_path)
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)
        
        base_name = backup_path[:-4]  # .zip 제거
        shutil.make_archive(base_name, 'zip', states_dir)
        print(colored(f"All states backed up to {backup_path}", "green"))
        return True
    except Exception as e:
        print(colored(f"Error backing up states: {str(e)}", "red"))
        return False

def restore_states_from_backup(backup_path: str) -> bool:
    try:
        if not os.path.exists(backup_path):
            print(colored(f"No backup file found: {backup_path}", "red"))
            return False
        states_dir = "resources/status"
        if os.path.exists(states_dir):
            shutil.rmtree(states_dir)
        os.makedirs(states_dir, exist_ok=True)
        shutil.unpack_archive(backup_path, states_dir)
        print(colored(f"States restored from {backup_path}", "green"))
        return True
    except Exception as e:
        print(colored(f"Error restoring states: {str(e)}", "red"))
        return False
