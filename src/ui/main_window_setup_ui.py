import os
import sys # sys 모듈 import
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox, QAbstractItemView, QMenuBar,
    QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QComboBox,
    QFrame, QLineEdit, QGroupBox
)
from PyQt5.QtGui import QFont, QFontDatabase # QFontDatabase import
from PyQt5.QtCore import Qt

# MainWindow 타입 힌트
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

# 모델 및 위젯 import
from .models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
from .widgets.custom_text_edit import CustomTextEdit
from .widgets.custom_tab_bar import CustomTabBar
# get_resource_path import
from utils.helpers import get_resource_path
# CheckBoxDelegate import 추가
from .widgets.check_box_delegate import CheckBoxDelegate

def create_menu_bar(mw: 'MainWindow'):
    """Creates the main menu bar."""
    mw.menubar = QMenuBar(mw) # 멤버 변수로 저장
    mw.setMenuBar(mw.menubar)

    # 파일 메뉴 (추가)
    file_menu = mw.menubar.addMenu("파일")
    mw.settings_action = QAction("환경 설정...", mw) # 설정 액션 추가
    file_menu.addAction(mw.settings_action)
    file_menu.addSeparator()

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
    # --- OS별 기본 폰트 설정 ---
    default_font = QFont() # 기본 시스템 폰트
    font_family_name = ""

    if sys.platform == "win32":
        try:
            font_path = get_resource_path("fonts/malgun.ttf")
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                family = QFontDatabase.applicationFontFamilies(font_id)[0]
                print(f"Loaded custom font: {family} from {font_path}")
                default_font = QFont(family, 10) # 폰트 크기 지정 (예: 10)
                font_family_name = family
            else:
                print(f"Failed to load custom font from {font_path}. Using system default.")
                # 실패 시 기본 sans-serif 폰트 사용 시도
                default_font.setFamily("Malgun Gothic") # 대체 폰트 지정
                default_font.setPointSize(10)
                font_family_name = "Malgun Gothic (Fallback)"
        except Exception as e:
            print(f"Error loading custom font: {e}. Using system default.")
            # 예외 발생 시 기본 sans-serif 폰트 사용 시도
            default_font.setFamily("Malgun Gothic") # 대체 폰트 지정
            default_font.setPointSize(10)
            font_family_name = "Malgun Gothic (Exception Fallback)"
    elif sys.platform == "darwin": # macOS
        default_font.setFamily("Apple SD Gothic Neo") # macOS 기본 한글 폰트 예시
        default_font.setPointSize(11) # macOS 기본 크기 예시
        font_family_name = "Apple SD Gothic Neo"
    else: # Linux 등 기타
        # 시스템 기본 sans-serif 폰트 사용
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
    mw.tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection) # Allow multi-selection
    mw.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
    mw.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers) # Disable editing item names directly

    # --- CheckBoxDelegate 적용 ---
    # Delegate 생성 시 부모 위젯 전달 (스타일 접근 등에 필요할 수 있음)
    # CheckBoxDelegate를 mw.tree_view의 자식으로 생성하여 스타일 상속 및 관리 용이
    mw.tree_view.setItemDelegateForColumn(0, CheckBoxDelegate(mw.tree_view)) # 0번 컬럼에 Delegate 설정

    # 파일 트리 폰트 설정 (선택적)
    # mw.tree_view.setFont(default_font)

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
    mw.system_tab.setFont(default_font) # 폰트 적용
    mw.build_tabs.addTab(mw.system_tab, system_tab_label)

    mw.user_tab = CustomTextEdit()
    mw.user_tab.setPlaceholderText(f"{user_tab_label} 내용 입력...")
    mw.user_tab.setFont(default_font) # 폰트 적용
    mw.build_tabs.addTab(mw.user_tab, user_tab_label)

    if mw.mode != "Meta Prompt Builder":
        mw.dir_structure_tab = CustomTextEdit()
        mw.dir_structure_tab.setReadOnly(True)
        mw.dir_structure_tab.setFont(default_font) # 폰트 적용
        mw.build_tabs.addTab(mw.dir_structure_tab, "파일 트리")

    mw.prompt_output_tab = CustomTextEdit()
    # 출력 탭은 고정폭 폰트 사용 고려 (Consolas 등)
    output_font = QFont("Consolas", 10) if sys.platform == "win32" else QFont("Monaco", 11) if sys.platform == "darwin" else QFont("Monospace", 10)
    output_font.setStyleHint(QFont.Monospace)
    mw.prompt_output_tab.setFont(output_font)
    mw.prompt_output_tab.setStyleSheet("QTextEdit { padding: 10px; }")
    mw.build_tabs.addTab(mw.prompt_output_tab, prompt_output_label)

    if mw.mode != "Meta Prompt Builder":
        mw.xml_input_tab = CustomTextEdit()
        mw.xml_input_tab.setPlaceholderText("XML 내용 입력...")
        mw.xml_input_tab.setFont(default_font) # 폰트 적용
        mw.build_tabs.addTab(mw.xml_input_tab, "XML 입력")

        # Summary 탭 추가 (Code Enhancer 모드에서만)
        mw.summary_tab = CustomTextEdit()
        mw.summary_tab.setPlaceholderText("Gemini 응답 요약...")
        mw.summary_tab.setReadOnly(True) # 읽기 전용 설정
        mw.summary_tab.setFont(default_font) # 폰트 적용
        mw.build_tabs.addTab(mw.summary_tab, "Summary")

    if mw.mode == "Meta Prompt Builder":
        mw.meta_prompt_tab = CustomTextEdit()
        mw.meta_prompt_tab.setPlaceholderText("메타 프롬프트 내용...")
        mw.meta_prompt_tab.setFont(default_font) # 폰트 적용
        mw.build_tabs.addTab(mw.meta_prompt_tab, "메타 프롬프트")

        mw.user_prompt_tab = CustomTextEdit()
        mw.user_prompt_tab.setPlaceholderText("사용자 프롬프트 내용 입력...")
        mw.user_prompt_tab.setFont(default_font) # 폰트 적용
        mw.build_tabs.addTab(mw.user_prompt_tab, "사용자 프롬프트")

        mw.final_prompt_tab = CustomTextEdit()
        # 최종 프롬프트 탭도 고정폭 폰트 사용 고려
        mw.final_prompt_tab.setFont(output_font)
        mw.final_prompt_tab.setStyleSheet("QTextEdit { padding: 10px; }")
        mw.build_tabs.addTab(mw.final_prompt_tab, "최종 프롬프트")

    # --- 실행 버튼 (오른쪽 상단) ---
    copy_btn_label = "📋 메타 프롬프트 복사" if mw.mode == "Meta Prompt Builder" else "📋 클립보드에 복사"
    if mw.mode != "Meta Prompt Builder":
        mw.generate_tree_btn = QPushButton("🌳 트리 생성")
        mw.generate_btn = QPushButton("✨ 프롬프트 생성")
        mw.send_to_gemini_btn = QPushButton("♊ Gemini로 전송") # Gemini 전송 버튼 추가
        mw.copy_btn = QPushButton(copy_btn_label)
        mw.run_xml_parser_btn = QPushButton("▶️ XML 파서 실행")
        mw.generate_all_btn = QPushButton("⚡️ 한번에 실행")
        mw.run_buttons = [mw.generate_tree_btn, mw.generate_btn, mw.send_to_gemini_btn, mw.copy_btn, mw.run_xml_parser_btn, mw.generate_all_btn]
    else:
        mw.generate_btn = QPushButton("🚀 메타 프롬프트 생성")
        mw.copy_btn = QPushButton(copy_btn_label)
        mw.generate_final_prompt_btn = QPushButton("🚀 최종 프롬프트 생성")
        mw.run_buttons = [mw.generate_btn, mw.copy_btn, mw.generate_final_prompt_btn]

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
    # Main layout margins 줄임 (상단 여백)
    main_layout.setContentsMargins(5, 2, 5, 5)
    main_layout.setSpacing(2) # Main layout spacing

    # --- 상단 레이아웃 ---
    top_button_container = QWidget()
    top_button_layout = QHBoxLayout(top_button_container)
    top_button_layout.setSpacing(10)
    top_button_layout.setContentsMargins(0, 0, 0, 0) # Button container margins
    top_button_layout.addWidget(mw.mode_toggle_btn)
    top_button_layout.addWidget(mw.reset_program_btn)
    top_button_layout.addWidget(mw.select_project_btn)
    top_button_layout.addStretch(1)

    top_layout_wrapper = QVBoxLayout()
    top_layout_wrapper.setSpacing(2) # Spacing between button container and label
    top_layout_wrapper.setContentsMargins(0, 0, 0, 0) # Wrapper margins
    top_layout_wrapper.addWidget(top_button_container)
    top_layout_wrapper.addWidget(mw.project_folder_label)
    # Add the wrapper to the main layout with stretch factor 0
    main_layout.addLayout(top_layout_wrapper, 0)

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
    run_layout.addStretch(1) # 버튼들을 왼쪽으로 정렬

    line_frame = QFrame()
    line_frame.setFrameShape(QFrame.HLine)
    line_frame.setFrameShadow(QFrame.Sunken)

    right_side_layout.addWidget(run_buttons_container)
    right_side_layout.addWidget(line_frame)
    right_side_layout.addWidget(mw.build_tabs) # 탭 위젯이 남은 공간 모두 차지
    mw.center_splitter.addWidget(right_side_widget)

    # 중앙 스플리터를 메인 레이아웃에 추가 (stretch=1로 설정하여 남은 공간 차지)
    main_layout.addWidget(mw.center_splitter, 1)

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