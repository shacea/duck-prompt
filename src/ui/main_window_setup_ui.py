import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox, QAbstractItemView, QMenuBar,
    QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QComboBox,
    QFrame, QLineEdit, QGroupBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# MainWindow 타입 힌트
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

# 모델 및 위젯 import
from .models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
from .widgets.custom_text_edit import CustomTextEdit
from .widgets.custom_tab_bar import CustomTabBar

def create_menu_bar(mw: 'MainWindow'):
    """Creates the main menu bar."""
    mw.menubar = QMenuBar(mw) # 멤버 변수로 저장
    mw.setMenuBar(mw.menubar)

    # 파일 메뉴 (추가)
    file_menu = mw.menubar.addMenu("파일")
    mw.settings_action = QAction("환경 설정...", mw) # 설정 액션 추가
    file_menu.addAction(mw.settings_action)
    file_menu.addSeparator()
    # TODO: Add Exit action if needed
    # exit_action = QAction("종료", mw)
    # exit_action.triggered.connect(mw.close)
    # file_menu.addAction(exit_action)


    # 모드 메뉴
    mode_menu = mw.menubar.addMenu("모드")
    switch_to_code_action = QAction("코드 강화 빌더로 전환", mw)
    switch_to_meta_action = QAction("메타 프롬프트 빌더로 전환", mw)
    switch_to_code_action.triggered.connect(lambda: mw._restart_with_mode("Code Enhancer Prompt Builder"))
    switch_to_meta_action.triggered.connect(lambda: mw._restart_with_mode("Meta Prompt Builder"))
    mode_menu.addAction(switch_to_code_action)
    mode_menu.addAction(switch_to_meta_action)

    # 상태 메뉴
    state_menu = mw.menubar.addMenu("상태")
    mw.save_state_action = QAction("상태 저장(기본)", mw)
    mw.load_state_action = QAction("상태 불러오기(기본)", mw)
    mw.export_state_action = QAction("상태 내보내기", mw)
    mw.import_state_action = QAction("상태 가져오기", mw)
    state_menu.addAction(mw.save_state_action)
    state_menu.addAction(mw.load_state_action)
    state_menu.addAction(mw.export_state_action)
    state_menu.addAction(mw.import_state_action)

    # 도움말 메뉴
    help_menu = mw.menubar.addMenu("도움말")
    open_readme_action = QAction("README 열기", mw)
    open_readme_action.triggered.connect(mw._open_readme)
    help_menu.addAction(open_readme_action)

