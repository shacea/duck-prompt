import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox, QFrame
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont, QDesktopServices
from PyQt5.QtCore import Qt, QSize, QStandardPaths, QModelIndex, QItemSelection, QUrl # QItemSelection, QUrl 추가

# 변경된 경로에서 import
from core.pydantic_models.app_state import AppState # 상태 타입 힌트용
from core.services.config_service import ConfigService
from core.services.state_service import StateService
from core.services.template_service import TemplateService
from core.services.prompt_service import PromptService
from core.services.xml_service import XmlService
from core.services.filesystem_service import FilesystemService

from ui.models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
# 컨트롤러 import
from ui.controllers.main_controller import MainController
from ui.controllers.resource_controller import ResourceController
from ui.controllers.prompt_controller import PromptController
from ui.controllers.xml_controller import XmlController
from ui.controllers.file_tree_controller import FileTreeController
from ui.controllers.system_prompt_controller import apply_default_system_prompt, select_default_system_prompt

from ui.widgets.custom_text_edit import CustomTextEdit
from ui.widgets.custom_tab_bar import CustomTabBar # CustomTabBar 임포트
from utils.helpers import get_resource_path


class MainWindow(QMainWindow):
    def __init__(self, mode="Code Enhancer Prompt Builder"):
        super().__init__()
        self.mode = mode
        self.base_title = "DuckPrompt"
        self.update_window_title() # 초기 제목 설정

        # 스타일 설정
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        # --- 상태 변수 ---
        self.current_project_folder: Optional[str] = None
        self.last_generated_prompt: str = "" # 마지막 생성된 프롬프트 (단순 문자열)
        self.selected_files_data: List[tuple] = [] # 선택된 파일 정보 (UI 표시용)
        self.tree_generated: bool = False # 파일 트리 생성 여부

        # --- 서비스 인스턴스 생성 ---
        # TODO: 서비스 인스턴스를 app.py 등에서 생성하고 주입하는 방식 고려
        self.config_service = ConfigService()
        self.state_service = StateService()
        self.template_service = TemplateService()
        self.prompt_service = PromptService()
        self.xml_service = XmlService()
        self.fs_service = FilesystemService(self.config_service)

        # --- UI 구성 요소 생성 ---
        self._create_menu_bar()
        self._create_widgets()
        self._create_layout()
        self._create_status_bar()

        # --- 컨트롤러 생성 및 연결 ---
        # 각 컨트롤러에 MainWindow와 필요한 서비스 주입
        self.main_controller = MainController(self)
        self.resource_controller = ResourceController(self, self.template_service, self.state_service)
        self.prompt_controller = PromptController(self, self.prompt_service)
        self.xml_controller = XmlController(self, self.xml_service)
        self.file_tree_controller = FileTreeController(self, self.fs_service, self.config_service)

        # --- 시그널 연결 ---
        self._connect_signals()

        # --- 초기화 작업 ---
        self.resource_controller.load_templates_list() # 리소스 목록 로드
        self._apply_initial_settings() # 기본 설정 적용 (기본 프롬프트 등)

        # 상태바 메시지 및 창 크기 설정
        self.status_bar.showMessage("Ready")
        self.resize(1200, 800)
        self.build_tabs.setCurrentIndex(1) # 사용자 탭을 기본으로 표시

    def _create_menu_bar(self):
        """Creates the main menu bar."""
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # 모드 메뉴
        mode_menu = menubar.addMenu("모드")
        switch_to_code_action = QAction("코드 강화 빌더로 전환", self)
        switch_to_meta_action = QAction("메타 프롬프트 빌더로 전환", self)
        switch_to_code_action.triggered.connect(lambda: self._restart_with_mode("Code Enhancer Prompt Builder"))
        switch_to_meta_action.triggered.connect(lambda: self._restart_with_mode("Meta Prompt Builder"))
        mode_menu.addAction(switch_to_code_action)
        mode_menu.addAction(switch_to_meta_action)

        # 상태 메뉴
        state_menu = menubar.addMenu("상태")
        self.save_state_action = QAction("상태 저장(기본)", self)
        self.load_state_action = QAction("상태 불러오기(기본)", self)
        self.export_state_action = QAction("상태 내보내기", self)
        self.import_state_action = QAction("상태 가져오기", self)
        state_menu.addAction(self.save_state_action)
        state_menu.addAction(self.load_state_action)
        state_menu.addAction(self.export_state_action)
        state_menu.addAction(self.import_state_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")
        open_readme_action = QAction("README 열기", self)
        open_readme_action.triggered.connect(self._open_readme)
        help_menu.addAction(open_readme_action)


    def _create_widgets(self):
        """Creates the main widgets used in the window."""
        # --- 상단 버튼 및 레이블 ---
        self.mode_toggle_btn = QPushButton("🔄 모드 전환")
        self.reset_program_btn = QPushButton("🗑️ 전체 프로그램 리셋")
        self.select_project_btn = QPushButton("📁 프로젝트 폴더 선택")
        self.select_default_prompt_btn = QPushButton("⚙️ 기본 시스템 프롬프트 지정")
        for btn in [self.mode_toggle_btn, self.reset_program_btn, self.select_project_btn, self.select_default_prompt_btn]:
            btn.setFixedHeight(30)
        self.project_folder_label = QLabel("현재 프로젝트 폴더: (선택 안 됨)")
        font_lbl = self.project_folder_label.font()
        font_lbl.setPointSize(10)
        font_lbl.setBold(True)
        self.project_folder_label.setFont(font_lbl)

        # --- 파일 탐색기 (왼쪽) ---
        self.dir_model = FilteredFileSystemModel()
        self.tree_view = QTreeView()
        project_folder_getter = lambda: self.current_project_folder
        self.checkable_proxy = CheckableProxyModel(self.dir_model, project_folder_getter, self.tree_view)
        self.checkable_proxy.setSourceModel(self.dir_model)
        self.tree_view.setModel(self.checkable_proxy)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.hideColumn(1); self.tree_view.hideColumn(2); self.tree_view.hideColumn(3)
        self.tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        home_path = os.path.expanduser("~")
        root_index = self.dir_model.setRootPathFiltered(home_path)
        self.tree_view.setRootIndex(self.checkable_proxy.mapFromSource(root_index))


        # --- 탭 위젯 (오른쪽) ---
        self.build_tabs = QTabWidget()
        custom_tab_bar = CustomTabBar(self.build_tabs, self)
        self.build_tabs.setTabBar(custom_tab_bar)

        system_tab_label = "메타 프롬프트 템플릿" if self.mode == "Meta Prompt Builder" else "시스템"
        user_tab_label = "메타 사용자 입력" if self.mode == "Meta Prompt Builder" else "사용자"
        prompt_output_label = "메타 프롬프트 출력" if self.mode == "Meta Prompt Builder" else "프롬프트 출력"

        self.system_tab = CustomTextEdit()
        self.system_tab.setPlaceholderText(f"{system_tab_label} 내용 입력...")
        self.build_tabs.addTab(self.system_tab, system_tab_label)

        self.user_tab = CustomTextEdit()
        self.user_tab.setPlaceholderText(f"{user_tab_label} 내용 입력...")
        self.build_tabs.addTab(self.user_tab, user_tab_label)

        if self.mode != "Meta Prompt Builder":
            self.dir_structure_tab = CustomTextEdit()
            self.dir_structure_tab.setReadOnly(True)
            self.build_tabs.addTab(self.dir_structure_tab, "파일 트리")

        self.prompt_output_tab = CustomTextEdit()
        self.prompt_output_tab.setFont(QFont("Consolas", 10))
        self.prompt_output_tab.setStyleSheet("QTextEdit { padding: 10px; }")
        self.build_tabs.addTab(self.prompt_output_tab, prompt_output_label)

        if self.mode != "Meta Prompt Builder":
            self.xml_input_tab = CustomTextEdit()
            self.xml_input_tab.setPlaceholderText("XML 내용 입력...")
            self.build_tabs.addTab(self.xml_input_tab, "XML 입력")

        if self.mode == "Meta Prompt Builder":
            self.meta_prompt_tab = CustomTextEdit()
            self.meta_prompt_tab.setPlaceholderText("메타 프롬프트 내용...")
            self.build_tabs.addTab(self.meta_prompt_tab, "메타 프롬프트")

            self.user_prompt_tab = CustomTextEdit()
            self.user_prompt_tab.setPlaceholderText("사용자 프롬프트 내용 입력...")
            self.build_tabs.addTab(self.user_prompt_tab, "사용자 프롬프트")

            self.final_prompt_tab = CustomTextEdit()
            self.final_prompt_tab.setFont(QFont("Consolas", 10))
            self.final_prompt_tab.setStyleSheet("QTextEdit { padding: 10px; }")
            self.build_tabs.addTab(self.final_prompt_tab, "최종 프롬프트")

        # --- 실행 버튼 (오른쪽 상단) ---
        copy_btn_label = "📋 메타 프롬프트 복사" if self.mode == "Meta Prompt Builder" else "📋 클립보드에 복사"
        if self.mode != "Meta Prompt Builder":
            self.generate_tree_btn = QPushButton("🌳 트리 생성")
            self.generate_btn = QPushButton("✨ 프롬프트 생성")
            self.copy_btn = QPushButton(copy_btn_label)
            self.run_xml_parser_btn = QPushButton("▶️ XML 파서 실행")
            self.generate_all_btn = QPushButton("⚡️ 한번에 실행")
            self.run_buttons = [self.generate_tree_btn, self.generate_btn, self.copy_btn, self.run_xml_parser_btn, self.generate_all_btn]
        else:
            self.generate_btn = QPushButton("🚀 메타 프롬프트 생성")
            self.copy_btn = QPushButton(copy_btn_label)
            self.generate_final_prompt_btn = QPushButton("🚀 최종 프롬프트 생성")
            self.run_buttons = [self.generate_btn, self.copy_btn, self.generate_final_prompt_btn]

        # --- 리소스 관리 (왼쪽 하단) ---
        self.resource_mode_combo = QComboBox()
        self.resource_mode_combo.addItems(["프롬프트", "상태"])
        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderHidden(True)
        self.load_selected_template_btn = QPushButton("📥 선택 불러오기")
        self.save_as_template_btn = QPushButton("💾 현재 내용으로 저장")
        self.template_type_label = QLabel("저장 타입:")
        self.template_type_combo = QComboBox()
        self.template_type_combo.addItems(["시스템", "사용자"])
        self.delete_template_btn = QPushButton("❌ 선택 삭제")
        self.update_template_btn = QPushButton("🔄 현재 내용 업데이트")
        self.backup_button = QPushButton("📦 모든 상태 백업")
        self.restore_button = QPushButton("🔙 백업에서 상태 복원")

        # --- .gitignore 뷰어/편집기 (오른쪽 하단) ---
        self.gitignore_tabwidget = QTabWidget()
        self.gitignore_edit = CustomTextEdit()
        self.gitignore_edit.setPlaceholderText(".gitignore 내용...")
        self.save_gitignore_btn = QPushButton("💾 .gitignore 저장")

    def _create_layout(self):
        """Creates the layout and arranges widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # --- 상단 레이아웃 ---
        top_button_container = QWidget()
        top_button_layout = QHBoxLayout(top_button_container)
        top_button_layout.setSpacing(10)
        top_button_layout.setContentsMargins(0, 0, 0, 0)
        top_button_layout.addWidget(self.mode_toggle_btn)
        top_button_layout.addWidget(self.reset_program_btn)
        top_button_layout.addWidget(self.select_project_btn)
        top_button_layout.addWidget(self.select_default_prompt_btn)
        top_button_layout.addStretch(1)

        top_layout_wrapper = QVBoxLayout()
        top_layout_wrapper.setSpacing(5)
        top_layout_wrapper.setContentsMargins(0, 0, 0, 0)
        top_layout_wrapper.addWidget(top_button_container)
        top_layout_wrapper.addWidget(self.project_folder_label)
        main_layout.addLayout(top_layout_wrapper)

        # --- 중앙 스플리터 (파일 트리 | 탭 위젯) ---
        center_splitter = QSplitter(Qt.Horizontal)

        left_side_widget = QWidget()
        left_side_layout = QVBoxLayout(left_side_widget)
        left_side_layout.setContentsMargins(2, 2, 2, 2)
        left_side_layout.setSpacing(5)
        left_side_layout.addWidget(self.tree_view)
        center_splitter.addWidget(left_side_widget)

        right_side_widget = QWidget()
        right_side_layout = QVBoxLayout(right_side_widget)
        right_side_layout.setContentsMargins(0, 0, 0, 0)
        right_side_layout.setSpacing(0)

        run_buttons_container = QWidget()
        run_layout = QHBoxLayout(run_buttons_container)
        run_layout.setContentsMargins(5, 5, 5, 5)
        run_layout.setSpacing(10)
        run_layout.setAlignment(Qt.AlignLeft)
        for btn in self.run_buttons:
            run_layout.addWidget(btn)

        line_frame = QFrame()
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)

        right_side_layout.addWidget(run_buttons_container)
        right_side_layout.addWidget(line_frame)
        right_side_layout.addWidget(self.build_tabs)
        center_splitter.addWidget(right_side_widget)

        main_layout.addWidget(center_splitter, stretch=4)

        # --- 하단 스플리터 (리소스 관리 | .gitignore) ---
        bottom_splitter = QSplitter(Qt.Horizontal)

        template_manager_frame = QFrame()
        tm_layout = QVBoxLayout(template_manager_frame)
        tm_layout.setContentsMargins(5, 5, 5, 5)
        tm_layout.setSpacing(5)

        tm_vertical_layout = QVBoxLayout()
        tm_vertical_layout.setContentsMargins(0, 0, 0, 0)
        tm_vertical_layout.setSpacing(5)

        tm_vertical_layout.addWidget(QLabel("리소스 타입 선택:"))
        tm_vertical_layout.addWidget(self.resource_mode_combo)
        tm_vertical_layout.addWidget(QLabel("아래에서 로드/저장할 리소스 선택:"))
        tm_vertical_layout.addWidget(self.template_tree)

        tm_button_layout = QVBoxLayout()
        tm_button_layout.setSpacing(5)
        first_row = QHBoxLayout(); first_row.addWidget(self.load_selected_template_btn); tm_button_layout.addLayout(first_row)
        second_row = QHBoxLayout(); second_row.addWidget(self.template_type_label); second_row.addWidget(self.template_type_combo); second_row.addWidget(self.save_as_template_btn); tm_button_layout.addLayout(second_row)
        third_row = QHBoxLayout(); third_row.addWidget(self.delete_template_btn); third_row.addWidget(self.update_template_btn); tm_button_layout.addLayout(third_row)
        fourth_row = QHBoxLayout(); fourth_row.addWidget(self.backup_button); fourth_row.addWidget(self.restore_button); tm_button_layout.addLayout(fourth_row)

        tm_vertical_layout.addLayout(tm_button_layout)
        tm_layout.addLayout(tm_vertical_layout)
        bottom_splitter.addWidget(template_manager_frame)

        gitignore_frame = QFrame()
        gitignore_layout = QVBoxLayout(gitignore_frame)
        gitignore_layout.setContentsMargins(5, 5, 5, 5)
        gitignore_layout.setSpacing(5)

        gitignore_edit_tab = QWidget()
        gitignore_edit_layout = QVBoxLayout(gitignore_edit_tab)
        gitignore_edit_layout.setContentsMargins(5, 5, 5, 5)
        gitignore_edit_layout.setSpacing(5)
        gitignore_edit_layout.addWidget(QLabel(".gitignore 보기/편집:"))
        gitignore_edit_layout.addWidget(self.gitignore_edit)
        gitignore_edit_layout.addWidget(self.save_gitignore_btn)

        self.gitignore_tabwidget.addTab(gitignore_edit_tab, ".gitignore")
        gitignore_layout.addWidget(self.gitignore_tabwidget)
        bottom_splitter.addWidget(gitignore_frame)

        main_layout.addWidget(bottom_splitter, stretch=2)

        center_splitter.setStretchFactor(0, 1)
        center_splitter.setStretchFactor(1, 3)
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 1)

    def _create_status_bar(self):
        """Creates the status bar with character and token counts."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.char_count_label = QLabel("Chars: 0")
        self.token_count_label = QLabel("토큰 계산: 비활성화")
        self.auto_token_calc_check = QCheckBox("토큰 자동 계산")
        self.auto_token_calc_check.setChecked(True)

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)
        status_layout.addWidget(self.char_count_label)
        status_layout.addWidget(self.auto_token_calc_check)
        status_layout.addWidget(self.token_count_label)

        self.status_bar.addPermanentWidget(status_widget)

    def _connect_signals(self):
        """Connects widget signals to controller slots."""
        # 상단 버튼
        self.mode_toggle_btn.clicked.connect(self._toggle_mode)
        self.reset_program_btn.clicked.connect(self.main_controller.reset_program) # MainController
        self.select_project_btn.clicked.connect(self.file_tree_controller.select_project_folder) # FileTreeController
        self.select_default_prompt_btn.clicked.connect(lambda: select_default_system_prompt(self)) # SystemPromptController (함수 직접 호출)

        # 파일 트리
        self.tree_view.customContextMenuRequested.connect(self.on_tree_view_context_menu) # MainWindow (컨트롤러 호출)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed_handler) # MainWindow (컨트롤러 호출)
        self.checkable_proxy.dataChanged.connect(self.file_tree_controller.on_data_changed) # FileTreeController

        # 실행 버튼
        if self.mode != "Meta Prompt Builder":
            self.generate_tree_btn.clicked.connect(self.file_tree_controller.generate_directory_tree_structure) # FileTreeController
            self.generate_btn.clicked.connect(self.prompt_controller.generate_prompt) # PromptController
            self.copy_btn.clicked.connect(self.prompt_controller.copy_to_clipboard) # PromptController
            self.run_xml_parser_btn.clicked.connect(self.xml_controller.run_xml_parser) # XmlController
            self.generate_all_btn.clicked.connect(self.prompt_controller.generate_all_and_copy) # PromptController
        else:
            self.generate_btn.clicked.connect(self.prompt_controller.generate_meta_prompt) # PromptController
            self.copy_btn.clicked.connect(self.prompt_controller.copy_to_clipboard) # PromptController
            if hasattr(self, "generate_final_prompt_btn"):
                self.generate_final_prompt_btn.clicked.connect(self.prompt_controller.generate_final_meta_prompt) # PromptController

        # 리소스 관리
        self.resource_mode_combo.currentIndexChanged.connect(self.resource_controller.load_templates_list) # ResourceController
        self.load_selected_template_btn.clicked.connect(self.resource_controller.load_selected_item) # ResourceController
        self.save_as_template_btn.clicked.connect(self.resource_controller.save_current_as_item) # ResourceController
        self.delete_template_btn.clicked.connect(self.resource_controller.delete_selected_item) # ResourceController
        self.update_template_btn.clicked.connect(self.resource_controller.update_current_item) # ResourceController
        self.backup_button.clicked.connect(self.resource_controller.backup_all_states_action) # ResourceController
        self.restore_button.clicked.connect(self.resource_controller.restore_states_from_backup_action) # ResourceController
        self.template_tree.itemDoubleClicked.connect(self.resource_controller.load_selected_item) # ResourceController

        # .gitignore
        self.save_gitignore_btn.clicked.connect(self.file_tree_controller.save_gitignore_settings) # FileTreeController

        # 상태바
        self.auto_token_calc_check.stateChanged.connect(self.main_controller.update_active_tab_counts) # MainController
        # 텍스트 변경 시 카운트 업데이트
        self.prompt_output_tab.textChanged.connect(self.main_controller.update_active_tab_counts)
        if hasattr(self, 'final_prompt_tab'):
            self.final_prompt_tab.textChanged.connect(self.main_controller.update_active_tab_counts)
        # 다른 탭들도 필요시 연결
        self.system_tab.textChanged.connect(self.main_controller.update_active_tab_counts)
        self.user_tab.textChanged.connect(self.main_controller.update_active_tab_counts)
        if hasattr(self, 'meta_prompt_tab'):
            self.meta_prompt_tab.textChanged.connect(self.main_controller.update_active_tab_counts)
        if hasattr(self, 'user_prompt_tab'):
            self.user_prompt_tab.textChanged.connect(self.main_controller.update_active_tab_counts)


        # 메뉴 액션
        self.save_state_action.triggered.connect(self.resource_controller.save_state_to_default) # ResourceController
        self.load_state_action.triggered.connect(self.resource_controller.load_state_from_default) # ResourceController
        self.export_state_action.triggered.connect(self.resource_controller.export_state_to_file) # ResourceController
        self.import_state_action.triggered.connect(self.resource_controller.import_state_from_file) # ResourceController

        # 단축키
        shortcut_generate = QAction(self)
        shortcut_generate.setShortcut(QKeySequence("Ctrl+Return"))
        if self.mode == "Meta Prompt Builder":
             shortcut_generate.triggered.connect(self.prompt_controller.generate_meta_prompt) # PromptController
        else:
             shortcut_generate.triggered.connect(self.prompt_controller.generate_prompt) # PromptController
        self.addAction(shortcut_generate)

        shortcut_copy = QAction(self)
        shortcut_copy.setShortcut(QKeySequence("Ctrl+C"))
        shortcut_copy.triggered.connect(self.on_copy_shortcut) # MainWindow
        self.addAction(shortcut_copy)

    def _apply_initial_settings(self):
        """Applies initial settings like default system prompt."""
        apply_default_system_prompt(self)

        if self.mode == "Meta Prompt Builder":
            meta_prompt_path_relative = os.path.join("prompts", "system", "META_Prompt.md")
            try:
                meta_prompt_path = get_resource_path(meta_prompt_path_relative)
                if os.path.exists(meta_prompt_path):
                    with open(meta_prompt_path, "r", encoding="utf-8") as f:
                        self.system_tab.setText(f.read())
            except Exception as e:
                print(f"Error loading default META prompt: {e}")

        self.file_tree_controller.load_gitignore_settings() # FileTreeController
        self.resource_controller.update_buttons_label() # ResourceController

    def _restart_with_mode(self, new_mode: str):
        """Restarts the application with the specified mode."""
        self.close()
        new_window = MainWindow(mode=new_mode)
        new_window.show()

    def _toggle_mode(self):
        """Toggles between application modes."""
        if self.mode == "Code Enhancer Prompt Builder":
            self._restart_with_mode("Meta Prompt Builder")
        else:
            self._restart_with_mode("Code Enhancer Prompt Builder")

    def _open_readme(self):
        """Opens the README.md file in the default web browser or text editor."""
        # README.md 파일 경로 찾기 (main.py 기준)
        readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'README.md'))
        if os.path.exists(readme_path):
            # QDesktopServices를 사용하여 파일 열기 시도
            url = QUrl.fromLocalFile(readme_path)
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(self, "오류", "README.md 파일을 여는 데 실패했습니다.\n파일 탐색기에서 직접 열어주세요.")
        else:
            QMessageBox.warning(self, "오류", "README.md 파일을 찾을 수 없습니다.")


    # --- Public Methods (Controller에서 호출) ---

    def reset_state(self):
        """Resets internal state variables of the MainWindow."""
        self.current_project_folder = None
        self.last_generated_prompt = ""
        self.selected_files_data = []
        self.tree_generated = False
        if hasattr(self, 'checkable_proxy'):
            self.checkable_proxy.checked_files_dict.clear()
        self.update_window_title()

    def update_window_title(self, folder_name: Optional[str] = None):
        """Updates the window title based on the project folder."""
        if folder_name:
            self.setWindowTitle(f"{folder_name} - {self.base_title}")
        else:
            self.setWindowTitle(self.base_title)

    def get_current_state(self) -> AppState:
        """Gathers the current UI state and returns it as an AppState model."""
        checked_paths = self.checkable_proxy.get_all_checked_paths() if hasattr(self, 'checkable_proxy') else []
        state_data = {
            "mode": self.mode,
            "project_folder": self.current_project_folder,
            "system_prompt": self.system_tab.toPlainText(),
            "user_prompt": self.user_tab.toPlainText(),
            "checked_files": checked_paths
        }
        try:
            app_state = AppState(**state_data)
            return app_state
        except Exception as e:
             print(f"Error creating AppState model: {e}")
             return AppState(mode=self.mode)

    def set_current_state(self, state: AppState):
        """Sets the UI state based on the provided AppState model."""
        if self.mode != state.mode:
            print(f"Mode mismatch during state load. Current: {self.mode}, Loaded: {state.mode}. Restarting...")
            self._restart_with_mode(state.mode)
            return # 재시작 후 새 인스턴스에서 상태 로드됨

        self.reset_state()

        folder_name = None
        if state.project_folder and os.path.isdir(state.project_folder):
            self.current_project_folder = state.project_folder
            folder_name = os.path.basename(state.project_folder)
            self.project_folder_label.setText(f"현재 프로젝트 폴더: {state.project_folder}")
            if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                idx = self.dir_model.setRootPathFiltered(state.project_folder)
                self.tree_view.setRootIndex(self.checkable_proxy.mapFromSource(idx))
            self.status_bar.showMessage(f"Project Folder: {state.project_folder}")
        else:
             self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
             home_path = os.path.expanduser("~")
             if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                 idx = self.dir_model.setRootPathFiltered(home_path)
                 self.tree_view.setRootIndex(self.checkable_proxy.mapFromSource(idx))

        self.system_tab.setText(state.system_prompt)
        self.user_tab.setText(state.user_prompt)

        if hasattr(self, 'checkable_proxy'):
            self.uncheck_all_files()
            for fpath in state.checked_files:
                 src_index = self.dir_model.index(fpath)
                 if src_index.isValid():
                     proxy_index = self.checkable_proxy.mapFromSource(src_index)
                     if proxy_index.isValid():
                         self.checkable_proxy.setData(proxy_index, Qt.Checked, Qt.CheckStateRole)

        self.file_tree_controller.load_gitignore_settings() # FileTreeController
        self.update_window_title(folder_name)
        self.resource_controller.update_buttons_label() # ResourceController
        self.status_bar.showMessage("State loaded successfully!")


    def uncheck_all_files(self):
        """Unchecks all items in the file tree view."""
        if not hasattr(self, 'checkable_proxy'): return
        self.checkable_proxy.checked_files_dict.clear()
        root_proxy_index = self.tree_view.rootIndex()
        if root_proxy_index.isValid():
            self._recursive_uncheck(root_proxy_index)


    def _recursive_uncheck(self, proxy_index: QModelIndex):
        """Helper method to recursively uncheck items via setData."""
        if not proxy_index.isValid(): return
        current_state = self.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
        if current_state == Qt.Checked:
            self.checkable_proxy.setData(proxy_index, Qt.Unchecked, Qt.CheckStateRole) # setData 호출 시 하위 항목 처리됨

        # 자식 항목 재귀 호출 (setData에서 이미 처리되므로 불필요할 수 있음)
        # child_count = self.checkable_proxy.rowCount(proxy_index)
        # for row in range(child_count):
        #     child_proxy_idx = self.checkable_proxy.index(row, 0, proxy_index)
        #     self._recursive_uncheck(child_proxy_idx)


    def create_tree_item(self, text, parent=None) -> QTreeWidgetItem:
        """Helper method to create items in the template/state tree."""
        if parent is None:
            item = QTreeWidgetItem([text])
            self.template_tree.addTopLevelItem(item)
        else:
            item = QTreeWidgetItem([text])
            parent.addChild(item)
        return item

    def add_new_custom_tab(self):
        """Adds a new custom tab to the build_tabs widget."""
        new_tab_name, ok = QInputDialog.getText(self, "새 탭 추가", "새 탭의 이름을 입력하세요:")
        if ok and new_tab_name and new_tab_name.strip():
            new_name = new_tab_name.strip()
            from ui.widgets.tab_manager import is_tab_deletable
            if not is_tab_deletable(new_name):
                 QMessageBox.warning(self, "경고", f"'{new_name}'은(는) 사용할 수 없는 탭 이름입니다.")
                 return
            # 중복 이름 확인
            for i in range(self.build_tabs.count()):
                if self.build_tabs.tabText(i) == new_name:
                    QMessageBox.warning(self, "경고", f"'{new_name}' 탭이 이미 존재합니다.")
                    return

            new_tab = CustomTextEdit()
            new_tab.setPlaceholderText(f"{new_name} 내용 입력...")
            plus_tab_index = -1
            for i in range(self.build_tabs.count()):
                if self.build_tabs.tabText(i) == "+":
                    plus_tab_index = i
                    break
            if plus_tab_index != -1:
                 self.build_tabs.insertTab(plus_tab_index, new_tab, new_name)
                 self.build_tabs.setCurrentIndex(plus_tab_index)
            else:
                 self.build_tabs.addTab(new_tab, new_name)
                 self.build_tabs.setCurrentIndex(self.build_tabs.count() - 1)
            # 새 탭 추가 시 토큰 계산 연결
            new_tab.textChanged.connect(self.main_controller.update_active_tab_counts)

        elif ok:
             QMessageBox.warning(self, "경고", "탭 이름은 비워둘 수 없습니다.")


    # --- Event Handlers ---

    def on_copy_shortcut(self):
        """Handles Ctrl+C shortcut, copies if prompt output tab is active."""
        current_widget = self.build_tabs.currentWidget()
        if isinstance(current_widget, CustomTextEdit): # 현재 위젯이 텍스트 편집기인지 확인
            # 선택된 텍스트가 있으면 그것을 복사
            if current_widget.textCursor().hasSelection():
                current_widget.copy()
            # 선택된 텍스트가 없고, 특정 탭(프롬프트 출력 등)이면 전체 내용 복사
            elif current_widget == self.prompt_output_tab or \
                 (hasattr(self, 'final_prompt_tab') and current_widget == self.final_prompt_tab):
                self.prompt_controller.copy_to_clipboard() # PromptController의 복사 메서드 사용
            # 그 외의 경우 기본 copy 동작 (아무것도 안 할 수 있음)
            # else:
            #     current_widget.copy()


    def on_tree_view_context_menu(self, position):
        """Handles context menu requests on the file tree view."""
        index = self.tree_view.indexAt(position)
        if not index.isValid(): return

        file_path = self.checkable_proxy.get_file_path_from_index(index)
        if not file_path: return

        menu = QMenu()
        rename_action = menu.addAction("이름 변경")
        delete_action = menu.addAction("삭제")
        action = menu.exec_(self.tree_view.viewport().mapToGlobal(position))

        if action == rename_action:
            self.file_tree_controller.rename_item(file_path) # FileTreeController
        elif action == delete_action:
            self.file_tree_controller.delete_item(file_path) # FileTreeController


    def on_selection_changed_handler(self, selected: QItemSelection, deselected: QItemSelection):
        """Handles selection changes in the file tree view to toggle check state."""
        # FileTreeController에게 위임
        self.file_tree_controller.handle_selection_change(selected, deselected)
