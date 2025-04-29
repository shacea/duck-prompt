import os
import datetime # datetime 추가
from PyQt6.QtWidgets import ( # PyQt5 -> PyQt6
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QLabel, QPlainTextEdit, QFileDialog, QMessageBox, QGroupBox, QHBoxLayout, QComboBox,
    QCheckBox, QApplication, QListWidget, QListWidgetItem, QAbstractItemView, QInputDialog, QWidget,
    QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt # PyQt5 -> PyQt6
from PyQt6.QtGui import QColor, QIcon, QIntValidator, QBrush # PyQt5 -> PyQt6, QIntValidator 추가, QBrush 추가
from typing import Optional, Set, List, Dict, Any, Tuple # Dict, Any, Tuple 추가
from pydantic import ValidationError
import logging # 로깅 추가

# 서비스 및 컨트롤러 함수 import
from core.services.config_service import ConfigService
from core.pydantic_models.config_settings import ConfigSettings
from ui.controllers.system_prompt_controller import select_default_system_prompt
# MainWindow 타입 힌트 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow
    from core.services.db_service import DbService # DbService 타입 힌트

logger = logging.getLogger(__name__) # 로거 설정

# 파스텔 그린 색상 정의
PASTEL_GREEN = QColor(152, 251, 152) # 연한 녹색 (RGB)
# 파스텔 블루 색상 정의 (사용자 선택 강조용)
PASTEL_BLUE = QColor(173, 216, 230) # 연한 파란색 (Light Blue)
# 파스텔 퍼플 색상 정의 (자동 선택 예정 강조용)
PASTEL_PURPLE = QColor(221, 160, 221) # 연보라색 (Plum)

# --- 모델 추가 다이얼로그 ---
class AddModelDialog(QDialog):
    """모델 이름, RPM, Daily Limit을 입력받는 다이얼로그."""
    def __init__(self, model_type: str, existing_models: List[str], parent=None):
        super().__init__(parent)
        self.model_type = model_type
        self.existing_models = existing_models
        self.setWindowTitle(f"{model_type} 모델 추가")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.model_name_edit = QLineEdit()
        self.rpm_limit_edit = QLineEdit()
        self.daily_limit_edit = QLineEdit()

        # 숫자만 입력 가능하도록 Validator 설정
        self.rpm_limit_edit.setValidator(QIntValidator(0, 999999)) # 0 이상 정수
        self.daily_limit_edit.setValidator(QIntValidator(0, 9999999)) # 0 이상 정수

        form_layout.addRow("모델 이름:", self.model_name_edit)
        form_layout.addRow("RPM Limit (분당 요청 수):", self.rpm_limit_edit)
        form_layout.addRow("Daily Limit (하루 요청 수):", self.daily_limit_edit)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        """입력값 유효성 검사 후 accept."""
        model_name = self.model_name_edit.text().strip()
        rpm_limit_str = self.rpm_limit_edit.text().strip()
        daily_limit_str = self.daily_limit_edit.text().strip()

        if not model_name:
            QMessageBox.warning(self, "입력 오류", "모델 이름을 입력해야 합니다.")
            return
        if model_name in self.existing_models:
            QMessageBox.warning(self, "입력 오류", f"'{model_name}' 모델이 이미 목록에 존재합니다.")
            return
        if not rpm_limit_str:
            QMessageBox.warning(self, "입력 오류", "RPM Limit을 입력해야 합니다.")
            return
        if not daily_limit_str:
            QMessageBox.warning(self, "입력 오류", "Daily Limit을 입력해야 합니다.")
            return

        try:
            int(rpm_limit_str)
            int(daily_limit_str)
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "RPM 및 Daily Limit은 숫자로 입력해야 합니다.")
            return

        self.accept() # 유효성 검사 통과 시 accept

    def get_model_data(self) -> Optional[Tuple[str, int, int]]:
        """입력된 모델 데이터 반환."""
        if self.result() == QDialog.DialogCode.Accepted: # QDialog.Accepted -> QDialog.DialogCode.Accepted
            model_name = self.model_name_edit.text().strip()
            rpm_limit = int(self.rpm_limit_edit.text().strip())
            daily_limit = int(self.daily_limit_edit.text().strip())
            return model_name, rpm_limit, daily_limit
        return None

