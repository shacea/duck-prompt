
import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from dotenv import load_dotenv

def apply_default_system_prompt(main_window):
    """
    .env에 설정된 DEFAULT_SYSTEM_PROMPT 경로를 읽어,
    해당 파일이 존재하면 system_tab에 로드.
    DEFAULT_SYSTEM_PROMPT가 ""(빈 문자열)인 경우 로드하지 않음.
    기본값은 resources/prompts/system/XML_Prompt_Guide.md 로 설정.
    """
    load_dotenv()

    # 기본값 설정
    default_value = "resources/prompts/system/XML_Prompt_Guide.md"
    default_system_prompt_path = os.getenv("DEFAULT_SYSTEM_PROMPT", default_value)
    print(f"기본 시스템 프롬프트 경로: {default_system_prompt_path}")
    # 빈 문자열인 경우(사용자가 로드 비활성화)
    if default_system_prompt_path == "":
        main_window.status_bar.showMessage("기본 시스템 프롬프트 로드 안 함: 빈 문자열 설정됨.")
        return

    # 파일 존재 여부 확인
    if not os.path.exists(default_system_prompt_path):
        main_window.status_bar.showMessage(
            f"시스템 프롬프트 경로가 존재하지 않아 로드 안 함: {default_system_prompt_path}"
        )
        return

    # 정상 로드 시도
    try:
        with open(default_system_prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        main_window.system_tab.setText(content)
        main_window.status_bar.showMessage(f"기본 시스템 프롬프트 로드 완료: {default_system_prompt_path}")
    except Exception as e:
        main_window.status_bar.showMessage(f"기본 시스템 프롬프트 로드 중 오류: {str(e)}")


def select_default_system_prompt(main_window):
    """
    '기본 시스템 프롬프트 지정' 버튼 클릭 시 실행.
    파일 다이얼로그로 Markdown/Text 파일을 선택받아
    .env 파일에 DEFAULT_SYSTEM_PROMPT 경로를 업데이트한다.
    """
    path, _ = QFileDialog.getOpenFileName(
        main_window,
        "기본 시스템 프롬프트 선택",
        os.path.expanduser("~"),
        "Text/Markdown Files (*.txt *.md);;All Files (*.*)"
    )
    if path:
        try:
            # 기존 .env 읽기
            lines = []
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
            except FileNotFoundError:
                # .env가 없으면 새로 생성
                pass

            updated = False
            for i, ln in enumerate(lines):
                if ln.startswith("DEFAULT_SYSTEM_PROMPT="):
                    lines[i] = f'DEFAULT_SYSTEM_PROMPT="{path}"'
                    updated = True
                    break
            if not updated:
                lines.append(f'DEFAULT_SYSTEM_PROMPT="{path}"')

            with open(".env", "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

            QMessageBox.information(
                main_window,
                "Info",
                f"기본 시스템 프롬프트가 설정되었습니다:\n{path}\n\n프로그램 재시작 후 적용됩니다."
            )
        except Exception as e:
            QMessageBox.warning(
                main_window,
                "Error",
                f"DEFAULT_SYSTEM_PROMPT 설정 중 오류: {str(e)}"
            )
