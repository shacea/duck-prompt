import os
import json
from termcolor import colored

def save_state(state: dict, filename: str) -> bool:
    """
    상태를 JSON 형식으로 파일에 저장합니다.
    filename은 'resources/status/' 아래의 파일명(확장자 없음)으로 가정합니다.
    """
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
    """
    상태를 파일에서 JSON 형식으로 로드합니다.
    filename은 'resources/status/' 아래의 파일명(확장자 없음)으로 가정합니다.
    """
    try:
        file_path = os.path.join("resources", "status", filename + ".json")
        if not os.path.exists(file_path):
            print(colored(f"No state file found at {file_path}", "yellow"))
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(colored(f"State loaded from {file_path}", "green"))
        return state
    except Exception as e:
        print(colored(f"Error loading state: {str(e)}", "red"))
        return {}

def import_state_from_file(path: str) -> dict:
    """
    외부 파일(아무 경로)에서 상태를 JSON으로 로드합니다.
    """
    try:
        if not os.path.exists(path):
            print(colored(f"No state file found at {path}", "yellow"))
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(colored(f"State imported from {path}", "green"))
        return state
    except Exception as e:
        print(colored(f"Error importing state: {str(e)}", "red"))
        return {}

def export_state_to_file(state: dict, path: str) -> bool:
    """
    상태를 외부 경로에 JSON으로 내보냅니다.
    """
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
