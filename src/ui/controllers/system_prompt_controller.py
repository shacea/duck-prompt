import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
# from dotenv import load_dotenv, set_key, find_dotenv # .env 사용 안 함

# 변경된 경로에서 import
from utils.helpers import get_resource_path, get_project_root
from core.services.config_service import ConfigService # ConfigService import

# MainWindow 타입 힌트
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow

# 함수 형태로 유지 (MainWindow에서 직접 호출)
def apply_default_system_prompt(main_window: 'MainWindow'):
    """
    Loads the default system prompt specified in config.yml into the system_tab.
    """
    # MainWindow가 가지고 있는 ConfigService 사용
    if not hasattr(main_window, 'config_service'):
        print("Error: ConfigService not found in MainWindow.")
        return

    config_service: ConfigService = main_window.config_service
    settings = config_service.get_settings()
    default_system_prompt_path_str = settings.default_system_prompt
    prompt_source = ""

    if default_system_prompt_path_str:
        prompt_path = default_system_prompt_path_str
        # 설정 파일의 경로는 프로젝트 루트 기준 상대 경로 또는 절대 경로로 간주
        if not os.path.isabs(prompt_path):
             prompt_path = str(get_project_root() / prompt_path)
        prompt_source = f"config.yml ({os.path.basename(default_system_prompt_path_str)})"
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
    if not os.path.exists(prompt_path):
        print(f"Default system prompt file not found at: {prompt_path}")
        main_window.status_bar.showMessage(
            f"기본 시스템 프롬프트 파일 없음: {os.path.basename(prompt_path)}"
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


def select_default_system_prompt(main_window: 'MainWindow'):
    """
    Opens a file dialog to select a default system prompt file (.md, .txt)
    and updates the default_system_prompt path in config.yml.
    """
    if not hasattr(main_window, 'config_service'):
        print("Error: ConfigService not found in MainWindow.")
        return
    config_service: ConfigService = main_window.config_service

    initial_dir = get_resource_path(os.path.join("prompts", "system"))
    if not os.path.isdir(initial_dir):
        initial_dir = os.path.expanduser("~")

    path, _ = QFileDialog.getOpenFileName(
        main_window,
        "기본 시스템 프롬프트 선택",
        initial_dir,
        "Text/Markdown Files (*.txt *.md);;All Files (*.*)"
    )

    if path:
        try:
            # 경로를 프로젝트 루트 기준 상대 경로로 변환 시도
            project_root_str = str(get_project_root())
            if path.startswith(project_root_str):
                relative_path = os.path.relpath(path, project_root_str).replace(os.sep, '/')
            else:
                # 프로젝트 외부는 절대 경로 저장 또는 사용자에게 경고
                # 여기서는 절대 경로 저장 (정규화)
                relative_path = path.replace(os.sep, '/')
                # QMessageBox.information(main_window, "정보", "프로젝트 외부 경로는 절대 경로로 저장됩니다.")

            # ConfigService를 통해 설정 업데이트 및 저장
            config_service.update_settings(default_system_prompt=relative_path)

            print(f"default_system_prompt set to: {relative_path} in config.yml")
            QMessageBox.information(
                main_window,
                "설정 완료",
                f"기본 시스템 프롬프트가 설정되었습니다:\n{path}\n\n설정이 즉시 적용되었습니다."
            )
            # 즉시 적용
            apply_default_system_prompt(main_window)
        except Exception as e:
            print(f"Error updating config.yml: {e}")
            QMessageBox.warning(
                main_window,
                "오류",
                f"설정 파일 업데이트 중 오류 발생: {str(e)}"
            )