def create_widgets(mw: 'MainWindow'):
    """Creates the main widgets used in the window."""
    # --- 상단 버튼 및 레이블 ---
    mw.mode_toggle_btn = QPushButton("🔄 모드 전환")
    mw.reset_program_btn = QPushButton("🗑️ 전체 프로그램 리셋")
    mw.select_project_btn = QPushButton("📁 프로젝트 폴더 선택")
    for btn in [mw.mode_toggle_btn, mw.reset_program_btn, mw.select_project_btn]:
        btn.setFixedHeight(30)
    mw.project_folder_label = QLabel("현재 프로젝트 폴더: (선택 안 됨)")
    font_lbl = mw.project_folder_label.font()
    font_lbl.setPointSize(10)
    font_lbl.setBold(True)
    mw.project_folder_label.setFont(font_lbl)

    # --- 파일 탐색기 (왼쪽 상단) ---
    mw.dir_model = FilteredFileSystemModel()
    mw.tree_view = QTreeView()
    project_folder_getter = lambda: mw.current_project_folder
    mw.checkable_proxy = CheckableProxyModel(mw.dir_model, project_folder_getter, mw.fs_service, mw.tree_view)
    mw.checkable_proxy.setSourceModel(mw.dir_model)
    mw.tree_view.setModel(mw.checkable_proxy)
    mw.tree_view.setColumnWidth(0, 250)
    mw.tree_view.hideColumn(1); mw.tree_view.hideColumn(2); mw.tree_view.hideColumn(3)
    mw.tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
    mw.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
    mw.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
    mw.tree_view.clicked.connect(lambda index: mw.checkable_proxy.setData(index,
                                                                          Qt.Checked if mw.checkable_proxy.data(index, Qt.CheckStateRole) == Qt.Unchecked else Qt.Unchecked,
                                                                          Qt.CheckStateRole))

    # --- 리소스 관리 (왼쪽 하단) ---
    mw.resource_manager_group = QGroupBox("리소스 관리") # GroupBox로 감싸기
    resource_manager_layout = QVBoxLayout()
    resource_manager_layout.setContentsMargins(5, 5, 5, 5)
    resource_manager_layout.setSpacing(5)

    mw.resource_mode_combo = QComboBox()
    mw.resource_mode_combo.addItems(["프롬프트", "상태"])
    mw.template_tree = QTreeWidget()
    mw.template_tree.setHeaderHidden(True)
    mw.load_selected_template_btn = QPushButton("📥 선택 불러오기")
    mw.save_as_template_btn = QPushButton("💾 현재 내용으로 저장")
    mw.template_type_label = QLabel("저장 타입:")
    mw.template_type_combo = QComboBox()
    mw.template_type_combo.addItems(["시스템", "사용자"])
    mw.delete_template_btn = QPushButton("❌ 선택 삭제")
    mw.update_template_btn = QPushButton("🔄 현재 내용 업데이트")
    mw.backup_button = QPushButton("📦 모든 상태 백업")
    mw.restore_button = QPushButton("🔙 백업에서 상태 복원")

    # 리소스 관리 레이아웃 구성
    resource_manager_layout.addWidget(QLabel("리소스 타입 선택:"))
    resource_manager_layout.addWidget(mw.resource_mode_combo)
    resource_manager_layout.addWidget(QLabel("아래에서 로드/저장할 리소스 선택:"))
    resource_manager_layout.addWidget(mw.template_tree, 1) # Tree 위젯이 공간 차지하도록 stretch=1

    tm_button_layout = QVBoxLayout()
    tm_button_layout.setSpacing(5)
    first_row = QHBoxLayout(); first_row.addWidget(mw.load_selected_template_btn); tm_button_layout.addLayout(first_row)
    second_row = QHBoxLayout(); second_row.addWidget(mw.template_type_label); second_row.addWidget(mw.template_type_combo); second_row.addWidget(mw.save_as_template_btn); tm_button_layout.addLayout(second_row)
    third_row = QHBoxLayout(); third_row.addWidget(mw.delete_template_btn); third_row.addWidget(mw.update_template_btn); tm_button_layout.addLayout(third_row)
    fourth_row = QHBoxLayout(); fourth_row.addWidget(mw.backup_button); fourth_row.addWidget(mw.restore_button); tm_button_layout.addLayout(fourth_row)
    resource_manager_layout.addLayout(tm_button_layout)
    mw.resource_manager_group.setLayout(resource_manager_layout)


    # --- 탭 위젯 (오른쪽) ---
    mw.build_tabs = QTabWidget()
    custom_tab_bar = CustomTabBar(mw.build_tabs, mw)
    mw.build_tabs.setTabBar(custom_tab_bar)

    system_tab_label = "메타 프롬프트 템플릿" if mw.mode == "Meta Prompt Builder" else "시스템"
    user_tab_label = "메타 사용자 입력" if mw.mode == "Meta Prompt Builder" else "사용자"
    prompt_output_label = "메타 프롬프트 출력" if mw.mode == "Meta Prompt Builder" else "프롬프트 출력"

    mw.system_tab = CustomTextEdit()
    mw.system_tab.setPlaceholderText(f"{system_tab_label} 내용 입력...")
    mw.build_tabs.addTab(mw.system_tab, system_tab_label)

    mw.user_tab = CustomTextEdit()
    mw.user_tab.setPlaceholderText(f"{user_tab_label} 내용 입력...")
    mw.build_tabs.addTab(mw.user_tab, user_tab_label)

    if mw.mode != "Meta Prompt Builder":
        mw.dir_structure_tab = CustomTextEdit()
        mw.dir_structure_tab.setReadOnly(True)
        mw.build_tabs.addTab(mw.dir_structure_tab, "파일 트리")

    mw.prompt_output_tab = CustomTextEdit()
    mw.prompt_output_tab.setFont(QFont("Consolas", 10))
    mw.prompt_output_tab.setStyleSheet("QTextEdit { padding: 10px; }")
    mw.build_tabs.addTab(mw.prompt_output_tab, prompt_output_label)

    if mw.mode != "Meta Prompt Builder":
        mw.xml_input_tab = CustomTextEdit()
        mw.xml_input_tab.setPlaceholderText("XML 내용 입력...")
        mw.build_tabs.addTab(mw.xml_input_tab, "XML 입력")

    if mw.mode == "Meta Prompt Builder":
        mw.meta_prompt_tab = CustomTextEdit()
        mw.meta_prompt_tab.setPlaceholderText("메타 프롬프트 내용...")
        mw.build_tabs.addTab(mw.meta_prompt_tab, "메타 프롬프트")

        mw.user_prompt_tab = CustomTextEdit()
        mw.user_prompt_tab.setPlaceholderText("사용자 프롬프트 내용 입력...")
        mw.build_tabs.addTab(mw.user_prompt_tab, "사용자 프롬프트")

        mw.final_prompt_tab = CustomTextEdit()
        mw.final_prompt_tab.setFont(QFont("Consolas", 10))
        mw.final_prompt_tab.setStyleSheet("QTextEdit { padding: 10px; }")
        mw.build_tabs.addTab(mw.final_prompt_tab, "최종 프롬프트")

    # --- 실행 버튼 (오른쪽 상단) ---
    copy_btn_label = "📋 메타 프롬프트 복사" if mw.mode == "Meta Prompt Builder" else "📋 클립보드에 복사"
    if mw.mode != "Meta Prompt Builder":
        mw.generate_tree_btn = QPushButton("🌳 트리 생성")
        mw.generate_btn = QPushButton("✨ 프롬프트 생성")
        mw.copy_btn = QPushButton(copy_btn_label)
        mw.run_xml_parser_btn = QPushButton("▶️ XML 파서 실행")
        mw.generate_all_btn = QPushButton("⚡️ 한번에 실행")
        mw.run_buttons = [mw.generate_tree_btn, mw.generate_btn, mw.copy_btn, mw.run_xml_parser_btn, mw.generate_all_btn]
    else:
        mw.generate_btn = QPushButton("🚀 메타 프롬프트 생성")
        mw.copy_btn = QPushButton(copy_btn_label)
        mw.generate_final_prompt_btn = QPushButton("🚀 최종 프롬프트 생성")
        mw.run_buttons = [mw.generate_btn, mw.copy_btn, mw.generate_final_prompt_btn]

    # --- .gitignore 뷰어/편집기 (제거됨) ---
    # mw.gitignore_tabwidget = QTabWidget()
    # mw.gitignore_edit = CustomTextEdit()
    # mw.gitignore_edit.setPlaceholderText(".gitignore 내용...")
    # mw.save_gitignore_btn = QPushButton("💾 .gitignore 저장")

    # --- 상태 표시줄 위젯 (create_status_bar에서 사용) ---
    mw.char_count_label = QLabel("Chars: 0")
    mw.token_count_label = QLabel("토큰 계산: -")
    mw.llm_combo = QComboBox()
    mw.llm_combo.addItems(["Gemini", "Claude", "GPT"])
    mw.model_name_input = QLineEdit()
    mw.model_name_input.setPlaceholderText("모델명 입력 (예: gemini-1.5-pro-latest)")


