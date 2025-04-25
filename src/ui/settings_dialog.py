import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QLabel, QPlainTextEdit, QFileDialog, QMessageBox, QGroupBox, QHBoxLayout, QComboBox,
    QCheckBox, QApplication
)
from PyQt5.QtCore import Qt
from typing import Optional, Set, List

# 서비스 및 컨트롤러 함수 import
from core.services.config_service import ConfigService
from core.pydantic_models.config_settings import ConfigSettings
from ui.controllers.system_prompt_controller import select_default_system_prompt # Keep for browsing

# MainWindow 타입 힌트 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

class SettingsDialog(QDialog):
    """
    환경 설정을 표시하는 다이얼로그 창.
    DB에서 로드된 설정을 보여주며, .gitignore 파일 편집/저장 기능은 유지합니다.
    config.yml 관련 설정 저장은 비활성화됩니다.
    """
    def __init__(self, main_window: 'MainWindow', parent=None):
        super().__init__(parent)
        self.mw = main_window # MainWindow 참조
        self.config_service = main_window.config_service
        self.settings: Optional[ConfigSettings] = None # Load in load_config_settings

        self.setWindowTitle("환경 설정 (읽기 전용 - DB 기반)") # Title updated
        self.setMinimumWidth(600)

        # --- UI 요소 생성 ---
        # 기본 시스템 프롬프트 (Read-only path, Browse still functional for viewing/copying path)
        self.default_prompt_group = QGroupBox("기본 시스템 프롬프트 (DB 설정)")
        prompt_layout = QHBoxLayout()
        self.default_prompt_path_edit = QLineEdit()
        self.default_prompt_path_edit.setReadOnly(True) # Read-only
        self.browse_prompt_button = QPushButton("경로 복사/확인...") # Button text changed
        prompt_layout.addWidget(self.default_prompt_path_edit)
        prompt_layout.addWidget(self.browse_prompt_button)
        self.default_prompt_group.setLayout(prompt_layout)

        # LLM 기본 모델 (Read-only)
        self.llm_model_group = QGroupBox("LLM 기본 모델명 (DB 설정)")
        llm_model_layout = QFormLayout()
        self.gemini_default_model_edit = QLineEdit(); self.gemini_default_model_edit.setReadOnly(True)
        self.claude_default_model_edit = QLineEdit(); self.claude_default_model_edit.setReadOnly(True)
        # GPT 모델 추가 (Read-only)
        self.gpt_default_model_edit = QLineEdit(); self.gpt_default_model_edit.setReadOnly(True)
        llm_model_layout.addRow("Gemini 기본 모델:", self.gemini_default_model_edit)
        llm_model_layout.addRow("Claude 기본 모델:", self.claude_default_model_edit)
        llm_model_layout.addRow("GPT 기본 모델:", self.gpt_default_model_edit) # GPT 필드 추가
        self.llm_model_group.setLayout(llm_model_layout)

        # API 키 (Read-only, masked)
        self.api_key_group = QGroupBox("API 키 (DB 설정)")
        api_key_layout = QFormLayout()
        self.gemini_api_key_edit = QLineEdit()
        self.gemini_api_key_edit.setEchoMode(QLineEdit.Password)
        self.gemini_api_key_edit.setReadOnly(True)
        self.anthropic_api_key_edit = QLineEdit()
        self.anthropic_api_key_edit.setEchoMode(QLineEdit.Password)
        self.anthropic_api_key_edit.setReadOnly(True)
        api_key_layout.addRow("Gemini API Key:", self.gemini_api_key_edit)
        api_key_layout.addRow("Anthropic API Key:", self.anthropic_api_key_edit)
        self.api_key_group.setLayout(api_key_layout)

        # 파일 필터링 (Read-only)
        self.filtering_group = QGroupBox("파일 필터링 (DB 설정)")
        filtering_layout = QFormLayout()
        self.allowed_extensions_edit = QLineEdit()
        self.allowed_extensions_edit.setReadOnly(True)
        self.excluded_dirs_edit = QPlainTextEdit()
        self.excluded_dirs_edit.setReadOnly(True)
        self.default_ignore_list_edit = QPlainTextEdit()
        self.default_ignore_list_edit.setReadOnly(True)
        filtering_layout.addRow("허용 확장자:", self.allowed_extensions_edit)
        filtering_layout.addRow("제외 폴더/파일:", self.excluded_dirs_edit)
        filtering_layout.addRow("기본 무시 목록:", self.default_ignore_list_edit)
        self.filtering_group.setLayout(filtering_layout)

        # .gitignore 편집 (Functionality remains)
        self.gitignore_group = QGroupBox(".gitignore 편집 (현재 프로젝트)")
        gitignore_layout = QVBoxLayout()
        gitignore_button_layout = QHBoxLayout()
        self.load_gitignore_button = QPushButton("불러오기")
        self.save_gitignore_button = QPushButton("저장하기") # This save is for .gitignore only
        gitignore_button_layout.addWidget(self.load_gitignore_button)
        gitignore_button_layout.addWidget(self.save_gitignore_button)
        gitignore_button_layout.addStretch()
        self.gitignore_edit = QPlainTextEdit()
        self.gitignore_edit.setPlaceholderText("프로젝트 폴더 선택 후 '.gitignore' 내용을 불러오거나 편집/저장하세요.")
        gitignore_layout.addLayout(gitignore_button_layout)
        gitignore_layout.addWidget(self.gitignore_edit)
        self.gitignore_group.setLayout(gitignore_layout)
        self.gitignore_group.setEnabled(bool(self.mw.current_project_folder))

        # 버튼 박스 (Save removed, Close added)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close) # Only Close button
        # self.button_box.button(QDialogButtonBox.Save).setText("설정 저장") # Remove Save button

        # --- 레이아웃 설정 ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.default_prompt_group)
        main_layout.addWidget(self.llm_model_group)
        main_layout.addWidget(self.api_key_group)
        main_layout.addWidget(self.filtering_group)
        main_layout.addWidget(self.gitignore_group)
        main_layout.addWidget(self.button_box)

        # --- 시그널 연결 ---
        self.browse_prompt_button.clicked.connect(self.browse_or_copy_default_prompt) # Changed function
        self.load_gitignore_button.clicked.connect(self.load_gitignore)
        self.save_gitignore_button.clicked.connect(self.save_gitignore) # .gitignore save remains
        # self.button_box.accepted.connect(self.save_config_settings) # Removed connection
        self.button_box.rejected.connect(self.reject) # Close button uses reject
        self.button_box.clicked.connect(self.handle_button_click) # Handle close explicitly if needed

        # --- 초기 설정값 로드 ---
        self.load_config_settings()
        if self.mw.current_project_folder:
            self.load_gitignore()

    def handle_button_click(self, button):
        """Handle button clicks, specifically for the Close button."""
        role = self.button_box.buttonRole(button)
        if role == QDialogButtonBox.RejectRole: # Close button triggers RejectRole
            self.reject()

    def load_config_settings(self):
        """UI 위젯에 현재 DB 설정값을 로드합니다."""
        try:
            self.settings = self.config_service.get_settings() # 최신 설정 로드
            if not self.settings:
                 QMessageBox.critical(self, "오류", "DB에서 설정을 로드하지 못했습니다.")
                 # Disable UI elements or close dialog? For now, show empty.
                 return

            self.default_prompt_path_edit.setText(self.settings.default_system_prompt or "")
            self.gemini_default_model_edit.setText(self.settings.gemini_default_model or "")
            self.claude_default_model_edit.setText(self.settings.claude_default_model or "")
            self.gpt_default_model_edit.setText(self.settings.gpt_default_model or "") # Load GPT model
            self.gemini_api_key_edit.setText(self.settings.gemini_api_key or "")
            self.anthropic_api_key_edit.setText(self.settings.anthropic_api_key or "")

            # Set<str> -> str (UI 표시용)
            self.allowed_extensions_edit.setText(", ".join(sorted(list(self.settings.allowed_extensions or set()))))
            self.excluded_dirs_edit.setPlainText("\n".join(sorted(list(self.settings.excluded_dirs or set()))))
            self.default_ignore_list_edit.setPlainText("\n".join(sorted(self.settings.default_ignore_list or [])))

        except Exception as e:
            QMessageBox.critical(self, "로드 오류", f"설정을 로드하는 중 오류 발생:\n{e}")


    def browse_or_copy_default_prompt(self):
        """Copies the default prompt path to clipboard or shows a message."""
        path = self.default_prompt_path_edit.text()
        if path:
            clipboard = QApplication.clipboard()
            clipboard.setText(path)
            QMessageBox.information(self, "경로 복사됨", f"기본 시스템 프롬프트 경로가 클립보드에 복사되었습니다:\n{path}")
        else:
            QMessageBox.information(self, "정보", "설정된 기본 시스템 프롬프트 경로가 없습니다.")


    def load_gitignore(self):
        """현재 프로젝트 폴더의 .gitignore 파일을 로드하여 편집기에 표시합니다."""
        if not self.mw.current_project_folder:
            return

        gitignore_path = os.path.join(self.mw.current_project_folder, ".gitignore")
        content = ""
        try:
            if os.path.isfile(gitignore_path):
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.gitignore_edit.setPlainText(content)
            else:
                self.gitignore_edit.setPlainText("")
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
            QMessageBox.information(self, "성공", f".gitignore 파일이 저장되었습니다:\n{gitignore_path}")
            if hasattr(self.mw, 'file_tree_controller'):
                self.mw.file_tree_controller.load_gitignore_settings()
        except Exception as e:
            QMessageBox.critical(self, "오류", f".gitignore 파일을 저장하는 중 오류 발생:\n{e}")

    # --- save_config_settings is removed as saving config to DB is disabled ---
    # def save_config_settings(self): ...

