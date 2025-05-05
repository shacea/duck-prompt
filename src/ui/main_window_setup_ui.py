import os
import sys
from PyQt6.QtWidgets import ( # PyQt5 -> PyQt6
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QTabWidget,
    QStatusBar, QPushButton, QLabel, QCheckBox, QAbstractItemView, QMenuBar,
    QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QComboBox,
    QFrame, QLineEdit, QGroupBox, QSpacerItem, QSizePolicy, QListWidget,
    QGridLayout
)
from PyQt6.QtGui import QFont, QFontDatabase, QAction # PyQt5 -> PyQt6, QAction 추가
from PyQt6.QtCore import Qt # PyQt5 -> PyQt6

# MainWindow 타입 힌트
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

# 모델 및 위젯 import
# from .models.file_system_models import FilteredFileSystemModel, CheckableProxyModel # Removed QFileSystemModel based
from .models.file_system_models import CachedFileSystemModel, CheckableProxyModel # Use new models
from .widgets.custom_text_edit import CustomTextEdit
from .widgets.custom_tab_bar import CustomTabBar
from utils.helpers import get_resource_path
from .widgets.check_box_delegate import CheckBoxDelegate
from .widgets.file_tree_view import FileTreeView

def create_menu_bar(mw: 'MainWindow'):
    """Creates the main menu bar."""
    mw.menubar = QMenuBar(mw)
    mw.setMenuBar(mw.menubar)

    # "파일" 메뉴 제거, "환경 설정" 메뉴를 첫 번째로 추가
    settings_menu = mw.menubar.addMenu("환경 설정") # "파일" 대신 "환경 설정" 메뉴 추가
    mw.settings_action = QAction("환경 설정 열기...", mw) # PyQt6: QAction(text, parent)
    settings_menu.addAction(mw.settings_action)
    settings_menu.addSeparator() # 필요 시 구분선 추가

    # 나머지 메뉴들
    mode_menu = mw.menubar.addMenu("모드")
    switch_to_code_action = QAction("코드 강화 빌더로 전환", mw) # PyQt6: QAction(text, parent)
    switch_to_meta_action = QAction("메타 프롬프트 빌더로 전환", mw) # PyQt6: QAction(text, parent)
    switch_to_code_action.triggered.connect(lambda: mw._restart_with_mode("Code Enhancer Prompt Builder"))
    switch_to_meta_action.triggered.connect(lambda: mw._restart_with_mode("Meta Prompt Builder"))
    mode_menu.addAction(switch_to_code_action)
    mode_menu.addAction(switch_to_meta_action)

    state_menu = mw.menubar.addMenu("상태")
    mw.save_state_action = QAction("상태 저장(기본)", mw) # PyQt6: QAction(text, parent)
    mw.load_state_action = QAction("상태 불러오기(기본)", mw) # PyQt6: QAction(text, parent)
    mw.export_state_action = QAction("상태 내보내기", mw) # PyQt6: QAction(text, parent)
    mw.import_state_action = QAction("상태 가져오기", mw) # PyQt6: QAction(text, parent)
    state_menu.addAction(mw.save_state_action)
    state_menu.addAction(mw.load_state_action)
    state_menu.addAction(mw.export_state_action)
    state_menu.addAction(mw.import_state_action)

    help_menu = mw.menubar.addMenu("도움말")
    open_readme_action = QAction("README 열기", mw) # PyQt6: QAction(text, parent)
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
        default_font.setStyleHint(QFont.StyleHint.SansSerif) # QFont.SansSerif -> QFont.StyleHint.SansSerif
        default_font.setPointSize(10)
        font_family_name = "System Default Sans-Serif"
    print(f"Applying default font: {font_family_name}, Size: {default_font.pointSize()}")

    # --- 상단 버튼 및 레이블 ---
    mw.mode_toggle_btn = QPushButton("🔄 모드 전환")
    mw.reset_program_btn = QPushButton("🗑️ 전체 프로그램 리셋")
    mw.load_previous_work_btn = QPushButton("⏪ 마지막 작업 불러오기") # 버튼 텍스트 변경
    mw.save_current_work_btn = QPushButton("💾 현재 작업 저장") # 작업 저장 버튼 추가
    mw.select_project_btn = QPushButton("📁 프로젝트 폴더 선택")
    for btn in [mw.mode_toggle_btn, mw.reset_program_btn, mw.load_previous_work_btn, mw.save_current_work_btn, mw.select_project_btn]: # 새 버튼 포함
        btn.setFixedHeight(30)
    mw.project_folder_label = QLabel("현재 프로젝트 폴더: (선택 안 됨)")
    font_lbl = mw.project_folder_label.font()
    font_lbl.setPointSize(10); font_lbl.setBold(True)
    mw.project_folder_label.setFont(font_lbl)

    # --- 파일 탐색기 (왼쪽) ---
    # Use CachedFileSystemModel and CheckableProxyModel
    mw.cached_model = CachedFileSystemModel() # Source model
    mw.tree_view = FileTreeView() # Custom view
    project_folder_getter = lambda: mw.current_project_folder
    # Pass fs_service for potential fallback checks (though ideally not needed)
    mw.checkable_proxy = CheckableProxyModel(project_folder_getter, mw.fs_service, mw.tree_view)
    mw.checkable_proxy.setSourceModel(mw.cached_model) # Set source model
    mw.checkable_proxy.setFilterKeyColumn(0) # Filter based on column 0 data (name/node)
    mw.checkable_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive) # Qt.CaseInsensitive -> Qt.CaseSensitivity.CaseInsensitive

    mw.tree_view.setModel(mw.checkable_proxy) # Set proxy model to the view
    mw.tree_view.setColumnWidth(0, 250)
    # No need to hide columns as CachedFileSystemModel only has one
    # mw.tree_view.hideColumn(1); mw.tree_view.hideColumn(2); mw.tree_view.hideColumn(3)
    mw.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # QAbstractItemView.ExtendedSelection -> QAbstractItemView.SelectionMode.ExtendedSelection
    mw.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) # Qt.CustomContextMenu -> Qt.ContextMenuPolicy.CustomContextMenu
    mw.tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # QAbstractItemView.NoEditTriggers -> QAbstractItemView.EditTrigger.NoEditTriggers
    mw.tree_view.setItemDelegateForColumn(0, CheckBoxDelegate(mw.tree_view))
    mw.tree_view.setHeaderHidden(True) # Hide header for single column model
    mw.tree_view.setSortingEnabled(False) # Disable sorting for now


    # --- 리소스 관리 (오른쪽 하단) ---
    mw.resource_manager_group = QGroupBox("리소스 관리")
    resource_manager_layout = QGridLayout() # QVBoxLayout 대신 QGridLayout 사용
    resource_manager_layout.setContentsMargins(5, 5, 5, 5); resource_manager_layout.setSpacing(5)

    # 위젯 생성 (기존 코드 재사용)
    mw.resource_mode_combo = QComboBox(); mw.resource_mode_combo.addItems(["프롬프트", "상태"])
    mw.template_tree = QTreeWidget(); mw.template_tree.setHeaderHidden(True)
    mw.load_selected_template_btn = QPushButton("📥 선택 불러오기")
    mw.save_as_template_btn = QPushButton("💾 현재 내용으로 저장")
    mw.template_type_label = QLabel("저장 타입:")
    mw.template_type_combo = QComboBox(); mw.template_type_combo.addItems(["시스템", "사용자"])
    mw.delete_template_btn = QPushButton("❌ 선택 삭제")
    mw.update_template_btn = QPushButton("🔄 현재 내용 업데이트")

    # --- 레이아웃 재구성 (2열 그리드) ---
    # 왼쪽 열 (Column 0)
    resource_manager_layout.addWidget(QLabel("아래에서 로드/저장할 리소스 선택:"), 0, 0, 1, 2) # 라벨은 2열에 걸쳐 표시
    resource_manager_layout.addWidget(mw.template_tree, 1, 0, 6, 1) # 트리는 1행부터 6개 행에 걸쳐 표시

    # 오른쪽 열 (Column 1) - 위젯 배치 순서 조정
    resource_manager_layout.addWidget(mw.load_selected_template_btn, 1, 1) # 행 1

    # 저장 타입 레이아웃 (HBox)
    save_type_layout = QHBoxLayout()
    save_type_layout.addWidget(mw.template_type_label)
    save_type_layout.addWidget(mw.template_type_combo)
    save_type_layout.setContentsMargins(0, 0, 0, 0)
    resource_manager_layout.addLayout(save_type_layout, 2, 1) # 행 2

    # 리소스 타입 선택 레이아웃 (HBox)
    resource_type_layout = QHBoxLayout()
    resource_type_layout.addWidget(QLabel("리소스 타입 선택:"))
    resource_type_layout.addWidget(mw.resource_mode_combo)
    resource_type_layout.setContentsMargins(0, 0, 0, 0)
    resource_manager_layout.addLayout(resource_type_layout, 3, 1) # 행 3

    resource_manager_layout.addWidget(mw.save_as_template_btn, 4, 1) # 행 4
    resource_manager_layout.addWidget(mw.update_template_btn, 5, 1) # 행 5
    resource_manager_layout.addWidget(mw.delete_template_btn, 6, 1) # 행 6

    # 오른쪽 열 하단에 빈 공간 추가 (선택적)
    resource_manager_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), 7, 1) # QSizePolicy.Minimum -> QSizePolicy.Policy.Minimum, QSizePolicy.Expanding -> QSizePolicy.Policy.Expanding

    # 열 너비 비율 설정 (선택적)
    resource_manager_layout.setColumnStretch(0, 1) # 왼쪽 열(트리)이 남는 공간 차지
    resource_manager_layout.setColumnStretch(1, 0) # 오른쪽 열(버튼)은 필요한 만큼만

    mw.resource_manager_group.setLayout(resource_manager_layout) # 최종 레이아웃 설정

    # --- 첨부 파일 관리 (왼쪽 하단으로 이동) ---
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
    mw.attachment_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # QAbstractItemView.ExtendedSelection -> QAbstractItemView.SelectionMode.ExtendedSelection
    attachment_layout.addLayout(attachment_button_layout)
    attachment_layout.addWidget(mw.attachment_list_widget, 1) # 리스트 위젯이 공간 차지
    mw.attachment_group.setLayout(attachment_layout)
    # Code Enhancer 모드에서만 보이도록 설정 (초기 상태)
    mw.attachment_group.setVisible(mw.mode == "Code Enhancer Prompt Builder")


    # --- 탭 위젯 (오른쪽 상단) ---
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
    output_font = QFont("Consolas", 10) if sys.platform == "win32" else QFont("Monaco", 11) if sys.platform == "darwin" else QFont("Monospace", 10); output_font.setStyleHint(QFont.StyleHint.Monospace) # QFont.Monospace -> QFont.StyleHint.Monospace
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

    # --- LLM 관련 위젯 (상단) ---
    mw.llm_combo = QComboBox(); mw.llm_combo.addItems(["Gemini", "Claude", "GPT"])
    mw.model_name_combo = QComboBox(); mw.model_name_combo.setEditable(True); mw.model_name_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert) # QComboBox.NoInsert -> QComboBox.InsertPolicy.NoInsert
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
    # 위젯 추가 순서 변경: Temp -> Search -> Thinking -> Budget
    gemini_param_layout.addWidget(mw.gemini_temp_label); gemini_param_layout.addWidget(mw.gemini_temp_edit)
    gemini_param_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)) # QSizePolicy.Fixed -> QSizePolicy.Policy.Fixed
    gemini_param_layout.addWidget(mw.gemini_search_label); gemini_param_layout.addWidget(mw.gemini_search_checkbox) # Search 이동
    gemini_param_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)) # QSizePolicy.Fixed -> QSizePolicy.Policy.Fixed
    gemini_param_layout.addWidget(mw.gemini_thinking_label); gemini_param_layout.addWidget(mw.gemini_thinking_checkbox)
    gemini_param_layout.addSpacerItem(QSpacerItem(10, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)) # QSizePolicy.Fixed -> QSizePolicy.Policy.Fixed
    gemini_param_layout.addWidget(mw.gemini_budget_label); gemini_param_layout.addWidget(mw.gemini_budget_edit)
    mw.gemini_param_widget.setVisible(mw.llm_combo.currentText() == "Gemini") # 초기 가시성 설정

