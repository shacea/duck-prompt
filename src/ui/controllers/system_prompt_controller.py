import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from dotenv import load_dotenv, set_key, find_dotenv

# 변경된 경로에서 import
from utils.helpers import get_resource_path # 필요시 사용

# .env 파일 경로 (프로젝트 루트 기준)
# find_dotenv()는 현재 디렉토리부터 상위로 올라가며 .env를 찾음
# src/ui/controllers/system_prompt_controller.py 기준 상위 3단계
project_root_from_controller = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
DOTENV_PATH = find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=False)

if not DOTENV_PATH:
    # .env 파일이 없으면 프로젝트 루트에 생성되도록 경로 지정
    DOTENV_PATH = os.path.join(project_root_from_controller, '.env')
    print(f".env file not found, will create/use path: {DOTENV_PATH}")


def apply_default_system_prompt(main_window):
    """
    Loads the default system prompt specified in .env into the system_tab.
    If DEFAULT_SYSTEM_PROMPT is empty or not set, tries to load XML_Prompt_Guide.md.
    """
    load_dotenv(dotenv_path=DOTENV_PATH, override=True) # override=True로 최신값 반영

    default_system_prompt_path = os.getenv("DEFAULT_SYSTEM_PROMPT")

    if not default_system_prompt_path:
        # 환경 변수가 없거나 비어 있으면 기본값 로드 시도
        default_path_relative = os.path.join("prompts", "system", "XML_Prompt_Guide.md")
        try:
            default_system_prompt_path = get_resource_path(default_path_relative)
            print(f"DEFAULT_SYSTEM_PROMPT not set, attempting to load default: {default_path_relative}")
        except Exception as e:
             print(f"Error getting resource path for default prompt: {e}")
             main_window.status_bar.showMessage("기본 시스템 프롬프트 경로를 찾을 수 없습니다.")
             return

    # 파일 존재 여부 확인
    if not os.path.exists(default_system_prompt_path):
        print(f"Default system prompt file not found at: {default_system_prompt_path}")
        main_window.status_bar.showMessage(
            f"기본 시스템 프롬프트 파일 없음: {os.path.basename(default_system_prompt_path)}"
        )
        # 파일이 없을 경우 UI를 비우거나, 이전 내용을 유지할 수 있음
        # main_window.system_tab.clear()
        return

    # 파일 로드 및 UI 업데이트
    try:
        with open(default_system_prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        main_window.system_tab.setText(content) # MainWindow의 system_tab 직접 접근
        print(f"Default system prompt loaded from: {default_system_prompt_path}")
        main_window.status_bar.showMessage(f"기본 시스템 프롬프트 로드 완료: {os.path.basename(default_system_prompt_path)}")
    except Exception as e:
        print(f"Error loading default system prompt file: {e}")
        main_window.status_bar.showMessage(f"기본 시스템 프롬프트 로드 중 오류: {str(e)}")


def select_default_system_prompt(main_window):
    """
    Opens a file dialog to select a default system prompt file (.md, .txt)
    and updates the DEFAULT_SYSTEM_PROMPT path in the .env file.
    """
    # 파일 선택 다이얼로그
    # 기본 경로는 resources/prompts/system 또는 사용자 홈 디렉토리
    initial_dir = get_resource_path(os.path.join("prompts", "system"))
    if not os.path.isdir(initial_dir):
        initial_dir = os.path.expanduser("~")

    path, _ = QFileDialog.getOpenFileName(
        main_window,
        "기본 시스템 프롬프트 선택",
        initial_dir, # 시작 디렉토리
        "Text/Markdown Files (*.txt *.md);;All Files (*.*)"
    )

    if path:
        try:
            # .env 파일에 경로 업데이트 (기존 값 덮어쓰기 또는 추가)
            # set_key는 .env 파일이 없으면 생성함
            # 경로 구분자를 OS 기본값 대신 '/'로 저장 (호환성)
            normalized_path = path.replace(os.sep, '/')
            set_key(DOTENV_PATH, "DEFAULT_SYSTEM_PROMPT", normalized_path, quote_mode='always')

            print(f"DEFAULT_SYSTEM_PROMPT set to: {normalized_path} in {DOTENV_PATH}")
            QMessageBox.information(
                main_window,
                "설정 완료",
                f"기본 시스템 프롬프트가 설정되었습니다:\n{path}\n\n프로그램 재시작 시 적용됩니다."
            )
            # 즉시 적용하려면 apply_default_system_prompt 호출 가능
            # apply_default_system_prompt(main_window)
        except Exception as e:
            print(f"Error updating .env file: {e}")
            QMessageBox.warning(
                main_window,
                "오류",
                f".env 파일 업데이트 중 오류 발생: {str(e)}"
            )
