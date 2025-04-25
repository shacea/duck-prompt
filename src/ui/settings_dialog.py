import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QLabel, QPlainTextEdit, QFileDialog, QMessageBox, QGroupBox, QHBoxLayout, QComboBox,
    QCheckBox, QApplication, QListWidget, QListWidgetItem, QAbstractItemView, QInputDialog, QWidget
)
from PyQt5.QtCore import Qt
from typing import Optional, Set, List
from pydantic import ValidationError

# 서비스 및 컨트롤러 함수 import
from core.services.config_service import ConfigService
from core.pydantic_models.config_settings import ConfigSettings
from ui.controllers.system_prompt_controller import select_default_system_prompt
# MainWindow 타입 힌트 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

class SettingsDialog(QDialog):
    """
    환경 설정을 표시하고 수정하는 다이얼로그 창.
    DB에서 로드된 설정을 보여주고, 수정 후 DB에 저장합니다.
    .gitignore 파일 편집/저장 기능도 유지합니다.
    API 키 필드는 쓰기 가능하게 변경되었습니다. (저장 로직은 별도 관리 필요)
    사용 가능 LLM 모델 목록을 관리하는 기능이 추가되었습니다.
    """
    def __init__(self, main_window: 'MainWindow', parent=None):
        super().__init__(parent)
        self.mw = main_window # MainWindow 참조
        self.config_service = main_window.config_service
        self.settings: Optional[ConfigSettings] = None # Load in load_config_settings

        self.setWindowTitle("환경 설정") # Title updated
        self.setMinimumWidth(700) # 너비 증가

        # --- UI 요소 생성 ---
        # 기본 시스템 프롬프트
        self.default_prompt_group = QGroupBox("기본 시스템 프롬프트")
        prompt_layout = QHBoxLayout()
        self.default_prompt_path_edit = QLineEdit()
        self.default_prompt_path_edit.setPlaceholderText("프로젝트 루트 기준 상대 경로 또는 절대 경로")
        self.browse_prompt_button = QPushButton("찾아보기...") # Button text changed
        prompt_layout.addWidget(self.default_prompt_path_edit)
        prompt_layout.addWidget(self.browse_prompt_button)
        self.default_prompt_group.setLayout(prompt_layout)

        # LLM 기본 모델
        self.llm_model_group = QGroupBox("LLM 기본 모델명")
        llm_model_layout = QFormLayout()
        self.gemini_default_model_edit = QLineEdit()
        self.claude_default_model_edit = QLineEdit()
        self.gpt_default_model_edit = QLineEdit()
        llm_model_layout.addRow("Gemini 기본 모델:", self.gemini_default_model_edit)
        llm_model_layout.addRow("Claude 기본 모델:", self.claude_default_model_edit)
        llm_model_layout.addRow("GPT 기본 모델:", self.gpt_default_model_edit)
        self.llm_model_group.setLayout(llm_model_layout)

        # API 키 (쓰기 가능, 마스크됨)
        self.api_key_group = QGroupBox("API 키 (DB 설정 - 편집 가능, 저장은 별도 관리)") # 그룹 제목 변경
        api_key_layout = QFormLayout()
        self.gemini_api_key_edit = QLineEdit()
        self.gemini_api_key_edit.setEchoMode(QLineEdit.Password)
        # self.gemini_api_key_edit.setReadOnly(True) # 읽기 전용 해제
        self.anthropic_api_key_edit = QLineEdit()
        self.anthropic_api_key_edit.setEchoMode(QLineEdit.Password)
        # self.anthropic_api_key_edit.setReadOnly(True) # 읽기 전용 해제
        api_key_layout.addRow("Gemini API Key:", self.gemini_api_key_edit)
        api_key_layout.addRow("Anthropic API Key:", self.anthropic_api_key_edit)
        self.api_key_group.setLayout(api_key_layout)

        # 사용 가능 LLM 모델 관리 (신규 추가)
        self.available_models_group = QGroupBox("사용 가능 LLM 모델 목록 관리")
        available_models_main_layout = QHBoxLayout()

        # Gemini 모델 목록
        gemini_model_widget = QWidget()
        gemini_model_layout = QVBoxLayout(gemini_model_widget)
        gemini_model_layout.addWidget(QLabel("Gemini 모델:"))
        self.gemini_models_list = QListWidget()
        self.gemini_models_list.setSelectionMode(QAbstractItemView.SingleSelection)
        gemini_model_buttons = QHBoxLayout()
        self.add_gemini_model_btn = QPushButton("추가")
        self.remove_gemini_model_btn = QPushButton("제거")
        gemini_model_buttons.addWidget(self.add_gemini_model_btn)
        gemini_model_buttons.addWidget(self.remove_gemini_model_btn)
        gemini_model_layout.addWidget(self.gemini_models_list)
        gemini_model_layout.addLayout(gemini_model_buttons)

        # Claude 모델 목록
        claude_model_widget = QWidget()
        claude_model_layout = QVBoxLayout(claude_model_widget)
        claude_model_layout.addWidget(QLabel("Claude 모델:"))
        self.claude_models_list = QListWidget()
        self.claude_models_list.setSelectionMode(QAbstractItemView.SingleSelection)
        claude_model_buttons = QHBoxLayout()
        self.add_claude_model_btn = QPushButton("추가")
        self.remove_claude_model_btn = QPushButton("제거")
        claude_model_buttons.addWidget(self.add_claude_model_btn)
        claude_model_buttons.addWidget(self.remove_claude_model_btn)
        claude_model_layout.addWidget(self.claude_models_list)
        claude_model_layout.addLayout(claude_model_buttons)

        # GPT 모델 목록
        gpt_model_widget = QWidget()
        gpt_model_layout = QVBoxLayout(gpt_model_widget)
        gpt_model_layout.addWidget(QLabel("GPT 모델:"))
        self.gpt_models_list = QListWidget()
        self.gpt_models_list.setSelectionMode(QAbstractItemView.SingleSelection)
        gpt_model_buttons = QHBoxLayout()
        self.add_gpt_model_btn = QPushButton("추가")
        self.remove_gpt_model_btn = QPushButton("제거")
        gpt_model_buttons.addWidget(self.add_gpt_model_btn)
        gpt_model_buttons.addWidget(self.remove_gpt_model_btn)
        gpt_model_layout.addWidget(self.gpt_models_list)
        gpt_model_layout.addLayout(gpt_model_buttons)

        available_models_main_layout.addWidget(gemini_model_widget)
        available_models_main_layout.addWidget(claude_model_widget)
        available_models_main_layout.addWidget(gpt_model_widget)
        self.available_models_group.setLayout(available_models_main_layout)


        # 파일 필터링
        self.filtering_group = QGroupBox("파일 필터링")
        filtering_layout = QFormLayout()
        self.allowed_extensions_edit = QLineEdit()
        self.allowed_extensions_edit.setPlaceholderText("쉼표(,) 또는 공백으로 구분 (예: .py, .js .html)")
        self.excluded_dirs_edit = QPlainTextEdit()
        self.excluded_dirs_edit.setPlaceholderText("한 줄에 하나씩 입력 (예: node_modules/, *.log)")
        self.default_ignore_list_edit = QPlainTextEdit()
        self.default_ignore_list_edit.setPlaceholderText("한 줄에 하나씩 입력 (예: .git/, __pycache__/)")
        filtering_layout.addRow("허용 확장자:", self.allowed_extensions_edit)
        filtering_layout.addRow("제외 폴더/파일:", self.excluded_dirs_edit)
        filtering_layout.addRow("기본 무시 목록:", self.default_ignore_list_edit)
        self.filtering_group.setLayout(filtering_layout)

        # Gemini 파라미터
        self.gemini_group = QGroupBox("Gemini 파라미터")
        gemini_layout = QFormLayout()
        self.gemini_temp_edit = QLineEdit()
        self.gemini_thinking_checkbox = QCheckBox()
        self.gemini_budget_edit = QLineEdit()
        self.gemini_search_checkbox = QCheckBox()
        gemini_layout.addRow("Temperature (0.0 ~ 2.0):", self.gemini_temp_edit)
        gemini_layout.addRow("Enable Thinking:", self.gemini_thinking_checkbox)
        gemini_layout.addRow("Thinking Budget:", self.gemini_budget_edit)
        gemini_layout.addRow("Enable Search:", self.gemini_search_checkbox)
        self.gemini_group.setLayout(gemini_layout)

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

        # 버튼 박스 (Save and Close)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        self.button_box.button(QDialogButtonBox.Save).setText("설정 저장")
        self.button_box.button(QDialogButtonBox.Close).setText("닫기")

        # --- 레이아웃 설정 ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.default_prompt_group)
        main_layout.addWidget(self.llm_model_group)
        main_layout.addWidget(self.api_key_group)
        main_layout.addWidget(self.available_models_group) # 사용 가능 모델 그룹 추가
        main_layout.addWidget(self.filtering_group)
        main_layout.addWidget(self.gemini_group) # Gemini 파라미터 그룹 추가
        main_layout.addWidget(self.gitignore_group)
        main_layout.addWidget(self.button_box)

        # --- 시그널 연결 ---
        self.browse_prompt_button.clicked.connect(self.browse_default_prompt) # Changed function
        self.load_gitignore_button.clicked.connect(self.load_gitignore)
        self.save_gitignore_button.clicked.connect(self.save_gitignore) # .gitignore save remains
        self.button_box.accepted.connect(self.save_config_settings) # Save button uses accept
        self.button_box.rejected.connect(self.reject) # Close button uses reject

        # 사용 가능 모델 추가/제거 버튼 시그널 연결
        self.add_gemini_model_btn.clicked.connect(lambda: self.add_model_to_list(self.gemini_models_list, "Gemini"))
        self.remove_gemini_model_btn.clicked.connect(lambda: self.remove_model_from_list(self.gemini_models_list))
        self.add_claude_model_btn.clicked.connect(lambda: self.add_model_to_list(self.claude_models_list, "Claude"))
        self.remove_claude_model_btn.clicked.connect(lambda: self.remove_model_from_list(self.claude_models_list))
        self.add_gpt_model_btn.clicked.connect(lambda: self.add_model_to_list(self.gpt_models_list, "GPT"))
        self.remove_gpt_model_btn.clicked.connect(lambda: self.remove_model_from_list(self.gpt_models_list))


        # --- 초기 설정값 로드 ---
        self.load_config_settings()
        if self.mw.current_project_folder:
            self.load_gitignore()

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

            # 사용 가능 모델 목록 로드
            self.gemini_models_list.clear(); self.gemini_models_list.addItems(self.settings.gemini_available_models or [])
            self.claude_models_list.clear(); self.claude_models_list.addItems(self.settings.claude_available_models or [])
            self.gpt_models_list.clear(); self.gpt_models_list.addItems(self.settings.gpt_available_models or [])

            # Set<str> -> str (UI 표시용)
            self.allowed_extensions_edit.setText(", ".join(sorted(list(self.settings.allowed_extensions or set()))))
            # List<str> -> str (UI 표시용)
            self.excluded_dirs_edit.setPlainText("\n".join(sorted(self.settings.excluded_dirs or [])))
            self.default_ignore_list_edit.setPlainText("\n".join(sorted(self.settings.default_ignore_list or [])))

            # Gemini 파라미터 로드
            self.gemini_temp_edit.setText(str(self.settings.gemini_temperature))
            self.gemini_thinking_checkbox.setChecked(self.settings.gemini_enable_thinking)
            self.gemini_budget_edit.setText(str(self.settings.gemini_thinking_budget))
            self.gemini_search_checkbox.setChecked(self.settings.gemini_enable_search)

        except Exception as e:
            QMessageBox.critical(self, "로드 오류", f"설정을 로드하는 중 오류 발생:\n{e}")

    def browse_default_prompt(self):
        """Opens a file dialog to select the default system prompt and updates the line edit."""
        selected_path = select_default_system_prompt(self.config_service, self)
        if selected_path is not None: # Allow empty path selection to clear
            self.default_prompt_path_edit.setText(selected_path)

    def add_model_to_list(self, list_widget: QListWidget, model_type: str):
        """리스트 위젯에 새 모델 이름을 추가합니다."""
        model_name, ok = QInputDialog.getText(self, f"{model_type} 모델 추가", "추가할 모델 이름을 입력하세요:")
        if ok and model_name and model_name.strip():
            name_stripped = model_name.strip()
            # 중복 체크
            items = [list_widget.item(i).text() for i in range(list_widget.count())]
            if name_stripped in items:
                QMessageBox.warning(self, "중복", f"'{name_stripped}' 모델이 이미 목록에 있습니다.")
                return
            list_widget.addItem(name_stripped)
        elif ok:
            QMessageBox.warning(self, "입력 오류", "모델 이름은 비워둘 수 없습니다.")

    def remove_model_from_list(self, list_widget: QListWidget):
        """리스트 위젯에서 선택된 모델 이름을 제거합니다."""
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "제거할 모델을 목록에서 선택하세요.")
            return
        for item in selected_items:
            list_widget.takeItem(list_widget.row(item))


    def save_config_settings(self):
        """UI에서 설정값을 읽어 ConfigSettings 모델을 업데이트하고 DB에 저장합니다."""
        if not self.settings:
            QMessageBox.critical(self, "오류", "설정 객체가 로드되지 않아 저장할 수 없습니다.")
            return

        try:
            # --- UI에서 값 읽기 ---
            default_prompt = self.default_prompt_path_edit.text().strip()
            gemini_model = self.gemini_default_model_edit.text().strip()
            claude_model = self.claude_default_model_edit.text().strip()
            gpt_model = self.gpt_default_model_edit.text().strip()

            # 사용 가능 모델 목록 읽기
            gemini_available = [self.gemini_models_list.item(i).text() for i in range(self.gemini_models_list.count())]
            claude_available = [self.claude_models_list.item(i).text() for i in range(self.claude_models_list.count())]
            gpt_available = [self.gpt_models_list.item(i).text() for i in range(self.gpt_models_list.count())]

            # 확장자: 쉼표 또는 공백으로 구분된 문자열 -> Set[str]
            allowed_ext_str = self.allowed_extensions_edit.text().strip()
            allowed_extensions = {ext.strip() for ext in allowed_ext_str.replace(',', ' ').split() if ext.strip()}

            # 제외 목록: 줄바꿈으로 구분된 문자열 -> List[str]
            excluded_dirs = [line.strip() for line in self.excluded_dirs_edit.toPlainText().splitlines() if line.strip()]
            default_ignore = [line.strip() for line in self.default_ignore_list_edit.toPlainText().splitlines() if line.strip()]

            # Gemini 파라미터
            temp_str = self.gemini_temp_edit.text().strip()
            gemini_temp = float(temp_str) if temp_str else 0.0
            gemini_thinking = self.gemini_thinking_checkbox.isChecked()
            budget_str = self.gemini_budget_edit.text().strip()
            gemini_budget = int(budget_str) if budget_str else 0
            gemini_search = self.gemini_search_checkbox.isChecked()

            # --- 업데이트할 데이터 준비 ---
            # 기존 settings 객체를 복사하여 업데이트 (API 키는 유지)
            update_data = self.settings.model_copy(deep=True)
            update_data.default_system_prompt = default_prompt if default_prompt else None
            update_data.gemini_default_model = gemini_model
            update_data.claude_default_model = claude_model
            update_data.gpt_default_model = gpt_model
            update_data.allowed_extensions = allowed_extensions
            update_data.excluded_dirs = set(excluded_dirs) # Pydantic 모델은 Set을 기대
            update_data.default_ignore_list = default_ignore
            # 사용 가능한 모델 목록 업데이트
            update_data.gemini_available_models = gemini_available
            update_data.claude_available_models = claude_available
            update_data.gpt_available_models = gpt_available
            update_data.gemini_temperature = gemini_temp
            update_data.gemini_enable_thinking = gemini_thinking
            update_data.gemini_thinking_budget = gemini_budget
            update_data.gemini_enable_search = gemini_search

            # API 키는 여기서 업데이트하지 않음 (읽기 전용 해제만 함)
            # update_data.gemini_api_key = self.gemini_api_key_edit.text().strip()
            # update_data.anthropic_api_key = self.anthropic_api_key_edit.text().strip()

            # --- Pydantic 유효성 검사 ---
            validated_settings = ConfigSettings(**update_data.model_dump())

            # --- DB 저장 ---
            if self.config_service.update_settings(validated_settings):
                QMessageBox.information(self, "성공", "설정이 성공적으로 저장되었습니다.")
                # MainWindow의 관련 UI 업데이트 트리거 (예: 기본 모델 콤보박스)
                self.mw.main_controller.on_llm_selected() # LLM 콤보박스 및 모델 업데이트
                self.mw.load_gemini_settings_to_ui() # Gemini 파라미터 UI 업데이트
                self.mw.file_tree_controller.load_gitignore_settings() # 필터 업데이트
                self.accept() # 다이얼로그 닫기
            else:
                QMessageBox.critical(self, "저장 실패", "설정을 데이터베이스에 저장하는 중 오류가 발생했습니다.")

        except ValidationError as e:
            QMessageBox.warning(self, "입력 오류", f"설정 값 유효성 검사 실패:\n{e}")
        except ValueError as e:
             QMessageBox.warning(self, "입력 오류", f"숫자 필드(온도, 예산)에 유효한 숫자를 입력하세요.\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 중 예기치 않은 오류 발생:\n{e}")


    def load_gitignore(self):
        """현재 프로젝트 폴더의 .gitignore 파일을 로드하여 편집기에 표시합니다."""
        if not self.mw.current_project_folder:
            self.gitignore_edit.setPlainText("")
            self.gitignore_edit.setEnabled(False)
            return

        self.gitignore_edit.setEnabled(True)
        gitignore_path = os.path.join(self.mw.current_project_folder, ".gitignore")
        content = ""
        try:
            if os.path.isfile(gitignore_path):
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.gitignore_edit.setPlainText(content)
            else:
                self.gitignore_edit.setPlainText("# .gitignore 파일 없음")
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
            # MainWindow의 파일 트리 필터 업데이트
            if hasattr(self.mw, 'file_tree_controller'):
                self.mw.file_tree_controller.load_gitignore_settings()
        except Exception as e:
            QMessageBox.critical(self, "오류", f".gitignore 파일을 저장하는 중 오류 발생:\n{e}")
            