def create_layout(mw: 'MainWindow'):
    """Creates the layout and arranges widgets."""
    central_widget = QWidget()
    mw.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(5, 5, 5, 5)
    main_layout.setSpacing(5)

    # --- 상단 레이아웃 ---
    top_button_container = QWidget()
    top_button_layout = QHBoxLayout(top_button_container)
    top_button_layout.setSpacing(10)
    top_button_layout.setContentsMargins(0, 0, 0, 0)
    top_button_layout.addWidget(mw.mode_toggle_btn)
    top_button_layout.addWidget(mw.reset_program_btn)
    top_button_layout.addWidget(mw.select_project_btn)
    top_button_layout.addStretch(1)

    top_layout_wrapper = QVBoxLayout()
    top_layout_wrapper.setSpacing(5)
    top_layout_wrapper.setContentsMargins(0, 0, 0, 0)
    top_layout_wrapper.addWidget(top_button_container)
    top_layout_wrapper.addWidget(mw.project_folder_label)
    main_layout.addLayout(top_layout_wrapper)

    # --- 중앙 스플리터 (왼쪽 영역 | 오른쪽 영역) ---
    mw.center_splitter = QSplitter(Qt.Horizontal)

    # --- 왼쪽 영역 (파일 트리 + 리소스 관리) ---
    left_side_widget = QWidget()
    left_side_layout = QVBoxLayout(left_side_widget)
    left_side_layout.setContentsMargins(2, 2, 2, 2)
    left_side_layout.setSpacing(5)
    left_side_layout.addWidget(mw.tree_view, 3) # 파일 트리가 더 많은 공간 차지 (stretch=3)
    left_side_layout.addWidget(mw.resource_manager_group, 2) # 리소스 관리 (stretch=2)
    mw.center_splitter.addWidget(left_side_widget)

    # --- 오른쪽 영역 (실행 버튼 + 탭 위젯) ---
    right_side_widget = QWidget()
    right_side_layout = QVBoxLayout(right_side_widget)
    right_side_layout.setContentsMargins(0, 0, 0, 0)
    right_side_layout.setSpacing(0)

    run_buttons_container = QWidget()
    run_layout = QHBoxLayout(run_buttons_container)
    run_layout.setContentsMargins(5, 5, 5, 5)
    run_layout.setSpacing(10)
    run_layout.setAlignment(Qt.AlignLeft)
    for btn in mw.run_buttons:
        run_layout.addWidget(btn)

    line_frame = QFrame()
    line_frame.setFrameShape(QFrame.HLine)
    line_frame.setFrameShadow(QFrame.Sunken)

    right_side_layout.addWidget(run_buttons_container)
    right_side_layout.addWidget(line_frame)
    right_side_layout.addWidget(mw.build_tabs) # 탭 위젯이 남은 공간 모두 차지
    mw.center_splitter.addWidget(right_side_widget)

    main_layout.addWidget(mw.center_splitter) # 중앙 스플리터 추가

    # --- 하단 스플리터 및 .gitignore 관련 위젯 제거 ---
    # mw.bottom_splitter = QSplitter(Qt.Horizontal)
    # ... (template_manager_frame, gitignore_frame 등 제거) ...
    # main_layout.addWidget(mw.bottom_splitter, stretch=2) # 제거

    # 초기 스플리터 크기 설정 (비율 조정)
    mw.center_splitter.setStretchFactor(0, 1) # 왼쪽 영역 비율
    mw.center_splitter.setStretchFactor(1, 3) # 오른쪽 영역 비율


def create_status_bar(mw: 'MainWindow'):
    """Creates the status bar with character and token counts, and model selection."""
    mw.status_bar = QStatusBar()
    mw.setStatusBar(mw.status_bar)

    # --- Right side of status bar (permanent widgets) ---
    status_widget = QWidget()
    status_layout = QHBoxLayout(status_widget)
    status_layout.setContentsMargins(5, 2, 5, 2)
    status_layout.setSpacing(10)

    status_layout.addWidget(mw.char_count_label)

    # Token calculation section
    status_layout.addWidget(QLabel("Model:"))
    status_layout.addWidget(mw.llm_combo)
    mw.llm_combo.setFixedWidth(80)

    status_layout.addWidget(mw.model_name_input)
    mw.model_name_input.setMinimumWidth(200)

    status_layout.addWidget(mw.token_count_label)

    status_layout.addStretch(1)

    mw.status_bar.addPermanentWidget(status_widget)
