

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QLabel, QPlainTextEdit, QFileDialog, QMessageBox, QGroupBox, QHBoxLayout, QComboBox,
    QCheckBox # QCheckBox import
)
from PyQt5.QtCore import Qt
from typing import Optional, Set, List

# 서비스 및 컨트롤러 함수 import
from core.services.config_service import ConfigService
from core.pydantic_models.config_settings import ConfigSettings
# from ui.controllers.system_prompt_controller import select_default_system_prompt # 이제 직접 사용 안 함

# MainWindow 타입 힌트 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

class SettingsDialog(QDialog):
    """
    환경 설정을 관리하는 다이얼로그 창.
    config.yml 파일의 내용을 로드하고 저장하며, .gitignore 파일도 관리합니다.
    """
    def __init__(self, main_window: 'MainWindow', parent=None):
        super().__init__(parent)
        self.mw = main_window # MainWindow 참조
        self.config_service = main_window.config_service
        # self.settings: ConfigSettings = self.config_service.get_settings() # 현재 설정 로드 (load_config_settings에서 수행)

        self.setWindowTitle("환경 설정")
        self.setMinimumWidth(600)

        # --- UI 요소 생성 ---
        # 기본 시스템 프롬프트
        self.default_prompt_group = QGroupBox("기본 시스템 프롬프트")
        prompt_layout = QHBoxLayout()
        self.default_prompt_path_edit = QLineEdit()
        self.browse_prompt_button = QPushButton("찾아보기...")
        prompt_layout.addWidget(self.default_prompt_path_edit)
        prompt_layout.addWidget(self.browse_prompt_button)
        self.default_prompt_group.setLayout(prompt_layout)

        # LLM 기본 모델
        self.llm_model_group = QGroupBox("LLM 기본 모델명")
        llm_model_layout = QFormLayout()
        self.gemini_default_model_edit = QLineEdit()
        self.claude_default_model_edit = QLineEdit()
        llm_model_layout.addRow("Gemini 기본 모델:", self.gemini_default_model_edit)
        llm_model_layout.addRow("Claude 기본 모델:", self.claude_default_model_edit)
        self.llm_model_group.setLayout(llm_model_layout)

        # API 키
        self.api_key_group = QGroupBox("API 키")
        api_key_layout = QFormLayout()
        self.gemini_api_key_edit = QLineEdit()
        self.gemini_api_key_edit.setEchoMode(QLineEdit.Password)
        self.anthropic_api_key_edit = QLineEdit()
        self.anthropic_api_key_edit.setEchoMode(QLineEdit.Password)
        api_key_layout.addRow("Gemini API Key:", self.gemini_api_key_edit)
        api_key_layout.addRow("Anthropic API Key:", self.anthropic_api_key_edit)
        self.api_key_group.setLayout(api_key_layout)

        # --- Gemini Parameters Group 제거 ---
        # self.gemini_params_group = QGroupBox("Gemini API 파라미터")
        # ... (관련 위젯 생성 코드 제거) ...
        # self.gemini_params_group.setLayout(gemini_params_layout)
        # -----------------------------


        # 파일 필터링
        self.filtering_group = QGroupBox("파일 필터링")
        filtering_layout = QFormLayout()
        self.allowed_extensions_edit = QLineEdit()
        self.allowed_extensions_edit.setPlaceholderText(".py, .txt, .md (쉼표 또는 공백으로 구분)")
        self.excluded_dirs_edit = QPlainTextEdit()
        self.excluded_dirs_edit.setPlaceholderText("제외할 폴더/파일 패턴 (한 줄에 하나씩, .gitignore 형식)")
        self.default_ignore_list_edit = QPlainTextEdit()
        self.default_ignore_list_edit.setPlaceholderText("기본 무시 패턴 (한 줄에 하나씩)")
        filtering_layout.addRow("허용 확장자:", self.allowed_extensions_edit)
        filtering_layout.addRow("제외 폴더/파일:", self.excluded_dirs_edit)
        filtering_layout.addRow("기본 무시 목록:", self.default_ignore_list_edit)
        self.filtering_group.setLayout(filtering_layout)

        # .gitignore 편집
        self.gitignore_group = QGroupBox(".gitignore 편집 (현재 프로젝트)")
        gitignore_layout = QVBoxLayout()
        gitignore_button_layout = QHBoxLayout()
        self.load_gitignore_button = QPushButton("불러오기")
        self.save_gitignore_button = QPushButton("저장하기")
        gitignore_button_layout.addWidget(self.load_gitignore_button)
        gitignore_button_layout.addWidget(self.save_gitignore_button)
        gitignore_button_layout.addStretch()
        self.gitignore_edit = QPlainTextEdit()
        self.gitignore_edit.setPlaceholderText("프로젝트 폴더 선택 후 '.gitignore' 내용을 불러오거나 편집/저장하세요.")
        gitignore_layout.addLayout(gitignore_button_layout)
        gitignore_layout.addWidget(self.gitignore_edit)
        self.gitignore_group.setLayout(gitignore_layout)
        # 프로젝트 폴더가 없으면 비활성화
        self.gitignore_group.setEnabled(bool(self.mw.current_project_folder))


        # 버튼 박스 (config.yml 저장용)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setText("설정 저장")

        # --- 레이아웃 설정 ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.default_prompt_group)
        main_layout.addWidget(self.llm_model_group)
        main_layout.addWidget(self.api_key_group)
        # main_layout.addWidget(self.gemini_params_group) # Gemini 파라미터 그룹 제거
        main_layout.addWidget(self.filtering_group)
        main_layout.addWidget(self.gitignore_group) # gitignore 그룹 추가
        main_layout.addWidget(self.button_box)

        # --- 시그널 연결 ---
        self.browse_prompt_button.clicked.connect(self.browse_default_prompt)
        self.load_gitignore_button.clicked.connect(self.load_gitignore)
        self.save_gitignore_button.clicked.connect(self.save_gitignore)
        self.button_box.accepted.connect(self.save_config_settings) # config.yml 저장 함수 연결
        self.button_box.rejected.connect(self.reject)

        # --- 초기 설정값 로드 ---
        self.load_config_settings()
        if self.mw.current_project_folder:
            self.load_gitignore() # 프로젝트 폴더 있으면 gitignore 자동 로드 시도

    def load_config_settings(self):
        """UI 위젯에 현재 config.yml 설정값을 로드합니다."""
        self.settings = self.config_service.get_settings() # 최신 설정 다시 로드
        self.default_prompt_path_edit.setText(self.settings.default_system_prompt or "")
        self.gemini_default_model_edit.setText(self.settings.gemini_default_model or "")
        self.claude_default_model_edit.setText(self.settings.claude_default_model or "")
        self.gemini_api_key_edit.setText(self.settings.gemini_api_key or "")
        self.anthropic_api_key_edit.setText(self.settings.anthropic_api_key or "")

        # Gemini Parameters 로드 로직 제거
        # self.gemini_temperature_edit.setText(str(self.settings.gemini_temperature))
        # self.gemini_enable_thinking_checkbox.setChecked(self.settings.gemini_enable_thinking)
        # self.gemini_thinking_budget_edit.setText(str(self.settings.gemini_thinking_budget))
        # self.gemini_enable_search_checkbox.setChecked(self.settings.gemini_enable_search)


        # Set<str> -> str (UI 표시용)
        self.allowed_extensions_edit.setText(", ".join(sorted(list(self.settings.allowed_extensions))))
        self.excluded_dirs_edit.setPlainText("\n".join(sorted(list(self.settings.excluded_dirs))))
        self.default_ignore_list_edit.setPlainText("\n".join(sorted(self.settings.default_ignore_list)))

    def browse_default_prompt(self):
        """기본 시스템 프롬프트 파일을 선택하는 다이얼로그를 엽니다."""
        # MainWindow에서 경로 선택 로직 사용 (프로젝트 루트 기준 상대/절대 경로 처리)
        from ui.controllers.system_prompt_controller import select_default_system_prompt
        selected_path = select_default_system_prompt(self.config_service, parent_widget=self)

        if selected_path is not None: # 사용자가 취소하지 않았다면
            self.default_prompt_path_edit.setText(selected_path)


    def load_gitignore(self):
        """현재 프로젝트 폴더의 .gitignore 파일을 로드하여 편집기에 표시합니다."""
        if not self.mw.current_project_folder:
            # QMessageBox.warning(self, "오류", "프로젝트 폴더가 선택되지 않았습니다.") # 메시지 제거
            return

        gitignore_path = os.path.join(self.mw.current_project_folder, ".gitignore")
        content = ""
        try:
            if os.path.isfile(gitignore_path):
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.gitignore_edit.setPlainText(content)
                # QMessageBox.information(self, "성공", ".gitignore 파일을 불러왔습니다.") # 메시지 제거
            else:
                self.gitignore_edit.setPlainText("") # 파일 없으면 비움
                # QMessageBox.information(self, "정보", ".gitignore 파일이 존재하지 않습니다.") # 메시지 제거
        except Exception as e:
            QMessageBox.critical(self, "오류", f".gitignore 파일을 불러오는 중 오류 발생:\n{e}")
            self.gitignore_edit.setPlainText(f"# 오류: {e}")

    def save_gitignore(self):
        """편집기 내용을 현재 프로젝트 폴더의 .gitignore 파일에 저장합니다."""
        if not self.mw.current_project_folder:
            QMessageBox.warning(self, "오류", "프로젝트 폴더가 선택되지 않았습니다.")
            return

        gitignore_path = os.path.join(self.mw.current_project_folder, ".gitignore")
        content = self.gitignore_edit.toPlainText()

        try:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(content)
            # QMessageBox.information(self, "성공", f".gitignore 파일이 저장되었습니다:\n{gitignore_path}") # 메시지 제거
            # 저장 후 메인 윈도우의 필터 업데이트 트리거
            if hasattr(self.mw, 'file_tree_controller'):
                self.mw.file_tree_controller.load_gitignore_settings()
        except Exception as e:
            QMessageBox.critical(self, "오류", f".gitignore 파일을 저장하는 중 오류 발생:\n{e}")


    def _parse_set_from_lineedit(self, text: str) -> Set[str]:
        """쉼표 또는 공백으로 구분된 문자열을 Set[str]으로 변환합니다."""
        if not text.strip():
            return set()
        items = [item.strip() for item in text.replace(',', ' ').split() if item.strip()]
        return set(items)

    def _parse_list_from_plaintextedit(self, text: str) -> List[str]:
        """여러 줄의 문자열을 List[str]으로 변환합니다."""
        return [line.strip() for line in text.splitlines() if line.strip()]

    def save_config_settings(self):
        """UI 위젯의 값을 읽어 ConfigService를 통해 config.yml 설정을 저장합니다."""
        try:
            # UI 값 읽기
            default_prompt = self.default_prompt_path_edit.text().strip() or None
            gemini_model = self.gemini_default_model_edit.text().strip()
            claude_model = self.claude_default_model_edit.text().strip()
            gemini_key = self.gemini_api_key_edit.text().strip() or None
            anthropic_key = self.anthropic_api_key_edit.text().strip() or None

            # Gemini Parameters 읽기 로직 제거
            # try:
            #     gemini_temperature = float(self.gemini_temperature_edit.text().strip())
            # except ValueError:
            #     QMessageBox.warning(self, "입력 오류", "Temperature는 유효한 숫자여야 합니다.")
            #     return # 저장 중단
            #
            # gemini_enable_thinking = self.gemini_enable_thinking_checkbox.isChecked()
            #
            # try:
            #     gemini_thinking_budget = int(self.gemini_thinking_budget_edit.text().strip())
            # except ValueError:
            #      QMessageBox.warning(self, "입력 오류", "Thinking Budget은 유효한 정수여야 합니다.")
            #      return # 저장 중단
            #
            # gemini_enable_search = self.gemini_enable_search_checkbox.isChecked()


            allowed_ext_set = self._parse_set_from_lineedit(self.allowed_extensions_edit.text())
            excluded_dirs_set = set(self._parse_list_from_plaintextedit(self.excluded_dirs_edit.toPlainText()))
            default_ignore_list = self._parse_list_from_plaintextedit(self.default_ignore_list_edit.toPlainText())

            # 업데이트할 설정 딕셔너리 생성 (Gemini 파라미터 제외)
            update_data = {
                "default_system_prompt": default_prompt,
                "gemini_default_model": gemini_model,
                "claude_default_model": claude_model,
                "gemini_api_key": gemini_key,
                "anthropic_api_key": anthropic_key,
                # "gemini_temperature": gemini_temperature, # Gemini 파라미터 제외
                # "gemini_enable_thinking": gemini_enable_thinking,
                # "gemini_thinking_budget": gemini_thinking_budget,
                # "gemini_enable_search": gemini_enable_search,
                "allowed_extensions": allowed_ext_set,
                "excluded_dirs": excluded_dirs_set,
                "default_ignore_list": default_ignore_list,
            }

            # ConfigService를 통해 업데이트 및 저장
            self.config_service.update_settings(**update_data)

            QMessageBox.information(self, "저장 완료", "환경 설정(config.yml)이 성공적으로 저장되었습니다.")
            self.accept() # 다이얼로그 닫기

        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"설정(config.yml)을 저장하는 중 오류가 발생했습니다:\n{e}")
