
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox, QAbstractItemView, QMenuBar,
    QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QComboBox,
    QFrame, QLineEdit, QGroupBox, QSpacerItem, QSizePolicy, QListWidget
)
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import Qt

# MainWindow 타입 힌트
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

# 모델 및 위젯 import
from .models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
from .widgets.custom_text_edit import CustomTextEdit
from .widgets.custom_tab_bar import CustomTabBar
from utils.helpers import get_resource_path
from .widgets.check_box_delegate import CheckBoxDelegate

def create_menu_bar(mw: 'MainWindow'):
    """Creates the main menu bar."""
    mw.menubar = QMenuBar(mw)
    mw.setMenuBar(mw.menubar)

    file_menu = mw.menubar.addMenu("파일")
    mw.settings_action = QAction("환경 설정...", mw)
    file_menu.addAction(mw.settings_action)
    file_menu.addSeparator()

    mode_menu = mw.menubar.addMenu("모드")
    switch_to_code_action = QAction("코드 강화 빌더로 전환", mw)
    switch_to_meta_action = QAction("메타 프롬프트 빌더로 전환", mw)
    switch_to_code_action.triggered.connect(lambda: mw._restart_with_mode("Code Enhancer Prompt Builder"))
    switch_to_meta_action.triggered.connect(lambda: mw._restart_with_mode("Meta Prompt Builder"))
    mode_menu.addAction(switch_to_code_action)
    mode_menu.addAction(switch_to_meta_action)

    state_menu = mw.menubar.addMenu("상태")
    mw.save_state_action = QAction("상태 저장(기본)", mw)
    mw.load_state_action = QAction("상태 불러오기(기본)", mw)
    mw.export_state_action = QAction("상태 내보내기", mw)
    mw.import_state_action = QAction("상태 가져오기", mw)
    state_menu.addAction(mw.save_state_action)
    state_menu.addAction(mw.load_state_action)
    state_menu.addAction(mw.export_state_action)
    state_menu.addAction(mw.import_state_action)

    help_menu = mw.menubar.addMenu("도움말")
    open_readme_action = QAction("README 열기", mw)
    open_readme_action.triggered.connect(mw._open_readme)
    help_menu.addAction(open_readme_action)

