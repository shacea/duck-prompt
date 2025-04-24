import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox, QFrame
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont
from PyQt5.QtCore import Qt, QSize, QStandardPaths, QModelIndex # QModelIndex 추가

# 변경된 경로에서 import
# from core.services.config_service import ConfigService # Controller 통해 접근
from core.pydantic_models.app_state import AppState # 상태 타입 힌트용
from ui.models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
from ui.controllers.main_controller import MainController
from ui.widgets.custom_text_edit import CustomTextEdit
from ui.widgets.custom_tab_bar import CustomTabBar # CustomTabBar 임포트
# from ui.widgets.tab_manager import is_tab_deletable # CustomTabBar 내부에서 사용
from utils.helpers import get_resource_path
from ui.controllers.system_prompt_controller import apply_default_system_prompt, select_default_system_prompt

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

        # --- UI 구성 요소 생성 ---
        self._create_menu_bar()
        self._create_widgets()
        self._create_layout()
        self._create_status_bar()

        # --- 컨트롤러 생성 및 연결 ---
        # TODO: 서비스 인스턴스 생성 및 컨트롤러에 주입
        self.controller = MainController(self)

        # --- 시그널 연결 ---
        self._connect_signals()

        # --- 초기화 작업 ---
        self.controller.load_templates_list() # 리소스 목록 로드
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
        # TODO: ConfigService 주입 방식 변경 필요
        # self.dir_model = FilteredFileSystemModel(config) # config 제거됨
        self.dir_model = FilteredFileSystemModel()
        self.tree_view = QTreeView()
        # project_folder_getter 람다 함수 정의
        project_folder_getter = lambda: self.current_project_folder
        self.checkable_proxy = CheckableProxyModel(self.dir_model, project_folder_getter, self.tree_view)
        self.checkable_proxy.setSourceModel(self.dir_model)
        self.tree_view.setModel(self.checkable_proxy)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.hideColumn(1); self.tree_view.hideColumn(2); self.tree_view.hideColumn(3)
        self.tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection) # ExtendedSelection 유지
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu) # 컨텍스트 메뉴 정책 유지
        # 초기 경로 설정 (예: 홈 디렉토리)
        home_path = os.path.expanduser("~")
        root_index = self.dir_model.setRootPathFiltered(home_path)
        self.tree_view.setRootIndex(self.checkable_proxy.mapFromSource(root_index))


        # --- 탭 위젯 (오른쪽) ---
        self.build_tabs = QTabWidget()
        # CustomTabBar 사용
        custom_tab_bar = CustomTabBar(self.build_tabs, self)
        self.build_tabs.setTabBar(custom_tab_bar)

        # 탭 생성 (모드에 따라 레이블 변경)
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
        # self.prompt_output_tab.setReadOnly(True) # 읽기 전용 제거 (편집 가능하도록)
        self.prompt_output_tab.setFont(QFont("Consolas", 10))
        self.prompt_output_tab.setStyleSheet("QTextEdit { padding: 10px; }")
        self.build_tabs.addTab(self.prompt_output_tab, prompt_output_label)

        if self.mode != "Meta Prompt Builder":
            self.xml_input_tab = CustomTextEdit()
            self.xml_input_tab.setPlaceholderText("XML 내용 입력...")
            self.build_tabs.addTab(self.xml_input_tab, "XML 입력")

        # Meta Prompt Builder 모드 전용 탭들
        if self.mode == "Meta Prompt Builder":
            # 구분자 탭 (닫기/이름 변경 불가 처리 필요 - CustomTabBar에서 처리)
            # separator_tab = QWidget() # 내용 없는 위젯 사용 가능
            # self.build_tabs.addTab(separator_tab, "   |   ")
            # self.build_tabs.setTabEnabled(self.build_tabs.indexOf(separator_tab), False) # 비활성화

            self.meta_prompt_tab = CustomTextEdit()
            self.meta_prompt_tab.setPlaceholderText("메타 프롬프트 내용...")
            self.build_tabs.addTab(self.meta_prompt_tab, "메타 프롬프트")

            self.user_prompt_tab = CustomTextEdit()
            self.user_prompt_tab.setPlaceholderText("사용자 프롬프트 내용 입력...")
            self.build_tabs.addTab(self.user_prompt_tab, "사용자 프롬프트")

            self.final_prompt_tab = CustomTextEdit()
            # self.final_prompt_tab.setReadOnly(True) # 읽기 전용 제거
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
        self.load_selected_template_btn = QPushButton("📥 선택 불러오기") # 초기 텍스트
        self.save_as_template_btn = QPushButton("💾 현재 내용으로 저장") # 초기 텍스트
        self.template_type_label = QLabel("저장 타입:")
        self.template_type_combo = QComboBox()
        self.template_type_combo.addItems(["시스템", "사용자"])
        self.delete_template_btn = QPushButton("❌ 선택 삭제") # 초기 텍스트
        self.update_template_btn = QPushButton("🔄 현재 내용 업데이트") # 초기 텍스트
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
        top_button_layout.addStretch(1) # 버튼들을 왼쪽으로 정렬

        top_layout_wrapper = QVBoxLayout()
        top_layout_wrapper.setSpacing(5)
        top_layout_wrapper.setContentsMargins(0, 0, 0, 0)
        top_layout_wrapper.addWidget(top_button_container)
        top_layout_wrapper.addWidget(self.project_folder_label)
        main_layout.addLayout(top_layout_wrapper)

        # --- 중앙 스플리터 (파일 트리 | 탭 위젯) ---
        center_splitter = QSplitter(Qt.Horizontal)

        # 왼쪽 (파일 트리)
        left_side_widget = QWidget()
        left_side_layout = QVBoxLayout(left_side_widget)
        left_side_layout.setContentsMargins(2, 2, 2, 2)
        left_side_layout.setSpacing(5)
        left_side_layout.addWidget(self.tree_view)
        center_splitter.addWidget(left_side_widget)

        # 오른쪽 (탭 위젯)
        right_side_widget = QWidget()
        right_side_layout = QVBoxLayout(right_side_widget)
        right_side_layout.setContentsMargins(0, 0, 0, 0)
        right_side_layout.setSpacing(0) # 간격 없음

        # 실행 버튼 컨테이너
        run_buttons_container = QWidget()
        run_layout = QHBoxLayout(run_buttons_container)
        run_layout.setContentsMargins(5, 5, 5, 5)
        run_layout.setSpacing(10)
        run_layout.setAlignment(Qt.AlignLeft)
        for btn in self.run_buttons:
            run_layout.addWidget(btn)

        # 구분선
        line_frame = QFrame()
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        # line_frame.setFixedHeight(2)
        # line_frame.setStyleSheet("background-color: #ccc;")

        right_side_layout.addWidget(run_buttons_container)
        right_side_layout.addWidget(line_frame)
        right_side_layout.addWidget(self.build_tabs) # 탭 위젯 추가
        center_splitter.addWidget(right_side_widget)

        main_layout.addWidget(center_splitter, stretch=4) # 중앙 영역이 더 많은 공간 차지

        # --- 하단 스플리터 (리소스 관리 | .gitignore) ---
        bottom_splitter = QSplitter(Qt.Horizontal)

        # 왼쪽 하단 (리소스 관리)
        template_manager_frame = QFrame()
        tm_layout = QVBoxLayout(template_manager_frame)
        tm_layout.setContentsMargins(5, 5, 5, 5)
        tm_layout.setSpacing(5)

        tm_vertical_layout = QVBoxLayout() # 내부 레이아웃
        tm_vertical_layout.setContentsMargins(0, 0, 0, 0) # 내부 마진 제거
        tm_vertical_layout.setSpacing(5)

        tm_vertical_layout.addWidget(QLabel("리소스 타입 선택:"))
        tm_vertical_layout.addWidget(self.resource_mode_combo)
        tm_vertical_layout.addWidget(QLabel("아래에서 로드/저장할 리소스 선택:"))
        tm_vertical_layout.addWidget(self.template_tree) # 트리 위젯 추가

        # 리소스 관리 버튼 레이아웃
        tm_button_layout = QVBoxLayout()
        tm_button_layout.setSpacing(5)
        first_row = QHBoxLayout(); first_row.addWidget(self.load_selected_template_btn); tm_button_layout.addLayout(first_row)
        second_row = QHBoxLayout(); second_row.addWidget(self.template_type_label); second_row.addWidget(self.template_type_combo); second_row.addWidget(self.save_as_template_btn); tm_button_layout.addLayout(second_row)
        third_row = QHBoxLayout(); third_row.addWidget(self.delete_template_btn); third_row.addWidget(self.update_template_btn); tm_button_layout.addLayout(third_row)
        fourth_row = QHBoxLayout(); fourth_row.addWidget(self.backup_button); fourth_row.addWidget(self.restore_button); tm_button_layout.addLayout(fourth_row)

        tm_vertical_layout.addLayout(tm_button_layout)
        tm_layout.addLayout(tm_vertical_layout) # 프레임에 내부 레이아웃 추가
        bottom_splitter.addWidget(template_manager_frame)

        # 오른쪽 하단 (.gitignore)
        gitignore_frame = QFrame()
        gitignore_layout = QVBoxLayout(gitignore_frame)
        gitignore_layout.setContentsMargins(5, 5, 5, 5)
        gitignore_layout.setSpacing(5)

        gitignore_edit_tab = QWidget() # 탭 내용 위젯
        gitignore_edit_layout = QVBoxLayout(gitignore_edit_tab)
        gitignore_edit_layout.setContentsMargins(5, 5, 5, 5)
        gitignore_edit_layout.setSpacing(5)
        gitignore_edit_layout.addWidget(QLabel(".gitignore 보기/편집:"))
        gitignore_edit_layout.addWidget(self.gitignore_edit)
        gitignore_edit_layout.addWidget(self.save_gitignore_btn)

        self.gitignore_tabwidget.addTab(gitignore_edit_tab, ".gitignore")
        gitignore_layout.addWidget(self.gitignore_tabwidget)
        bottom_splitter.addWidget(gitignore_frame)

        main_layout.addWidget(bottom_splitter, stretch=2) # 하단 영역 비율

        # 스플리터 크기 비율 설정
        center_splitter.setStretchFactor(0, 1) # 왼쪽 파일 트리 비율
        center_splitter.setStretchFactor(1, 3) # 오른쪽 탭 위젯 비율
        bottom_splitter.setStretchFactor(0, 1) # 왼쪽 리소스 관리 비율
        bottom_splitter.setStretchFactor(1, 1) # 오른쪽 .gitignore 비율

    def _create_status_bar(self):
        """Creates the status bar with character and token counts."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.char_count_label = QLabel("Chars: 0")
        self.token_count_label = QLabel("토큰 계산: 비활성화") # 초기 텍스트
        self.auto_token_calc_check = QCheckBox("토큰 자동 계산")
        self.auto_token_calc_check.setChecked(True) # 기본값 체크

        status_widget = QWidget() # 상태바 오른쪽에 위젯 추가용
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)
        status_layout.addWidget(self.char_count_label)
        status_layout.addWidget(self.auto_token_calc_check)
        status_layout.addWidget(self.token_count_label)
        # status_layout.addStretch(1) # 상태바 끝까지 확장 안 함

        self.status_bar.addPermanentWidget(status_widget)

    def _connect_signals(self):
        """Connects widget signals to controller slots."""
        # 상단 버튼
        self.mode_toggle_btn.clicked.connect(self._toggle_mode) # 내부 메서드 연결
        self.reset_program_btn.clicked.connect(self.controller.reset_program)
        self.select_project_btn.clicked.connect(self.controller.select_project_folder)
        self.select_default_prompt_btn.clicked.connect(lambda: select_default_system_prompt(self)) # 컨트롤러 함수 직접 연결

        # 파일 트리
        self.tree_view.customContextMenuRequested.connect(self.on_tree_view_context_menu) # 컨텍스트 메뉴 연결
        # selectionChanged 시그널 연결 (파일/폴더 클릭 시 체크 토글)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed_handler)
        # checkable_proxy의 dataChanged 시그널 연결 (체크 상태 변경 시 카운트 업데이트 등)
        self.checkable_proxy.dataChanged.connect(self.controller.on_data_changed)

        # 실행 버튼
        if self.mode != "Meta Prompt Builder":
            self.generate_tree_btn.clicked.connect(self.controller.generate_directory_tree_structure)
            self.generate_btn.clicked.connect(self.controller.generate_prompt)
            self.copy_btn.clicked.connect(self.controller.copy_to_clipboard)
            self.run_xml_parser_btn.clicked.connect(self.controller.run_xml_parser)
            self.generate_all_btn.clicked.connect(self.controller.generate_all_and_copy)
        else:
            self.generate_btn.clicked.connect(self.controller.generate_meta_prompt)
            self.copy_btn.clicked.connect(self.controller.copy_to_clipboard)
            if hasattr(self, "generate_final_prompt_btn"):
                self.generate_final_prompt_btn.clicked.connect(self.controller.generate_final_meta_prompt)

        # 리소스 관리
        self.resource_mode_combo.currentIndexChanged.connect(self.controller.load_templates_list)
        self.load_selected_template_btn.clicked.connect(self.controller.load_selected_item)
        self.save_as_template_btn.clicked.connect(self.controller.save_current_as_item)
        self.delete_template_btn.clicked.connect(self.controller.delete_selected_item)
        self.update_template_btn.clicked.connect(self.controller.update_current_item)
        self.backup_button.clicked.connect(self.controller.backup_all_states_action)
        self.restore_button.clicked.connect(self.controller.restore_states_from_backup_action)
        # template_tree 더블 클릭 시 로드 연결
        self.template_tree.itemDoubleClicked.connect(self.controller.load_selected_item)

        # .gitignore
        self.save_gitignore_btn.clicked.connect(self.controller.save_gitignore_settings)

        # 상태바
        self.auto_token_calc_check.stateChanged.connect(
            # 현재 활성화된 탭의 텍스트로 카운트 업데이트 (prompt_output 또는 final_prompt)
            lambda: self.controller.update_counts_for_text(
                self.final_prompt_tab.toPlainText() if self.mode == "Meta Prompt Builder" and hasattr(self, 'final_prompt_tab')
                else self.prompt_output_tab.toPlainText()
            )
        )
        # 텍스트 변경 시 카운트 업데이트 (prompt_output_tab 또는 final_prompt_tab)
        self.prompt_output_tab.textChanged.connect(
             lambda: self.controller.update_counts_for_text(self.prompt_output_tab.toPlainText())
        )
        if hasattr(self, 'final_prompt_tab'):
            self.final_prompt_tab.textChanged.connect(
                 lambda: self.controller.update_counts_for_text(self.final_prompt_tab.toPlainText())
            )
        # TODO: 다른 탭 (system, user 등) 변경 시에도 카운트 업데이트 필요시 연결

        # 메뉴 액션
        self.save_state_action.triggered.connect(self.controller.save_state_to_default)
        self.load_state_action.triggered.connect(self.controller.load_state_from_default)
        self.export_state_action.triggered.connect(self.controller.export_state_to_file)
        self.import_state_action.triggered.connect(self.controller.import_state_from_file)

        # 단축키
        # Ctrl+Return 프롬프트 생성
        shortcut_generate = QAction(self)
        shortcut_generate.setShortcut(QKeySequence("Ctrl+Return"))
        if self.mode == "Meta Prompt Builder":
             shortcut_generate.triggered.connect(self.controller.generate_meta_prompt)
        else:
             shortcut_generate.triggered.connect(self.controller.generate_prompt)
        self.addAction(shortcut_generate)

        # Ctrl+C (프롬프트 출력 탭 활성 시) 복사
        shortcut_copy = QAction(self)
        shortcut_copy.setShortcut(QKeySequence("Ctrl+C"))
        shortcut_copy.triggered.connect(self.on_copy_shortcut) # 내부 메서드 연결
        self.addAction(shortcut_copy)

    def _apply_initial_settings(self):
        """Applies initial settings like default system prompt."""
        # 기본 시스템 프롬프트 로드
        apply_default_system_prompt(self)

        # Meta Prompt Builder 모드일 경우 특정 프롬프트 로드 (선택적)
        if self.mode == "Meta Prompt Builder":
            # 예시: META_Prompt.md 로드
            meta_prompt_path_relative = os.path.join("prompts", "system", "META_Prompt.md")
            try:
                meta_prompt_path = get_resource_path(meta_prompt_path_relative)
                if os.path.exists(meta_prompt_path):
                    with open(meta_prompt_path, "r", encoding="utf-8") as f:
                        # system_tab (메타 프롬프트 템플릿 탭)에 로드
                        self.system_tab.setText(f.read())
            except Exception as e:
                print(f"Error loading default META prompt: {e}")

        # 초기 .gitignore 로드
        self.controller.load_gitignore_settings()

        # 초기 리소스 버튼 레이블 업데이트
        self.controller.update_buttons_label()

    def _restart_with_mode(self, new_mode: str):
        """Restarts the application with the specified mode."""
        self.close()
        # 새 MainWindow 인스턴스 생성 및 표시
        # TODO: 현재 상태를 저장하고 새 창에 전달하는 로직 추가 가능
        new_window = MainWindow(mode=new_mode)
        # new_window.resize(self.size()) # 이전 창 크기 유지
        new_window.show()
        # new_window.build_tabs.setCurrentIndex(0) # 첫 번째 탭 활성화

    def _toggle_mode(self):
        """Toggles between application modes."""
        if self.mode == "Code Enhancer Prompt Builder":
            self._restart_with_mode("Meta Prompt Builder")
        else:
            self._restart_with_mode("Code Enhancer Prompt Builder")

    # --- Public Methods (Controller에서 호출) ---

    def reset_state(self):
        """Resets internal state variables of the MainWindow."""
        self.current_project_folder = None
        self.last_generated_prompt = ""
        self.selected_files_data = []
        # 체크 상태 초기화 (ProxyModel에서 관리)
        if hasattr(self, 'checkable_proxy'):
            self.checkable_proxy.checked_files_dict.clear()
        # 윈도우 제목 리셋
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
            # last_generated_prompt는 저장하지 않음 (필요시 추가)
        }
        # Pydantic 모델로 변환 (유효성 검사 포함)
        try:
            app_state = AppState(**state_data)
            return app_state
        except Exception as e: # Pydantic ValidationError 등
             print(f"Error creating AppState model: {e}")
             # 오류 발생 시 기본 상태 반환 또는 None 반환
             return AppState(mode=self.mode) # 현재 모드만 유지한 기본 상태

    def set_current_state(self, state: AppState):
        """Sets the UI state based on the provided AppState model."""
        # 모드 전환 (필요시 재시작)
        if self.mode != state.mode:
            print(f"Mode mismatch during state load. Current: {self.mode}, Loaded: {state.mode}. Restarting...")
            self._restart_with_mode(state.mode)
            # 재시작 후 상태를 다시 로드해야 할 수 있음 (복잡도 증가)
            # 여기서는 일단 현재 인스턴스에 상태 적용 시도
            self.mode = state.mode # 모드 강제 변경 (UI 불일치 가능성)

        self.reset_state() # 기존 상태 초기화

        # 프로젝트 폴더 설정
        folder_name = None
        if state.project_folder and os.path.isdir(state.project_folder):
            self.current_project_folder = state.project_folder
            folder_name = os.path.basename(state.project_folder)
            self.project_folder_label.setText(f"현재 프로젝트 폴더: {state.project_folder}")
            # 파일 트리 업데이트
            if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                idx = self.dir_model.setRootPathFiltered(state.project_folder)
                self.tree_view.setRootIndex(self.checkable_proxy.mapFromSource(idx))
            self.status_bar.showMessage(f"Project Folder: {state.project_folder}")
        else:
             self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
             # 파일 트리 홈으로 리셋?
             home_path = os.path.expanduser("~")
             if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                 idx = self.dir_model.setRootPathFiltered(home_path)
                 self.tree_view.setRootIndex(self.checkable_proxy.mapFromSource(idx))


        # 텍스트 탭 설정
        self.system_tab.setText(state.system_prompt)
        self.user_tab.setText(state.user_prompt)
        # last_generated_prompt는 로드하지 않음

        # 체크 상태 복원
        if hasattr(self, 'checkable_proxy'):
            self.uncheck_all_files() # 먼저 모든 체크 해제
            # 체크 상태 설정 (setData 호출)
            for fpath in state.checked_files:
                 # toggle_file_check는 현재 상태를 토글하므로 직접 setData 호출 필요
                 src_index = self.dir_model.index(fpath)
                 if src_index.isValid():
                     proxy_index = self.checkable_proxy.mapFromSource(src_index)
                     if proxy_index.isValid():
                         self.checkable_proxy.setData(proxy_index, Qt.Checked, Qt.CheckStateRole)

        # .gitignore 로드 및 필터 갱신
        self.controller.load_gitignore_settings()

        # 윈도우 제목 업데이트
        self.update_window_title(folder_name)
        self.status_bar.showMessage("State loaded successfully!")


    def uncheck_all_files(self):
        """Unchecks all items in the file tree view."""
        # 이 로직은 CheckableProxyModel 또는 FileTreeController로 이동 고려
        if not hasattr(self, 'checkable_proxy'): return

        # ProxyModel의 내부 상태(checked_files_dict)를 직접 수정하고
        # 전체 뷰 갱신을 유도하는 것이 더 효율적일 수 있음
        # checked_paths_to_uncheck = list(self.checkable_proxy.checked_files_dict.keys())
        self.checkable_proxy.checked_files_dict.clear()

        # 뷰 갱신 (전체 모델 리셋 또는 dataChanged 시그널 발생)
        # self.checkable_proxy.invalidate() # 전체 모델 무효화 (비효율적일 수 있음)
        # 또는 각 항목에 대해 dataChanged 발생
        # TODO: 더 효율적인 방법 찾기 (예: 모델 리셋 후 재구성)
        # 임시: 루트부터 순회하며 setData 호출 (비효율적)
        root_proxy_index = self.tree_view.rootIndex()
        if root_proxy_index.isValid():
            self._recursive_uncheck(root_proxy_index)

        # for path in checked_paths_to_uncheck:
        #     src_index = self.dir_model.index(path)
        #     if src_index.isValid():
        #         proxy_index = self.checkable_proxy.mapFromSource(src_index)
        #         if proxy_index.isValid():
        #              self.checkable_proxy.dataChanged.emit(proxy_index, proxy_index, [Qt.CheckStateRole])


    def _recursive_uncheck(self, proxy_index: QModelIndex):
        """Helper method to recursively uncheck items via setData."""
        if not proxy_index.isValid(): return

        # 현재 항목 체크 해제 (setData 호출 -> 시그널 발생)
        current_state = self.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
        if current_state == Qt.Checked:
            # setData 호출 시 check_all_children이 재귀적으로 호출되므로,
            # 여기서 직접 setData를 호출하면 중복 및 비효율 발생 가능.
            # 대신 내부 상태만 변경하고 dataChanged 시그널만 발생시키는 것이 나을 수 있음.
            # self.checkable_proxy.setData(proxy_index, Qt.Unchecked, Qt.CheckStateRole)
            file_path = self.checkable_proxy.get_file_path_from_index(proxy_index)
            if file_path in self.checkable_proxy.checked_files_dict:
                del self.checkable_proxy.checked_files_dict[file_path]
            self.checkable_proxy.dataChanged.emit(proxy_index, proxy_index, [Qt.CheckStateRole])


        # 자식 항목 재귀 호출
        child_count = self.checkable_proxy.rowCount(proxy_index)
        for row in range(child_count):
            child_proxy_idx = self.checkable_proxy.index(row, 0, proxy_index)
            self._recursive_uncheck(child_proxy_idx)


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
            # TODO: 중복 이름 확인
            # TODO: 보호된 이름 사용 불가 처리
            from ui.widgets.tab_manager import is_tab_deletable
            if not is_tab_deletable(new_name):
                 QMessageBox.warning(self, "경고", f"'{new_name}'은(는) 사용할 수 없는 탭 이름입니다.")
                 return

            new_tab = CustomTextEdit()
            new_tab.setPlaceholderText(f"{new_name} 내용 입력...")
            # "+" 탭 바로 앞에 삽입
            plus_tab_index = -1
            for i in range(self.build_tabs.count()):
                if self.build_tabs.tabText(i) == "+":
                    plus_tab_index = i
                    break
            if plus_tab_index != -1:
                 self.build_tabs.insertTab(plus_tab_index, new_tab, new_name)
                 self.build_tabs.setCurrentIndex(plus_tab_index) # 새로 추가된 탭 활성화
            else: # "+" 탭 못 찾으면 맨 끝에 추가 (예외 상황)
                 self.build_tabs.addTab(new_tab, new_name)
                 self.build_tabs.setCurrentIndex(self.build_tabs.count() - 1)

        elif ok:
             QMessageBox.warning(self, "경고", "탭 이름은 비워둘 수 없습니다.")


    # --- Event Handlers ---

    def on_copy_shortcut(self):
        """Handles Ctrl+C shortcut, copies if prompt output tab is active."""
        # 현재 활성화된 탭 위젯 확인
        current_widget = self.build_tabs.currentWidget()
        # 프롬프트 출력 탭 또는 최종 프롬프트 탭인 경우 복사 실행
        if current_widget == self.prompt_output_tab or \
           (hasattr(self, 'final_prompt_tab') and current_widget == self.final_prompt_tab):
            self.controller.copy_to_clipboard()
        else:
            # 다른 탭이 활성화된 경우, 기본 복사 동작 수행 (선택된 텍스트 복사)
            if hasattr(current_widget, 'copy'):
                 current_widget.copy()


    def on_tree_view_context_menu(self, position):
        """Handles context menu requests on the file tree view."""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        # 프록시 인덱스에서 파일 경로 가져오기
        file_path = self.checkable_proxy.get_file_path_from_index(index)
        if not file_path:
            return

        menu = QMenu()

        # 액션 추가
        rename_action = menu.addAction("이름 변경")
        delete_action = menu.addAction("삭제")
        # TODO: 새 파일/폴더 만들기, 경로 복사 등 추가 가능

        action = menu.exec_(self.tree_view.viewport().mapToGlobal(position))

        # 액션 처리 (컨트롤러 메서드 호출)
        if action == rename_action:
            self.controller.rename_item(file_path)
        elif action == delete_action:
            self.controller.delete_item(file_path)


    def on_selection_changed_handler(self, selected: QItemSelection, deselected: QItemSelection):
        """Handles selection changes in the file tree view to toggle check state."""
        # QItemSelectionModel::selectionChanged 시그널은 QItemSelection을 인자로 받음
        # selected.indexes()를 사용하여 선택된 인덱스 목록 가져오기

        # 클릭/드래그 시 여러 항목이 선택될 수 있으므로, 모든 선택된 인덱스 처리
        # 하지만 일반적인 클릭 동작은 하나의 항목만 선택/해제하므로 첫 번째 인덱스만 처리해도 무방할 수 있음
        # 여기서는 첫 번째 인덱스만 처리하여 클릭 시 토글 동작 구현
        indexes = selected.indexes()
        if not indexes:
            return

        proxy_index = indexes[0] # 첫 번째 선택된 인덱스
        if proxy_index.column() != 0: return # 첫 번째 컬럼(이름/체크박스)만 처리

        # 체크 상태 토글 (Controller에게 위임하거나 ProxyModel 직접 조작)
        # Controller에게 위임하는 방식:
        # file_path = self.checkable_proxy.get_file_path_from_index(proxy_index)
        # if file_path:
        #     self.controller.toggle_file_check(file_path) # Controller의 토글 메서드 호출

        # ProxyModel 직접 조작 방식 (기존 유지):
        current_state = self.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
        new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
        # setData 호출 시 내부적으로 ensure_loaded, check_all_children, expand_index_recursively 등이 호출됨
        self.checkable_proxy.setData(proxy_index, new_state, Qt.CheckStateRole)

        # deselected 처리는 복잡성을 증가시키므로 여기서는 생략
