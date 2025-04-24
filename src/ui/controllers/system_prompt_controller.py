import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget # QWidget 추가
# from dotenv import load_dotenv, set_key, find_dotenv # .env 사용 안 함

# 변경된 경로에서 import
from utils.helpers import get_resource_path, get_project_root
from core.services.config_service import ConfigService # ConfigService import

# MainWindow 타입 힌트
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ui.main_window import MainWindow

# 함수 형태로 유지 (MainWindow 또는 SettingsDialog에서 호출)
def apply_default_system_prompt(main_window: 'MainWindow'):
    """
    Loads the default system prompt specified in config.yml into the system_tab.
    Handles both relative (to project root) and absolute paths.
    """
    # MainWindow가 가지고 있는 ConfigService 사용
    if not hasattr(main_window, 'config_service'):
        print("Error: ConfigService not found in MainWindow.")
        return

    config_service: ConfigService = main_window.config_service
    settings = config_service.get_settings()
    default_system_prompt_path_str = settings.default_system_prompt
    prompt_source = ""
    prompt_path = "" # Initialize prompt_path

    if default_system_prompt_path_str:
        prompt_path_input = default_system_prompt_path_str
        # 설정 파일의 경로는 프로젝트 루트 기준 상대 경로 또는 절대 경로로 간주
        if not os.path.isabs(prompt_path_input):
             # 상대 경로일 경우 프로젝트 루트 기준으로 절대 경로 생성
             try:
                 project_root = get_project_root()
                 prompt_path = str(project_root / prompt_path_input)
                 prompt_source = f"config.yml (relative: {prompt_path_input})"
             except Exception as e:
                 print(f"Error resolving relative path '{prompt_path_input}': {e}")
                 main_window.status_bar.showMessage(f"기본 시스템 프롬프트 상대 경로 오류: {prompt_path_input}")
                 return
        else:
            # 절대 경로인 경우 그대로 사용
            prompt_path = prompt_path_input
            prompt_source = f"config.yml (absolute: {os.path.basename(prompt_path_input)})"
    else:
        # 설정값이 없으면 기본값(XML Guide) 사용 시도
        default_path_relative = os.path.join("prompts", "system", "XML_Prompt_Guide.md")
        try:
            prompt_path = get_resource_path(default_path_relative)
            prompt_source = f"Default ({os.path.basename(default_path_relative)})"
            print(f"default_system_prompt not set in config, attempting to load default: {default_path_relative}")
        except Exception as e:
             print(f"Error getting resource path for default prompt: {e}")
             main_window.status_bar.showMessage("기본 시스템 프롬프트 경로를 찾을 수 없습니다.")
             return

    # 파일 존재 여부 확인
    if not prompt_path or not os.path.exists(prompt_path):
        print(f"Default system prompt file not found at resolved path: {prompt_path}")
        main_window.status_bar.showMessage(
            f"기본 시스템 프롬프트 파일 없음: {os.path.basename(default_system_prompt_path_str or 'Default')}"
        )
        return

    # 파일 로드 및 UI 업데이트
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        main_window.system_tab.setText(content)
        print(f"Default system prompt loaded from: {prompt_path}")
        main_window.status_bar.showMessage(f"기본 시스템 프롬프트 로드 완료: {prompt_source}")
    except Exception as e:
        print(f"Error loading default system prompt file '{prompt_path}': {e}")
        main_window.status_bar.showMessage(f"기본 시스템 프롬프트 로드 중 오류: {str(e)}")


def select_default_system_prompt(config_service: ConfigService, parent_widget: Optional[QWidget] = None) -> Optional[str]:
    """
    Opens a file dialog to select a default system prompt file (.md, .txt).
    Returns the path to be saved (relative to project root if possible, otherwise absolute).

    Args:
        config_service: The ConfigService instance.
        parent_widget: The parent widget for the file dialog.

    Returns:
        The path string to be saved in config.yml, or None if cancelled.
    """
    settings = config_service.get_settings()
    current_path_str = settings.default_system_prompt
    initial_dir = os.path.expanduser("~") # Default initial directory

    # Determine initial directory for file dialog
    try:
        project_root = get_project_root()
        # Try to resolve current path (relative or absolute)
        if current_path_str:
            resolved_path = current_path_str
            if not os.path.isabs(current_path_str):
                resolved_path = str(project_root / current_path_str)

            if os.path.exists(resolved_path):
                initial_dir = os.path.dirname(resolved_path)
            elif os.path.isdir(str(project_root / "resources" / "prompts" / "system")):
                 initial_dir = str(project_root / "resources" / "prompts" / "system")
        elif os.path.isdir(str(project_root / "resources" / "prompts" / "system")):
             initial_dir = str(project_root / "resources" / "prompts" / "system")
    except Exception as e:
        print(f"Error determining initial directory: {e}")
        # Fallback to user home if error occurs

    path, _ = QFileDialog.getOpenFileName(
        parent_widget, # 부모 위젯 전달
        "기본 시스템 프롬프트 선택",
        initial_dir,
        "Text/Markdown Files (*.txt *.md);;All Files (*.*)"
    )

    if path:
        try:
            # 경로를 프로젝트 루트 기준 상대 경로로 변환 시도
            project_root_str = str(get_project_root())
            # Use os.path.normpath and os.path.abspath for reliable comparison
            abs_path = os.path.abspath(path)
            abs_project_root = os.path.abspath(project_root_str)

            if abs_path.startswith(abs_project_root):
                # Calculate relative path and normalize separators to forward slashes
                relative_path = os.path.relpath(abs_path, abs_project_root).replace(os.sep, '/')
                print(f"Default system prompt selected (relative path): {relative_path}")
                return relative_path
            else:
                # 프로젝트 외부는 정규화된 절대 경로 저장 (forward slashes)
                absolute_path_normalized = abs_path.replace(os.sep, '/')
                print(f"Default system prompt selected (absolute path): {absolute_path_normalized}")
                QMessageBox.information(parent_widget, "정보", "프로젝트 외부 경로는 절대 경로로 저장됩니다.")
                return absolute_path_normalized

        except Exception as e:
            print(f"Error processing selected path: {e}")
            QMessageBox.warning(
                parent_widget,
                "오류",
                f"경로 처리 중 오류 발생: {str(e)}"
            )
            return None
    return None # 사용자가 취소한 경우