def create_widgets(mw: 'MainWindow'):
    """Creates the main widgets used in the window."""
    # --- OS별 기본 폰트 설정 ---
    default_font = QFont()
    font_family_name = ""
    if sys.platform == "win32":
        try:
            font_path = get_resource_path("fonts/malgun.ttf")
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                family = QFontDatabase.applicationFontFamilies(font_id)[0]
                print(f"Loaded custom font: {family} from {font_path}")
                default_font = QFont(family, 10)
                font_family_name = family
            else:
                print(f"Failed to load custom font from {font_path}. Using system default.")
                default_font.setFamily("Malgun Gothic")
                default_font.setPointSize(10)
                font_family_name = "Malgun Gothic (Fallback)"
        except Exception as e:
            print(f"Error loading custom font: {e}. Using system default.")
            default_font.setFamily("Malgun Gothic")
            default_font.setPointSize(10)
            font_family_name = "Malgun Gothic (Exception Fallback)"
    elif sys.platform == "darwin":
        default_font.setFamily("Apple SD Gothic Neo")
        default_font.setPointSize(11)
        font_family_name = "Apple SD Gothic Neo"
    else:
        default_font.setStyleHint(QFont.SansSerif)
        default_font.setPointSize(10)
        font_family_name = "System Default Sans-Serif"
    print(f"Applying default font: {font_family_name}, Size: {default_font.pointSize()}")

    # --- 상단 버튼 및 레이블 ---
    mw.mode_toggle_btn = QPushButton("🔄 모드 전환")
    mw.reset_program_btn = QPushButton("🗑️ 전체 프로그램 리셋")
    mw.select_project_btn = QPushButton("📁 프로젝트 폴더 선택")
    for btn in [mw.mode_toggle_btn, mw.reset_program_btn, mw.select_project_btn]:
        btn.setFixedHeight(30)
    mw.project_folder_label = QLabel("현재 프로젝트 폴더: (선택 안 됨)")
    font_lbl = mw.project_folder_label.font()
    font_lbl.setPointSize(10); font_lbl.setBold(True)
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
    mw.tree_view.setItemDelegateForColumn(0, CheckBoxDelegate(mw.tree_view))

    # --- 리소스 관리 (왼쪽 중간) ---
    mw.resource_manager_group = QGroupBox("리소스 관리")
    resource_manager_layout = QVBoxLayout()
    resource_manager_layout.setContentsMargins(5, 5, 5, 5); resource_manager_layout.setSpacing(5)
    mw.resource_mode_combo = QComboBox(); mw.resource_mode_combo.addItems(["프롬프트", "상태"])
    mw.template_tree = QTreeWidget(); mw.template_tree.setHeaderHidden(True)
    mw.load_selected_template_btn = QPushButton("📥 선택 불러오기")
    mw.save_as_template_btn = QPushButton("💾 현재 내용으로 저장")
    mw.template_type_label = QLabel("저장 타입:")
    mw.template_type_combo = QComboBox(); mw.template_type_combo.addItems(["시스템", "사용자"])
    mw.delete_template_btn = QPushButton("❌ 선택 삭제")
    mw.update_template_btn = QPushButton("🔄 현재 내용 업데이트")
    mw.backup_button = QPushButton("📦 모든 상태 백업")
    mw.restore_button = QPushButton("🔙 백업에서 상태 복원")
    resource_manager_layout.addWidget(QLabel("리소스 타입 선택:"))
    resource_manager_layout.addWidget(mw.resource_mode_combo)
    resource_manager_layout.addWidget(QLabel("아래에서 로드/저장할 리소스 선택:"))
    resource_manager_layout.addWidget(mw.template_tree, 1)
    tm_button_layout = QVBoxLayout(); tm_button_layout.setSpacing(5)
    first_row = QHBoxLayout(); first_row.addWidget(mw.load_selected_template_btn); tm_button_layout.addLayout(first_row)
    second_row = QHBoxLayout(); second_row.addWidget(mw.template_type_label); second_row.addWidget(mw.template_type_combo); second_row.addWidget(mw.save_as_template_btn); tm_button_layout.addLayout(second_row)
    third_row = QHBoxLayout(); third_row.addWidget(mw.delete_template_btn); third_row.addWidget(mw.update_template_btn); tm_button_layout.addLayout(third_row)
    fourth_row = QHBoxLayout(); fourth_row.addWidget(mw.backup_button); fourth_row.addWidget(mw.restore_button); tm_button_layout.addLayout(fourth_row)
    resource_manager_layout.addLayout(tm_button_layout)
    mw.resource_manager_group.setLayout(resource_manager_layout)

    # --- 첨부 파일 관리 (왼쪽 하단) ---
    mw.attachment_group = QGroupBox("첨부 파일")
    attachment_layout = QVBoxLayout()
    attachment_layout.setContentsMargins(5, 5, 5, 5); attachment_layout.setSpacing(5)
    attachment_button_layout = QHBoxLayout()
    mw.attach_file_btn = QPushButton("📎 파일 첨부")
    mw.paste_clipboard_btn = QPushButton("📋 클립보드 붙여넣기")
    mw.remove_attachment_btn = QPushButton("➖ 선택 제거")
    attachment_button_layout.addWidget(mw.attach_file_btn)
    attachment_button_layout.addWidget(mw.paste_clipboard_btn)
    attachment_button_layout.addWidget(mw.remove_attachment_btn)
    attachment_button_layout.addStretch()
    mw.attachment_list_widget = QListWidget() # 리스트 위젯 생성
    mw.attachment_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection) # 다중 선택 가능
    attachment_layout.addLayout(attachment_button_layout)
    attachment_layout.addWidget(mw.attachment_list_widget, 1) # 리스트 위젯이 공간 차지
    mw.attachment_group.setLayout(attachment_layout)
    # Code Enhancer 모드에서만 보이도록 설정 (초기 상태)
    mw.attachment_group.setVisible(mw.mode == "Code Enhancer Prompt Builder")


    # --- 탭 위젯 (오른쪽) ---
    mw.build_tabs = QTabWidget()
    custom_tab_bar = CustomTabBar(mw.build_tabs, mw)
    mw.build_tabs.setTabBar(custom_tab_bar)
    system_tab_label = "메타 프롬프트 템플릿" if mw.mode == "Meta Prompt Builder" else "시스템"
    user_tab_label = "메타 사용자 입력" if mw.mode == "Meta Prompt Builder" else "사용자"
    prompt_output_label = "메타 프롬프트 출력" if mw.mode == "Meta Prompt Builder" else "프롬프트 출력"
    mw.system_tab = CustomTextEdit(); mw.system_tab.setPlaceholderText(f"{system_tab_label} 내용 입력..."); mw.system_tab.setFont(default_font); mw.build_tabs.addTab(mw.system_tab, system_tab_label)
    mw.user_tab = CustomTextEdit(); mw.user_tab.setPlaceholderText(f"{user_tab_label} 내용 입력..."); mw.user_tab.setFont(default_font); mw.build_tabs.addTab(mw.user_tab, user_tab_label)
    if mw.mode != "Meta Prompt Builder":
        mw.dir_structure_tab = CustomTextEdit(); mw.dir_structure_tab.setReadOnly(True); mw.dir_structure_tab.setFont(default_font); mw.build_tabs.addTab(mw.dir_structure_tab, "파일 트리")
    mw.prompt_output_tab = CustomTextEdit()
    output_font = QFont("Consolas", 10) if sys.platform == "win32" else QFont("Monaco", 11) if sys.platform == "darwin" else QFont("Monospace", 10); output_font.setStyleHint(QFont.Monospace)
    mw.prompt_output_tab.setFont(output_font); mw.prompt_output_tab.setStyleSheet("QTextEdit { padding: 10px; }"); mw.build_tabs.addTab(mw.prompt_output_tab, prompt_output_label)
    if mw.mode != "Meta Prompt Builder":
        mw.xml_input_tab = CustomTextEdit(); mw.xml_input_tab.setPlaceholderText("XML 내용 입력..."); mw.xml_input_tab.setFont(default_font); mw.build_tabs.addTab(mw.xml_input_tab, "XML 입력")
        mw.summary_tab = CustomTextEdit(); mw.summary_tab.setPlaceholderText("Gemini 응답 요약..."); mw.summary_tab.setReadOnly(True); mw.summary_tab.setFont(default_font); mw.build_tabs.addTab(mw.summary_tab, "Summary")
    if mw.mode == "Meta Prompt Builder":
        mw.meta_prompt_tab = CustomTextEdit(); mw.meta_prompt_tab.setPlaceholderText("메타 프롬프트 내용..."); mw.meta_prompt_tab.setFont(default_font); mw.build_tabs.addTab(mw.meta_prompt_tab, "메타 프롬프트")
        mw.user_prompt_tab = CustomTextEdit(); mw.user_prompt_tab.setPlaceholderText("사용자 프롬프트 내용 입력..."); mw.user_prompt_tab.setFont(default_font); mw.build_tabs.addTab(mw.user_prompt_tab, "사용자 프롬프트")
        mw.final_prompt_tab = CustomTextEdit(); mw.final_prompt_tab.setFont(output_font); mw.final_prompt_tab.setStyleSheet("QTextEdit { padding: 10px; }"); mw.build_tabs.addTab(mw.final_prompt_tab, "최종 프롬프트")

    # --- 실행 버튼 (오른쪽 상단) ---
    copy_btn_label = "📋 메타 프롬프트 복사" if mw.mode == "Meta Prompt Builder" else "📋 클립보드에 복사"
    if mw.mode != "Meta Prompt Builder":
        mw.generate_tree_btn = QPushButton("🌳 트리 생성")
        mw.generate_btn = QPushButton("✨ 프롬프트 생성")
        mw.send_to_gemini_btn = QPushButton("♊ Gemini로 전송")
        mw.copy_btn = QPushButton(copy_btn_label)
        mw.run_xml_parser_btn = QPushButton("▶️ XML 파서 실행")
        mw.generate_all_btn = QPushButton("⚡️ 한번에 실행")
        mw.run_buttons = [mw.generate_tree_btn, mw.generate_btn, mw.send_to_gemini_btn, mw.copy_btn, mw.run_xml_parser_btn, mw.generate_all_btn]
    else:
        mw.generate_btn = QPushButton("🚀 메타 프롬프트 생성")
        mw.copy_btn = QPushButton(copy_btn_label)
        mw.generate_final_prompt_btn = QPushButton("🚀 최종 프롬프트 생성")
        mw.run_buttons = [mw.generate_btn, mw.copy_btn, mw.generate_final_prompt_btn]

    # --- 상태 표시줄 위젯 ---
    mw.char_count_label = QLabel("Chars: 0")
    mw.token_count_label = QLabel("토큰 계산: -")
    mw.api_time_label = QLabel("API 시간: -") # API 시간 표시 라벨 추가

    # --- LLM 관련 위젯 (상단으로 이동 예정) ---
    mw.llm_combo = QComboBox(); mw.llm_combo.addItems(["Gemini", "Claude", "GPT"])
    mw.model_name_combo = QComboBox(); mw.model_name_combo.setEditable(True); mw.model_name_combo.setInsertPolicy(QComboBox.NoInsert)
    mw.gemini_temp_label = QLabel("Temp:")
    mw.gemini_temp_edit = QLineEdit(); mw.gemini_temp_edit.setFixedWidth(40); mw.gemini_temp_edit.setPlaceholderText("0.0")
    mw.gemini_thinking_label = QLabel("Thinking:")
    mw.gemini_thinking_checkbox = QCheckBox()
    mw.gemini_budget_label = QLabel("Budget:")
    mw.gemini_budget_edit = QLineEdit(); mw.gemini_budget_edit.setFixedWidth(60); mw.gemini_budget_edit.setPlaceholderText("24576")
    mw.gemini_search_label = QLabel("Search:")
    mw.gemini_search_checkbox = QCheckBox()
    # Gemini 파라미터 위젯 그룹화 (상단 이동용)
    mw.gemini_param_widget = QWidget()
    gemini_param_layout = QHBoxLayout(mw.gemini_param_widget)
    gemini_param_layout.setContentsMargins(0, 0, 0, 0); gemini_param_layout.setSpacing(5)
    gemini_param_layout.addWidget(mw.gemini_temp_label); gemini_param_layout.addWidget(mw.gemini_temp_edit)
    gemini_param_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
    gemini_param_layout.addWidget(mw.gemini_thinking_label); gemini_param_layout.addWidget(mw.gemini_thinking_checkbox)
    gemini_param_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
    gemini_param_layout.addWidget(mw.gemini_budget_label); gemini_param_layout.addWidget(mw.gemini_budget_edit)
    gemini_param_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
    gemini_param_layout.addWidget(mw.gemini_search_label); gemini_param_layout.addWidget(mw.gemini_search_checkbox)
    mw.gemini_param_widget.setVisible(mw.llm_combo.currentText() == "Gemini") # 초기 가시성 설정


