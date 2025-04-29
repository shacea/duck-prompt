import os
import json
import shutil
from datetime import datetime
from typing import Optional, List
from pydantic import ValidationError

from core.pydantic_models.app_state import AppState
from utils.helpers import get_resource_path # 리소스 경로 함수 사용

# 상태 파일 저장 디렉토리 (resources/status)
STATUS_DIR = get_resource_path("status")

class StateService:
    def __init__(self, status_dir: str = STATUS_DIR):
        self.status_dir = status_dir
        os.makedirs(self.status_dir, exist_ok=True)

    def _get_state_file_path(self, filename: str) -> str:
        """Constructs the full path for a state file."""
        # 파일 이름에 .json 확장자가 없으면 추가
        if not filename.lower().endswith(".json"):
            filename += ".json"
        return os.path.join(self.status_dir, filename)

    def save_state(self, state: AppState, filename: str) -> bool:
        """Saves the application state (Pydantic model) to a JSON file."""
        file_path = self._get_state_file_path(filename)
        try:
            # Pydantic 모델을 JSON 문자열로 직렬화 (indent 적용)
            state_json = state.model_dump_json(indent=4)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(state_json)
            print(f"State saved successfully to {file_path}")
            return True
        except ValidationError as e:
            print(f"State validation error before saving: {e}")
            return False
        except Exception as e:
            print(f"Error saving state to {file_path}: {str(e)}")
            return False

    def load_state(self, filename: str) -> Optional[AppState]:
        """Loads application state from a JSON file into a Pydantic model."""
        file_path = self._get_state_file_path(filename)
        if not os.path.exists(file_path):
            print(f"State file not found: {file_path}. Returning default state.")
            return AppState() # 파일 없으면 기본 상태 반환

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            # JSON 데이터를 Pydantic 모델로 파싱 및 유효성 검사
            state = AppState.model_validate(state_data)
            print(f"State loaded successfully from {file_path}")
            return state
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}. Returning default state.")
            return AppState()
        except ValidationError as e:
            print(f"State validation error loading from {file_path}: {e}. Returning default state.")
            # 유효성 검사 실패 시 기본값 반환 또는 더 엄격한 처리 가능
            return AppState()
        except Exception as e:
            print(f"Error loading state from {file_path}: {str(e)}. Returning default state.")
            return AppState()

    def import_state_from_file(self, import_path: str) -> Optional[AppState]:
        """Imports state from an external JSON file."""
        if not os.path.exists(import_path):
            print(f"Import file not found: {import_path}")
            return None # 가져올 파일 없으면 None 반환

        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            state = AppState.model_validate(state_data)
            print(f"State imported successfully from {import_path}")
            return state
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from import file {import_path}: {e}")
            return None
        except ValidationError as e:
            print(f"Imported state validation error: {e}")
            return None
        except Exception as e:
            print(f"Error importing state from {import_path}: {str(e)}")
            return None

    def export_state_to_file(self, state: AppState, export_path: str) -> bool:
        """Exports the current state to an external JSON file."""
        try:
            dir_path = os.path.dirname(export_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            state_json = state.model_dump_json(indent=4)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(state_json)
            print(f"State exported successfully to {export_path}")
            return True
        except ValidationError as e:
             print(f"State validation error before exporting: {e}")
             return False
        except Exception as e:
            print(f"Error exporting state to {export_path}: {str(e)}")
            return False

    def list_states(self) -> List[str]:
        """Lists available state files (JSON) in the status directory."""
        if not os.path.exists(self.status_dir):
            return []
        try:
            files = os.listdir(self.status_dir)
            # .json 파일만 필터링
            return [f for f in files if f.lower().endswith(".json")]
        except Exception as e:
            print(f"Error listing states in {self.status_dir}: {e}")
            return []

    def delete_state(self, filename: str) -> bool:
        """Deletes a specific state file."""
        file_path = self._get_state_file_path(filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted state file: {file_path}")
                return True
            except Exception as e:
                print(f"Error deleting state file {file_path}: {e}")
                return False
        else:
            print(f"State file not found for deletion: {file_path}")
            return False

    def backup_all_states(self, backup_path: str) -> bool:
        """Backs up all state files into a zip archive."""
        if not os.path.isdir(self.status_dir):
            print("Status directory does not exist. Nothing to backup.")
            return False

        # Ensure backup path ends with .zip
        if not backup_path.lower().endswith(".zip"):
            backup_path += ".zip"

        base_dir = os.path.dirname(backup_path)
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)

        # shutil.make_archive needs the archive name without extension
        archive_name = backup_path[:-4]

        try:
            shutil.make_archive(archive_name, 'zip', self.status_dir)
            print(f"All states successfully backed up to {backup_path}")
            return True
        except Exception as e:
            print(f"Error backing up states to {backup_path}: {str(e)}")
            return False

    def restore_states_from_backup(self, backup_path: str) -> bool:
        """Restores states from a zip archive, overwriting existing ones."""
        if not os.path.exists(backup_path):
            print(f"Backup file not found: {backup_path}")
            return False

        try:
            # Remove existing status directory before restoring if it exists
            if os.path.exists(self.status_dir):
                shutil.rmtree(self.status_dir)
            os.makedirs(self.status_dir, exist_ok=True) # Ensure directory exists

            # Unpack the archive into the status directory
            shutil.unpack_archive(backup_path, self.status_dir, 'zip')
            print(f"States successfully restored from {backup_path} to {self.status_dir}")
            return True
        except Exception as e:
            print(f"Error restoring states from {backup_path}: {str(e)}")
            return False