# --- SettingsDialog ---
class SettingsDialog(QDialog):
    """
    환경 설정을 표시하고 수정하는 다이얼로그 창.
    DB에서 로드된 설정을 보여주고, 수정 후 DB에 저장합니다.
    .gitignore 파일 편집/저장 기능도 유지합니다.
    API 키 필드는 일반 텍스트로 표시됩니다. (저장 로직은 별도 관리)
    사용 가능 LLM 모델 목록 및 API 키를 관리하는 기능이 추가되었습니다.
    API 키 목록에 잔여 사용량 정보를 표시하고, 사용자가 사용할 키를 선택할 수 있습니다.
    사용 가능 LLM 모델 목록에서 클릭하여 기본 모델을 지정할 수 있습니다.
    사용자가 키를 선택하지 않았을 때 자동으로 선택될 키를 표시합니다.
    """
    PASTEL_GREEN = PASTEL_GREEN # 클래스 변수로도 정의
    PASTEL_BLUE = PASTEL_BLUE # 클래스 변수로도 정의
    PASTEL_PURPLE = PASTEL_PURPLE # 클래스 변수로도 정의

    def __init__(self, main_window: 'MainWindow', parent=None):
        super().__init__(parent)
        self.mw = main_window # MainWindow 참조
        self.config_service = main_window.config_service
        self.db_service: 'DbService' = main_window.db_service # DbService 참조 추가
        self.settings: Optional[ConfigSettings] = None # Load in load_config_settings

        self.setWindowTitle("환경 설정") # Title updated
        self.setMinimumWidth(800) # 너비 증가
        self.setMinimumHeight(750) # 높이 증가 (내용 표시 공간 확보)

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

        # --- API 키 관리 (개선) ---
        self.api_key_management_group = QGroupBox("API 키 관리")
        api_key_management_layout = QVBoxLayout()

        # API 키 목록 표시 및 새로고침 버튼
        api_list_layout = QHBoxLayout()
        self.api_keys_list = QListWidget()
        self.api_keys_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # QAbstractItemView.SingleSelection -> QAbstractItemView.SelectionMode.SingleSelection
        self.api_keys_list.setMinimumHeight(100) # 최소 높이 증가
        self.api_keys_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # QSizePolicy.Expanding -> QSizePolicy.Policy.Expanding
        self.refresh_api_usage_btn = QPushButton("🔄") # 새로고침 버튼 추가
        self.refresh_api_usage_btn.setToolTip("API 키 사용량 새로고침")
        self.refresh_api_usage_btn.setFixedWidth(30) # 버튼 크기 고정
        api_list_layout.addWidget(self.api_keys_list)
        api_list_layout.addWidget(self.refresh_api_usage_btn)

        # 라벨 업데이트: 아이콘 설명 추가 (✨ 추가)
        self.api_key_label = QLabel(
            "등록된 API 키 (🔵: 사용자 선택됨, 🟢: 마지막 사용, ✨: 자동 선택 예정, 🟡: 활성, 🔴: 비활성 / 잔여량은 기본 Gemini 모델 기준):"
        )
        api_key_management_layout.addWidget(self.api_key_label)
        api_key_management_layout.addLayout(api_list_layout) # 목록과 새로고침 버튼 레이아웃 추가

        # API 키 추가/제거/선택 버튼
        api_key_buttons_layout = QHBoxLayout()
        self.add_api_key_btn = QPushButton("➕ 새 API 키 추가")
        self.remove_api_key_btn = QPushButton("➖ 선택한 키 제거")
        self.set_selected_key_btn = QPushButton("✅ 선택한 키 사용") # 사용 키 선택 버튼 추가
        api_key_buttons_layout.addWidget(self.add_api_key_btn)
        api_key_buttons_layout.addWidget(self.remove_api_key_btn)
        api_key_buttons_layout.addWidget(self.set_selected_key_btn) # 버튼 레이아웃에 추가
        api_key_buttons_layout.addStretch()
        api_key_management_layout.addLayout(api_key_buttons_layout)

        self.api_key_management_group.setLayout(api_key_management_layout)


        # 사용 가능 LLM 모델 관리 (위치 이동됨)
        self.available_models_group = QGroupBox("사용 가능 LLM 모델 목록 관리 (클릭하여 기본 모델 지정)") # 그룹 제목 수정
        available_models_main_layout = QHBoxLayout()

        # Gemini 모델 목록
        gemini_model_widget = QWidget()
        gemini_model_layout = QVBoxLayout(gemini_model_widget)
        gemini_model_layout.addWidget(QLabel("Gemini 모델:"))
        self.gemini_models_list = QListWidget()
        self.gemini_models_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # QAbstractItemView.SingleSelection -> QAbstractItemView.SelectionMode.SingleSelection
        self.gemini_models_list.setMinimumHeight(100) # 최소 높이 증가
        self.gemini_models_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # QSizePolicy.Expanding -> QSizePolicy.Policy.Expanding
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
        self.claude_models_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # QAbstractItemView.SingleSelection -> QAbstractItemView.SelectionMode.SingleSelection
        self.claude_models_list.setMinimumHeight(100) # 최소 높이 증가
        self.claude_models_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # QSizePolicy.Expanding -> QSizePolicy.Policy.Expanding
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
        self.gpt_models_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # QAbstractItemView.SingleSelection -> QAbstractItemView.SelectionMode.SingleSelection
        self.gpt_models_list.setMinimumHeight(100) # 최소 높이 증가
        self.gpt_models_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # QSizePolicy.Expanding -> QSizePolicy.Policy.Expanding
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
        self.excluded_dirs_edit.setMinimumHeight(80) # 최소 높이 설정
        self.excluded_dirs_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # QSizePolicy.Expanding -> QSizePolicy.Policy.Expanding
        self.default_ignore_list_edit = QPlainTextEdit()
        self.default_ignore_list_edit.setPlaceholderText("한 줄에 하나씩 입력 (예: .git/, __pycache__/)")
        self.default_ignore_list_edit.setMinimumHeight(80) # 최소 높이 설정
        self.default_ignore_list_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # QSizePolicy.Expanding -> QSizePolicy.Policy.Expanding
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
        # 위젯 추가 순서 변경: Temp -> Search -> Thinking -> Budget
        gemini_layout.addRow("Temperature (0.0 ~ 2.0):", self.gemini_temp_edit)
        gemini_layout.addRow("Enable Search:", self.gemini_search_checkbox) # Search 이동
        gemini_layout.addRow("Enable Thinking:", self.gemini_thinking_checkbox)
        gemini_layout.addRow("Thinking Budget:", self.gemini_budget_edit)
        self.gemini_group.setLayout(gemini_layout)

        # .gitignore 편집
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
        self.gitignore_edit.setMinimumHeight(120) # 최소 높이 설정
        self.gitignore_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # QSizePolicy.Expanding -> QSizePolicy.Policy.Expanding
        gitignore_layout.addLayout(gitignore_button_layout)
        gitignore_layout.addWidget(self.gitignore_edit)
        self.gitignore_group.setLayout(gitignore_layout)
        self.gitignore_group.setEnabled(bool(self.mw.current_project_folder))

        # 버튼 박스 (Save and Close)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Close) # QDialogButtonBox.Save -> QDialogButtonBox.StandardButton.Save
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText("설정 저장") # QDialogButtonBox.Save -> QDialogButtonBox.StandardButton.Save
        self.button_box.button(QDialogButtonBox.StandardButton.Close).setText("닫기") # QDialogButtonBox.Close -> QDialogButtonBox.StandardButton.Close

        # --- 레이아웃 설정 (2단 컬럼 스플리터 사용) ---
        main_layout = QVBoxLayout(self)

        # 메인 수평 스플리터 생성
        main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal) # Qt.Horizontal -> Qt.Orientation.Horizontal

        # 왼쪽 컬럼 위젯 및 레이아웃 생성
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)

        # 왼쪽 컬럼에 그룹 추가 (순서 변경)
        left_layout.addWidget(self.default_prompt_group)
        left_layout.addWidget(self.available_models_group) # 사용 가능 모델 목록 그룹을 왼쪽으로 이동
        left_layout.addWidget(self.api_key_management_group)
        left_layout.addWidget(self.gemini_group) # Gemini 파라미터 왼쪽으로 이동
        left_layout.addStretch(1) # 위젯들을 위로 밀기

        # 오른쪽 컬럼 위젯 및 레이아웃 생성
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)

        # 오른쪽 컬럼에 그룹 추가
        right_layout.addWidget(self.filtering_group)
        right_layout.addWidget(self.gitignore_group) # gitignore 오른쪽으로 이동
        right_layout.addStretch(1) # 위젯들을 위로 밀기

        # 수평 스플리터에 왼쪽/오른쪽 컬럼 위젯 추가
        main_horizontal_splitter.addWidget(left_widget)
        main_horizontal_splitter.addWidget(right_widget)

        # 수평 스플리터 초기 크기 설정 (예: 1:1 비율)
        initial_width = self.width() # 현재 다이얼로그 너비 사용
        main_horizontal_splitter.setSizes([initial_width // 2, initial_width // 2])

        # 메인 레이아웃에 수평 스플리터와 버튼 박스 추가
        main_layout.addWidget(main_horizontal_splitter, 1) # 스플리터가 남는 공간 차지
        main_layout.addWidget(self.button_box)

        # --- 시그널 연결 ---
        self.browse_prompt_button.clicked.connect(self.browse_default_prompt)
        self.load_gitignore_button.clicked.connect(self.load_gitignore)
        self.save_gitignore_button.clicked.connect(self.save_gitignore)
        self.button_box.accepted.connect(self.save_config_settings)
        self.button_box.rejected.connect(self.reject)

        # API 키 관리 버튼 시그널
        self.add_api_key_btn.clicked.connect(self.add_api_key)
        self.remove_api_key_btn.clicked.connect(self.remove_api_key)
        self.refresh_api_usage_btn.clicked.connect(self.load_api_keys_list) # 새로고침 버튼 연결
        self.api_keys_list.itemDoubleClicked.connect(self.show_api_key_value) # 더블클릭 시그널 연결
        self.set_selected_key_btn.clicked.connect(self.set_selected_api_key) # 키 선택 버튼 연결

        # 사용 가능 모델 추가/제거 버튼 시그널 연결
        self.add_gemini_model_btn.clicked.connect(lambda: self.add_model_to_list(self.gemini_models_list, "google")) # Provider 이름 전달
        self.remove_gemini_model_btn.clicked.connect(lambda: self.remove_model_from_list(self.gemini_models_list))
        self.add_claude_model_btn.clicked.connect(lambda: self.add_model_to_list(self.claude_models_list, "anthropic")) # Provider 이름 전달
        self.remove_claude_model_btn.clicked.connect(lambda: self.remove_model_from_list(self.claude_models_list))
        self.add_gpt_model_btn.clicked.connect(lambda: self.add_model_to_list(self.gpt_models_list, "openai")) # Provider 이름 전달
        self.remove_gpt_model_btn.clicked.connect(lambda: self.remove_model_from_list(self.gpt_models_list))

        # 사용 가능 모델 리스트 클릭 시그널 연결 (기본 모델 지정용)
        self.gemini_models_list.itemClicked.connect(lambda item: self.handle_model_click(item, self.gemini_models_list, 'gemini'))
        self.claude_models_list.itemClicked.connect(lambda item: self.handle_model_click(item, self.claude_models_list, 'claude'))
        self.gpt_models_list.itemClicked.connect(lambda item: self.handle_model_click(item, self.gpt_models_list, 'gpt'))

        # --- 초기 설정값 로드 ---
        self.load_config_settings()
        self.load_api_keys_list() # API 키 목록 로드
        if self.mw.current_project_folder:
            self.load_gitignore()

    def load_config_settings(self):
        """UI 위젯에 현재 DB 설정값을 로드하고 기본 모델을 하이라이트합니다."""
        try:
            # ConfigService를 통해 최신 설정 로드
            self.settings = self.config_service.get_settings()
            if not self.settings:
                 QMessageBox.critical(self, "오류", "DB에서 설정을 로드하지 못했습니다.")
                 return

            logger.info("Loading config settings into SettingsDialog UI...")

            # UI 위젯 업데이트 (시그널 차단 불필요, 로드 시점에는 사용자 입력 없음)
            self.default_prompt_path_edit.setText(self.settings.default_system_prompt or "")

            # 사용 가능 모델 목록 로드 및 기본 모델 하이라이트
            self._populate_and_highlight_model_list(self.gemini_models_list, self.settings.gemini_available_models, self.settings.gemini_default_model)
            self._populate_and_highlight_model_list(self.claude_models_list, self.settings.claude_available_models, self.settings.claude_default_model)
            self._populate_and_highlight_model_list(self.gpt_models_list, self.settings.gpt_available_models, self.settings.gpt_default_model)

            self.allowed_extensions_edit.setText(", ".join(sorted(list(self.settings.allowed_extensions or set()))))
            self.excluded_dirs_edit.setPlainText("\n".join(sorted(self.settings.excluded_dirs or [])))
            self.default_ignore_list_edit.setPlainText("\n".join(sorted(self.settings.default_ignore_list or [])))

            self.gemini_temp_edit.setText(str(self.settings.gemini_temperature))
            self.gemini_thinking_checkbox.setChecked(self.settings.gemini_enable_thinking)
            self.gemini_budget_edit.setText(str(self.settings.gemini_thinking_budget))
            self.gemini_search_checkbox.setChecked(self.settings.gemini_enable_search)

            logger.info("SettingsDialog UI updated with loaded config.")

        except Exception as e:
            QMessageBox.critical(self, "로드 오류", f"설정을 로드하는 중 오류 발생:\n{e}")
            logger.exception("Error loading config settings into SettingsDialog UI")

    def _populate_and_highlight_model_list(self, list_widget: QListWidget, models: List[str], default_model: str):
        """Helper function to populate a model list and highlight the default."""
        list_widget.clear()
        list_widget.addItems(models or [])
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.text() == default_model:
                item.setBackground(self.PASTEL_GREEN) # 기본 모델 하이라이트
            else:
                # 명시적으로 기본 배경색 설정 (이전 하이라이트 제거)
                # 기본 배경색을 투명하게 설정하여 시스템 테마 따르도록 수정
                item.setBackground(QBrush(Qt.GlobalColor.transparent)) # Qt.white -> Qt.transparent

    def handle_model_click(self, clicked_item: QListWidgetItem, list_widget: QListWidget, model_type: str):
        """Handles clicks on model list items to set the default model."""
        if not self.settings: return
        new_default_model = clicked_item.text()
        old_default_model = ""

        # Update the settings object and get the old default model
        if model_type == 'gemini':
            old_default_model = self.settings.gemini_default_model
            self.settings.gemini_default_model = new_default_model
        elif model_type == 'claude':
            old_default_model = self.settings.claude_default_model
            self.settings.claude_default_model = new_default_model
        elif model_type == 'gpt':
            old_default_model = self.settings.gpt_default_model
            self.settings.gpt_default_model = new_default_model
        else:
            return

        logger.info(f"Set default {model_type} model to: {new_default_model}")

        # Update highlighting in the list widget
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            # 이전 기본 모델 하이라이트 제거
            if item.text() == old_default_model:
                 item.setBackground(QBrush(Qt.GlobalColor.transparent)) # Qt.white -> Qt.transparent
            # 새 기본 모델 하이라이트 적용
            if item.text() == new_default_model:
                item.setBackground(self.PASTEL_GREEN)

    def load_api_keys_list(self):
        """DB에서 API 키 목록을 로드하여 리스트 위젯에 표시하고 상태(사용자 선택, 마지막 사용, 자동 선택 예정 등)를 강조합니다."""
        self.api_keys_list.clear()
        try:
            all_keys = self.db_service.list_api_keys() # 모든 키 정보 가져오기 (사용량 포함)
            if not all_keys:
                self.api_keys_list.addItem("등록된 API 키가 없습니다.")
                self.api_keys_list.setEnabled(False)
                return

            self.api_keys_list.setEnabled(True)

            user_selected_key_id = self.config_service.get_user_selected_gemini_key_id()
            last_used_key_id = self.config_service.get_last_used_gemini_key_id()
            logger.info(f"Current User Selected Key ID: {user_selected_key_id}, Last Used Key ID: {last_used_key_id}")

            default_gemini_model = self.config_service.get_default_model_name('Gemini')
            # Rate limit info is fetched inside the loop now if needed

            # --- 자동 선택 예정 키 식별 (개선) ---
            auto_select_candidate_id: Optional[int] = None
            if user_selected_key_id is None:
                logger.info("Identifying auto-select candidate key...")
                candidate_keys = []
                # 활성 Google 키 필터링
                active_google_keys_info = [k for k in all_keys if k.get('provider') == 'google' and k.get('is_active')]

                for key_info in active_google_keys_info:
                    key_id = key_info['id']
                    # Rate Limit 체크
                    is_limited, reason = self.db_service.is_key_rate_limited(key_id, default_gemini_model)
                    if not is_limited:
                        # Rate Limit 안 걸린 키만 후보로 추가
                        # 유효 일일 사용량 계산 (기존 로직 유지)
                        now = datetime.datetime.now(datetime.timezone.utc)
                        current_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        raw_calls_day = key_info.get('calls_this_day', 0)
                        day_start = key_info.get('day_start_timestamp')
                        if day_start and day_start.tzinfo is None: # 타임존 정보 없으면 UTC로 간주
                             day_start = day_start.replace(tzinfo=datetime.timezone.utc)
                        effective_daily_calls = raw_calls_day if day_start and day_start >= current_day_start else 0
                        candidate_keys.append({'id': key_id, 'effective_calls': effective_daily_calls})
                        logger.debug(f"  Candidate Key ID: {key_id} (Not Rate Limited, Effective Daily Calls: {effective_daily_calls})")
                    else:
                        logger.debug(f"  Skipping Key ID: {key_id} (Rate Limited: {reason})")

                # 유효 일일 사용량 기준 정렬
                candidate_keys.sort(key=lambda x: x['effective_calls'])

                # 가장 사용량 적은 키가 자동 선택 후보
                if candidate_keys:
                    auto_select_candidate_id = candidate_keys[0]['id']
                    logger.info(f"Auto-select candidate key ID identified: {auto_select_candidate_id} (Effective Daily Calls: {candidate_keys[0]['effective_calls']})")
                else:
                    logger.warning("No suitable auto-select candidate key found (all active keys might be rate-limited).")
            # -----------------------------

            # --- 키 목록 UI 업데이트 ---
            rate_limit_info = self.db_service.get_model_rate_limit(default_gemini_model) # Get rate limit info once
            rpm_limit = rate_limit_info.get('rpm_limit') if rate_limit_info else None
            daily_limit = rate_limit_info.get('daily_limit') if rate_limit_info else None
            now = datetime.datetime.now(datetime.timezone.utc) # Get current time once

            for key_info in all_keys:
                key_id = key_info['id']
                provider = key_info.get('provider', 'N/A')
                description = key_info.get('description', '')
                api_key_value = key_info.get('api_key', '')
                api_key_display = api_key_value[:4] + "..." + api_key_value[-4:] if len(api_key_value) > 8 else api_key_value[:4] + "..."
                is_active = key_info.get('is_active', False)

                status_icon = ""
                item_color = QBrush(Qt.GlobalColor.transparent) # 기본 배경 투명
                display_text = f"[{provider.upper()}] {description or api_key_display}"
                extra_info = "" # 상태 표시용 추가 텍스트
                tooltip_status = "" # 툴팁용 상태 문자열

                # 상태 결정 (우선순위: 사용자 선택 > 자동 선택 예정 > 마지막 사용 > 활성 > 비활성)
                if provider == 'google' and key_id == user_selected_key_id:
                    status_icon = "🔵" # 사용자 선택
                    item_color = QBrush(self.PASTEL_BLUE) # 연한 파란색 배경
                    extra_info = " (사용자 선택)"
                    tooltip_status = "User Selected"
                elif provider == 'google' and key_id == auto_select_candidate_id:
                    status_icon = "✨" # 자동 선택 예정
                    item_color = QBrush(self.PASTEL_PURPLE) # 연보라색 배경
                    extra_info = " (자동 선택 예정)"
                    tooltip_status = "Auto-Select Candidate"
                elif provider == 'google' and key_id == last_used_key_id:
                    status_icon = "🟢" # 마지막 사용
                    item_color = QBrush(self.PASTEL_GREEN) # 연한 녹색 배경
                    extra_info = " (마지막 사용)"
                    tooltip_status = "Last Used"
                elif is_active:
                    status_icon = "🟡" # 활성
                    item_color = QBrush(QColor("lightyellow")) # 연한 노란색 배경
                    tooltip_status = "Active"
                else:
                    status_icon = "🔴" # 비활성
                    item_color = QBrush(QColor("lightcoral")) # 연한 산호색 배경
                    tooltip_status = "Inactive"

                display_text = f"{status_icon}{display_text}{extra_info}"

                # 잔여 사용량 계산 (Gemini 키)
                remaining_rpm_str, remaining_daily_str = "N/A", "N/A"
                tooltip_rpm, tooltip_daily = "N/A", "N/A"
                if provider == 'google' and rpm_limit is not None and daily_limit is not None:
                    calls_this_minute = key_info.get('calls_this_minute', 0)
                    minute_start = key_info.get('minute_start_timestamp')
                    calls_this_day = key_info.get('calls_this_day', 0)
                    day_start = key_info.get('day_start_timestamp')
                    if minute_start and minute_start.tzinfo is None: minute_start = minute_start.replace(tzinfo=datetime.timezone.utc)
                    if day_start and day_start.tzinfo is None: day_start = day_start.replace(tzinfo=datetime.timezone.utc)

                    current_minute_calls = calls_this_minute
                    # 분 시작 시간이 있고, 현재 시간이 분 시작 시간 + 1분보다 크거나 같으면 0으로 리셋
                    if minute_start and now >= minute_start + datetime.timedelta(minutes=1):
                        current_minute_calls = 0
                    remaining_rpm = max(0, rpm_limit - current_minute_calls)
                    remaining_rpm_str = f"{remaining_rpm}/{rpm_limit}"
                    tooltip_rpm = f"{remaining_rpm} / {rpm_limit} (Used: {current_minute_calls})"

                    current_day_calls = calls_this_day
                    # 일 시작 시간이 있고, 현재 시간이 일 시작 시간 + 1일보다 크거나 같으면 0으로 리셋
                    if day_start and now >= day_start + datetime.timedelta(days=1):
                        current_day_calls = 0
                    remaining_daily = max(0, daily_limit - current_day_calls)
                    remaining_daily_str = f"{remaining_daily}/{daily_limit}"
                    tooltip_daily = f"{remaining_daily} / {daily_limit} (Used: {current_day_calls})"

                    display_text += f" (RPM: {remaining_rpm_str}, Daily: {remaining_daily_str})"
                elif provider == 'google':
                    logger.warning(f"Rate limit info not found for model '{default_gemini_model}'. Cannot calculate remaining usage for key ID {key_id}.")

                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, key_id) # 키 ID 저장
                item.setData(Qt.ItemDataRole.UserRole + 1, api_key_value) # 실제 키 값 저장
                item.setData(Qt.ItemDataRole.UserRole + 2, provider) # 프로바이더 저장
                item.setBackground(item_color) # 배경색 설정 (QBrush 사용)

                # 툴팁 업데이트
                tooltip_text = (
                    f"ID: {key_id}\nProvider: {provider}\nKey: {api_key_display}\nStatus: {tooltip_status}"
                )
                if provider == 'google':
                     tooltip_text += f"\nRemaining RPM (vs {default_gemini_model}): {tooltip_rpm}\nRemaining Daily (vs {default_gemini_model}): {tooltip_daily}"
                item.setToolTip(tooltip_text)

                self.api_keys_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "API 키 로드 오류", f"API 키 목록을 불러오는 중 오류 발생:\n{e}")
            logger.exception("Error loading API keys list")
            self.api_keys_list.addItem("API 키 로드 오류")
            self.api_keys_list.setEnabled(False)


    def add_api_key(self):
        """새 API 키를 추가하는 다이얼로그를 띄우고 DB에 저장합니다."""
        provider, ok1 = QInputDialog.getItem(self, "API 키 추가", "Provider 선택:", ["google", "anthropic", "openai"], 0, False)
        if not ok1: return
        # QLineEdit.Password 대신 QLineEdit.Normal 사용
        api_key, ok2 = QInputDialog.getText(self, "API 키 추가", f"{provider} API 키 입력:", QLineEdit.EchoMode.Normal) # QLineEdit.Normal -> QLineEdit.EchoMode.Normal
        if not ok2 or not api_key.strip(): return
        description, ok3 = QInputDialog.getText(self, "API 키 추가", "설명 (선택 사항):", QLineEdit.EchoMode.Normal) # QLineEdit.Normal -> QLineEdit.EchoMode.Normal
        if not ok3: description = ""

        try:
            key_id = self.db_service.add_api_key(provider, api_key.strip(), description.strip())
            if key_id is not None:
                QMessageBox.information(self, "성공", "API 키가 성공적으로 추가되었습니다.")
                self.load_api_keys_list() # 목록 새로고침
            else:
                QMessageBox.warning(self, "실패", "API 키 추가 중 오류가 발생했습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"API 키 추가 중 예외 발생:\n{e}")

    def remove_api_key(self):
        """선택된 API 키를 DB에서 제거합니다."""
        selected_items = self.api_keys_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "제거할 API 키를 목록에서 선택하세요.")
            return

        item = selected_items[0]
        key_id = item.data(Qt.ItemDataRole.UserRole) # Qt.UserRole -> Qt.ItemDataRole.UserRole
        display_text = item.text()

        # 사용자 선택 키는 제거 불가
        user_selected_key_id = self.config_service.get_user_selected_gemini_key_id()
        if key_id == user_selected_key_id:
            QMessageBox.warning(self, "제거 불가", "현재 사용하도록 선택된 API 키는 제거할 수 없습니다.\n다른 키를 선택하거나 선택을 해제한 후 시도하세요.")
            return

        reply = QMessageBox.question(self, "삭제 확인", f"정말로 API 키를 삭제하시겠습니까?\n({display_text})",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) # QMessageBox.Yes/No -> QMessageBox.StandardButton.Yes/No
        if reply != QMessageBox.StandardButton.Yes: return # QMessageBox.Yes -> QMessageBox.StandardButton.Yes

        try:
            success = self.db_service.delete_api_key(key_id)
            if success:
                QMessageBox.information(self, "성공", "API 키가 성공적으로 제거되었습니다.")
                self.load_api_keys_list() # 목록 새로고침
            else:
                QMessageBox.warning(self, "실패", "API 키 제거 중 오류가 발생했습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"API 키 제거 중 예외 발생:\n{e}")

    def show_api_key_value(self, item: QListWidgetItem):
        """더블클릭된 API 키의 실제 값을 메시지 박스로 보여줍니다."""
        api_key_value = item.data(Qt.ItemDataRole.UserRole + 1) # Qt.UserRole -> Qt.ItemDataRole.UserRole
        if api_key_value:
            QMessageBox.information(self, "API 키 값 확인",
                                    f"선택한 API 키 값:\n\n{api_key_value}\n\n"
                                    "주의: 이 키는 민감한 정보이므로 안전하게 관리하세요.",
                                    QMessageBox.StandardButton.Ok) # QMessageBox.Ok -> QMessageBox.StandardButton.Ok
        else:
            QMessageBox.warning(self, "오류", "API 키 값을 가져올 수 없습니다.")

    def set_selected_api_key(self):
        """선택된 API 키를 사용자가 사용할 키로 설정합니다 (Gemini 키만 해당)."""
        selected_items = self.api_keys_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "사용할 API 키를 목록에서 선택하세요.")
            return

        item = selected_items[0]
        key_id = item.data(Qt.ItemDataRole.UserRole)
        provider = item.data(Qt.ItemDataRole.UserRole + 2)

        if provider != 'google':
            QMessageBox.information(self, "정보", "Google (Gemini) API 키만 사용하도록 선택할 수 있습니다.")
            return

        # 비활성 키는 선택 불가
        if "🔴" in item.text():
             QMessageBox.warning(self, "선택 불가", "비활성화된 API 키는 사용할 수 없습니다.")
             return

        current_selected_id = self.config_service.get_user_selected_gemini_key_id()

        if key_id == current_selected_id:
            # 이미 선택된 키를 다시 선택하면 선택 해제
            self.config_service.set_user_selected_gemini_key(None)
            QMessageBox.information(self, "선택 해제", "API 키 선택이 해제되었습니다.\n이제 사용량이 가장 적은 키부터 자동으로 사용됩니다.")
        else:
            # 새 키 선택
            self.config_service.set_user_selected_gemini_key(key_id)
            QMessageBox.information(self, "키 선택 완료", f"API 키 ID {key_id}가 사용되도록 선택되었습니다.")

        # UI 업데이트를 위해 목록 다시 로드
        self.load_api_keys_list()


    def browse_default_prompt(self):
        """Opens a file dialog to select the default system prompt and updates the line edit."""
        selected_path = select_default_system_prompt(self.config_service, self)
        if selected_path is not None:
            self.default_prompt_path_edit.setText(selected_path)

    def add_model_to_list(self, list_widget: QListWidget, provider: str):
        """리스트 위젯에 새 모델 이름과 Rate Limit을 추가하고 DB에 저장합니다."""
        existing_models = [list_widget.item(i).text() for i in range(list_widget.count())]
        dialog = AddModelDialog(provider.capitalize(), existing_models, self)
        if dialog.exec() == QDialog.DialogCode.Accepted: # QDialog.Accepted -> QDialog.DialogCode.Accepted
            model_data = dialog.get_model_data()
            if model_data:
                model_name, rpm_limit, daily_limit = model_data
                try:
                    # DB에 Rate Limit 정보 저장
                    self.db_service.insert_or_update_rate_limit(
                        model_name=model_name,
                        provider=provider,
                        rpm_limit=rpm_limit,
                        daily_limit=daily_limit
                    )
                    # UI 리스트 위젯에 모델 이름 추가
                    list_widget.addItem(model_name)
                    QMessageBox.information(self, "성공", f"모델 '{model_name}' 및 Rate Limit 정보가 추가되었습니다.")
                except Exception as e:
                    QMessageBox.critical(self, "DB 오류", f"모델 Rate Limit 정보 저장 중 오류 발생:\n{e}")
                    logger.exception(f"Error saving rate limit for model {model_name}")

    def remove_model_from_list(self, list_widget: QListWidget):
        """리스트 위젯에서 선택된 모델 이름을 제거하고 DB에서도 Rate Limit 정보를 제거합니다."""
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "제거할 모델을 목록에서 선택하세요.")
            return

        model_to_remove = selected_items[0].text()
        is_default = False
        if list_widget == self.gemini_models_list and self.settings and model_to_remove == self.settings.gemini_default_model: is_default = True
        elif list_widget == self.claude_models_list and self.settings and model_to_remove == self.settings.claude_default_model: is_default = True
        elif list_widget == self.gpt_models_list and self.settings and model_to_remove == self.settings.gpt_default_model: is_default = True


        if is_default:
            QMessageBox.warning(self, "제거 불가", f"'{model_to_remove}' 모델은 현재 기본 모델로 지정되어 있어 제거할 수 없습니다.\n다른 모델을 기본으로 지정한 후 다시 시도하세요.")
            return

        # 기본 모델이 아니면 제거 진행
        reply = QMessageBox.question(self, "모델 제거 확인",
                                     f"정말로 '{model_to_remove}' 모델을 목록과 DB에서 제거하시겠습니까?\n(Rate Limit 정보도 함께 제거됩니다)",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # DB에서 Rate Limit 정보 제거 시도
            success_db = self.db_service.delete_rate_limit(model_name=model_to_remove)
            if success_db:
                logger.info(f"Successfully removed rate limit info for model '{model_to_remove}' from DB.")
                # DB 제거 성공 시 UI 목록에서도 제거
                for item in selected_items:
                    list_widget.takeItem(list_widget.row(item))
                QMessageBox.information(self, "성공", f"모델 '{model_to_remove}'이(가) 목록과 DB에서 제거되었습니다.")
            else:
                # DB 제거 실패 또는 해당 모델 정보 없음
                logger.warning(f"Failed to remove rate limit info for model '{model_to_remove}' from DB (or not found).")
                # UI 목록에서만 제거할지 여부 결정 (여기서는 DB 실패 시 UI도 유지)
                QMessageBox.warning(self, "DB 오류", f"DB에서 '{model_to_remove}' 모델의 Rate Limit 정보를 제거하는 데 실패했습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"모델 제거 중 예외 발생:\n{e}")
            logger.exception(f"Error removing model {model_to_remove}")


    def save_config_settings(self):
        """UI에서 설정값을 읽어 ConfigSettings 모델을 업데이트하고 DB에 저장합니다."""
        if not self.settings:
            QMessageBox.critical(self, "오류", "설정 객체가 로드되지 않아 저장할 수 없습니다.")
            return

        try:
            # --- UI에서 값 읽기 (기본 모델은 self.settings에서 직접 읽음) ---
            default_prompt = self.default_prompt_path_edit.text().strip()
            gemini_model = self.settings.gemini_default_model # 클릭 핸들러가 업데이트한 값 사용
            claude_model = self.settings.claude_default_model # 클릭 핸들러가 업데이트한 값 사용
            gpt_model = self.settings.gpt_default_model     # 클릭 핸들러가 업데이트한 값 사용

            gemini_available = [self.gemini_models_list.item(i).text() for i in range(self.gemini_models_list.count())]
            claude_available = [self.claude_models_list.item(i).text() for i in range(self.claude_models_list.count())]
            gpt_available = [self.gpt_models_list.item(i).text() for i in range(self.gpt_models_list.count())]

            # 기본 모델이 사용 가능 목록에 있는지 확인
            if gemini_model not in gemini_available and gemini_available:
                 QMessageBox.warning(self, "설정 오류", f"Gemini 기본 모델 '{gemini_model}'이(가) 사용 가능 목록에 없습니다. 목록에 추가하거나 다른 모델을 기본으로 선택하세요.")
                 return
            if claude_model not in claude_available and claude_available:
                 QMessageBox.warning(self, "설정 오류", f"Claude 기본 모델 '{claude_model}'이(가) 사용 가능 목록에 없습니다. 목록에 추가하거나 다른 모델을 기본으로 선택하세요.")
                 return
            if gpt_model not in gpt_available and gpt_available:
                 QMessageBox.warning(self, "설정 오류", f"GPT 기본 모델 '{gpt_model}'이(가) 사용 가능 목록에 없습니다. 목록에 추가하거나 다른 모델을 기본으로 선택하세요.")
                 return

            allowed_ext_str = self.allowed_extensions_edit.text().strip()
            allowed_extensions = {ext.strip() for ext in allowed_ext_str.replace(',', ' ').split() if ext.strip()}

            excluded_dirs = [line.strip() for line in self.excluded_dirs_edit.toPlainText().splitlines() if line.strip()]
            default_ignore = [line.strip() for line in self.default_ignore_list_edit.toPlainText().splitlines() if line.strip()]

            temp_str = self.gemini_temp_edit.text().strip()
            gemini_temp = float(temp_str) if temp_str else 0.0
            gemini_thinking = self.gemini_thinking_checkbox.isChecked()
            budget_str = self.gemini_budget_edit.text().strip()
            gemini_budget = int(budget_str) if budget_str else 0
            gemini_search = self.gemini_search_checkbox.isChecked()

            # --- 업데이트할 데이터 준비 ---
            # self.settings 객체는 이미 클릭 핸들러에 의해 기본 모델이 업데이트되었으므로,
            # 나머지 필드만 업데이트합니다.
            update_data = self.settings.model_copy(deep=True)
            update_data.default_system_prompt = default_prompt if default_prompt else None
            # 기본 모델은 이미 self.settings에 반영됨
            update_data.allowed_extensions = allowed_extensions
            update_data.excluded_dirs = set(excluded_dirs)
            update_data.default_ignore_list = default_ignore
            update_data.gemini_available_models = gemini_available
            update_data.claude_available_models = claude_available
            update_data.gpt_available_models = gpt_available
            update_data.gemini_temperature = gemini_temp
            update_data.gemini_enable_thinking = gemini_thinking
            update_data.gemini_thinking_budget = gemini_budget
            update_data.gemini_enable_search = gemini_search

            # --- Pydantic 유효성 검사 ---
            validated_settings = ConfigSettings(**update_data.model_dump(exclude={'gemini_api_key', 'anthropic_api_key'})) # API 키는 검증/저장 제외

            # --- 로깅 추가: 저장될 최종 설정 데이터 확인 ---
            logger.info("Validated settings data before saving to DB:")
            logger.info(f"{validated_settings.model_dump(exclude={'gemini_api_key', 'anthropic_api_key'})}")
            # ---------------------------------------------

            # --- DB 저장 ---
            if self.config_service.update_settings(validated_settings):
                # QMessageBox.information(self, "성공", "애플리케이션 설정이 성공적으로 저장되었습니다.") # 확인 메시지 제거
                logger.info("Application settings saved successfully.")
                # MainWindow의 관련 UI 업데이트 트리거
                self.mw.main_controller.on_llm_selected() # LLM/모델 콤보박스 업데이트
                self.mw.load_gemini_settings_to_ui() # 메인 윈도우의 Gemini 파라미터 UI 업데이트
                self.mw.file_tree_controller.load_gitignore_settings() # 필터링 규칙 업데이트
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
            if hasattr(self.mw, 'file_tree_controller'):
                self.mw.file_tree_controller.load_gitignore_settings()
        except Exception as e:
            QMessageBox.critical(self, "오류", f".gitignore 파일을 저장하는 중 오류 발생:\n{e}")