def create_layout(mw: 'MainWindow'):
    """Creates the layout and arranges widgets."""
    central_widget = QWidget()
    mw.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(5, 2, 5, 5); main_layout.setSpacing(2)

    # --- 상단 레이아웃 (버튼 + 프로젝트 경로 + LLM 컨트롤) ---
    top_layout_wrapper = QVBoxLayout(); top_layout_wrapper.setSpacing(2); top_layout_wrapper.setContentsMargins(0, 0, 0, 0)

    # 상단 버튼 행
    top_button_container = QWidget()
    top_button_layout = QHBoxLayout(top_button_container)
    top_button_layout.setSpacing(10); top_button_layout.setContentsMargins(0, 0, 0, 0)
    top_button_layout.addWidget(mw.mode_toggle_btn)
    top_button_layout.addWidget(mw.reset_program_btn)
    top_button_layout.addWidget(mw.select_project_btn)
    top_button_layout.addStretch(1)
    top_layout_wrapper.addWidget(top_button_container)

    # 프로젝트 경로 행
    top_layout_wrapper.addWidget(mw.project_folder_label)

    # LLM 컨트롤 행 (새로 추가)
    llm_controls_container = QWidget()
    llm_controls_layout = QHBoxLayout(llm_controls_container)
    llm_controls_layout.setContentsMargins(0, 5, 0, 5); llm_controls_layout.setSpacing(10) # 상하 여백 추가
    llm_controls_layout.addWidget(QLabel("Model:"))
    llm_controls_layout.addWidget(mw.llm_combo); mw.llm_combo.setFixedWidth(80)
    llm_controls_layout.addWidget(mw.model_name_combo); mw.model_name_combo.setMinimumWidth(180)
    llm_controls_layout.addWidget(mw.gemini_param_widget) # Gemini 파라미터 그룹 위젯 추가
    llm_controls_layout.addStretch(1)
    top_layout_wrapper.addWidget(llm_controls_container)

    main_layout.addLayout(top_layout_wrapper, 0) # 상단 전체 레이아웃 추가

    # --- 중앙 스플리터 ---
    mw.center_splitter = QSplitter(Qt.Horizontal)

    # --- 왼쪽 영역 (파일 트리 + 리소스 관리 + 첨부 파일) ---
    left_side_widget = QWidget()
    left_side_layout = QVBoxLayout(left_side_widget)
    left_side_layout.setContentsMargins(2, 2, 2, 2); left_side_layout.setSpacing(5)
    left_side_layout.addWidget(mw.tree_view, 3) # 파일 트리 (비율 3)
    left_side_layout.addWidget(mw.resource_manager_group, 2) # 리소스 관리 (비율 2)
    left_side_layout.addWidget(mw.attachment_group, 1) # 첨부 파일 (비율 1)
    mw.center_splitter.addWidget(left_side_widget)

    # --- 오른쪽 영역 (실행 버튼 + 탭 위젯) ---
    right_side_widget = QWidget()
    right_side_layout = QVBoxLayout(right_side_widget)
    right_side_layout.setContentsMargins(0, 0, 0, 0); right_side_layout.setSpacing(0)
    run_buttons_container = QWidget()
    run_layout = QHBoxLayout(run_buttons_container)
    run_layout.setContentsMargins(5, 5, 5, 5); run_layout.setSpacing(10); run_layout.setAlignment(Qt.AlignLeft)
    for btn in mw.run_buttons: run_layout.addWidget(btn)
    run_layout.addStretch(1)
    line_frame = QFrame(); line_frame.setFrameShape(QFrame.HLine); line_frame.setFrameShadow(QFrame.Sunken)
    right_side_layout.addWidget(run_buttons_container)
    right_side_layout.addWidget(line_frame)
    right_side_layout.addWidget(mw.build_tabs)
    mw.center_splitter.addWidget(right_side_widget)

    main_layout.addWidget(mw.center_splitter, 1)
    mw.center_splitter.setStretchFactor(0, 1) # 왼쪽 영역 비율
    mw.center_splitter.setStretchFactor(1, 3) # 오른쪽 영역 비율

def create_status_bar(mw: 'MainWindow'):
    """Creates the status bar."""
    mw.status_bar = QStatusBar()
    mw.setStatusBar(mw.status_bar)
    status_widget = QWidget()
    status_layout = QHBoxLayout(status_widget)
    status_layout.setContentsMargins(5, 2, 5, 2); status_layout.setSpacing(10)

    # 문자 수와 토큰 계산 라벨을 붙여서 추가
    status_layout.addWidget(mw.char_count_label)
    status_layout.addWidget(mw.token_count_label) # 토큰 계산 라벨 위치 변경

    # API 시간 표시 라벨 추가
    status_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
    status_layout.addWidget(mw.api_time_label)

    # LLM 관련 위젯들은 상단으로 이동했으므로 여기서 제거
    # status_layout.addWidget(QLabel("Model:"))
    # status_layout.addWidget(mw.llm_combo); mw.llm_combo.setFixedWidth(80)
    # status_layout.addWidget(mw.model_name_combo); mw.model_name_combo.setMinimumWidth(180)
    # status_layout.addWidget(mw.gemini_param_widget) # Gemini 파라미터 그룹 위젯 추가

    status_layout.addStretch(1)
    mw.status_bar.addPermanentWidget(status_widget)
