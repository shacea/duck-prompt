from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QKeySequence

# MainWindow 타입 힌트
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

# 컨트롤러 import (함수 호출용)
from .controllers.system_prompt_controller import select_default_system_prompt

def connect_signals(mw: 'MainWindow'):
    """Connects widget signals to controller slots."""
    # 상단 버튼
    mw.mode_toggle_btn.clicked.connect(mw._toggle_mode)
    mw.reset_program_btn.clicked.connect(mw.main_controller.reset_program) # MainController
    mw.select_project_btn.clicked.connect(mw.file_tree_controller.select_project_folder) # FileTreeController
    mw.select_default_prompt_btn.clicked.connect(lambda: select_default_system_prompt(mw)) # SystemPromptController (함수 직접 호출)

    # 파일 트리
    mw.tree_view.customContextMenuRequested.connect(mw.on_tree_view_context_menu) # MainWindow (컨트롤러 호출)
    mw.tree_view.selectionModel().selectionChanged.connect(mw.on_selection_changed_handler) # MainWindow (컨트롤러 호출)
    mw.checkable_proxy.dataChanged.connect(mw.file_tree_controller.on_data_changed) # FileTreeController

    # 실행 버튼
    if mw.mode != "Meta Prompt Builder":
        mw.generate_tree_btn.clicked.connect(mw.file_tree_controller.generate_directory_tree_structure) # FileTreeController
        mw.generate_btn.clicked.connect(mw.prompt_controller.generate_prompt) # PromptController
        mw.copy_btn.clicked.connect(mw.prompt_controller.copy_to_clipboard) # PromptController
        mw.run_xml_parser_btn.clicked.connect(mw.xml_controller.run_xml_parser) # XmlController
        mw.generate_all_btn.clicked.connect(mw.prompt_controller.generate_all_and_copy) # PromptController
    else:
        mw.generate_btn.clicked.connect(mw.prompt_controller.generate_meta_prompt) # PromptController
        mw.copy_btn.clicked.connect(mw.prompt_controller.copy_to_clipboard) # PromptController
        if hasattr(mw, "generate_final_prompt_btn"):
            mw.generate_final_prompt_btn.clicked.connect(mw.prompt_controller.generate_final_meta_prompt) # PromptController

    # 리소스 관리
    mw.resource_mode_combo.currentIndexChanged.connect(mw.resource_controller.load_templates_list) # ResourceController
    mw.load_selected_template_btn.clicked.connect(mw.resource_controller.load_selected_item) # ResourceController
    mw.save_as_template_btn.clicked.connect(mw.resource_controller.save_current_as_item) # ResourceController
    mw.delete_template_btn.clicked.connect(mw.resource_controller.delete_selected_item) # ResourceController
    mw.update_template_btn.clicked.connect(mw.resource_controller.update_current_item) # ResourceController
    mw.backup_button.clicked.connect(mw.resource_controller.backup_all_states_action) # ResourceController
    mw.restore_button.clicked.connect(mw.resource_controller.restore_states_from_backup_action) # ResourceController
    mw.template_tree.itemDoubleClicked.connect(mw.resource_controller.load_selected_item) # ResourceController

    # .gitignore
    mw.save_gitignore_btn.clicked.connect(mw.file_tree_controller.save_gitignore_settings) # FileTreeController

    # 상태바
    mw.auto_token_calc_check.stateChanged.connect(mw.main_controller.update_active_tab_counts) # MainController
    # 텍스트 변경 시 카운트 업데이트
    mw.prompt_output_tab.textChanged.connect(mw.main_controller.update_active_tab_counts)
    if hasattr(mw, 'final_prompt_tab'):
        mw.final_prompt_tab.textChanged.connect(mw.main_controller.update_active_tab_counts)
    # 다른 탭들도 필요시 연결
    mw.system_tab.textChanged.connect(mw.main_controller.update_active_tab_counts)
    mw.user_tab.textChanged.connect(mw.main_controller.update_active_tab_counts)
    if hasattr(mw, 'meta_prompt_tab'):
        mw.meta_prompt_tab.textChanged.connect(mw.main_controller.update_active_tab_counts)
    if hasattr(mw, 'user_prompt_tab'):
        mw.user_prompt_tab.textChanged.connect(mw.main_controller.update_active_tab_counts)


    # 메뉴 액션
    mw.save_state_action.triggered.connect(mw.resource_controller.save_state_to_default) # ResourceController
    mw.load_state_action.triggered.connect(mw.resource_controller.load_state_from_default) # ResourceController
    mw.export_state_action.triggered.connect(mw.resource_controller.export_state_to_file) # ResourceController
    mw.import_state_action.triggered.connect(mw.resource_controller.import_state_from_file) # ResourceController

    # 단축키
    shortcut_generate = QAction(mw)
    shortcut_generate.setShortcut(QKeySequence("Ctrl+Return"))
    if mw.mode == "Meta Prompt Builder":
         shortcut_generate.triggered.connect(mw.prompt_controller.generate_meta_prompt) # PromptController
    else:
         shortcut_generate.triggered.connect(mw.prompt_controller.generate_prompt) # PromptController
    mw.addAction(shortcut_generate)

    shortcut_copy = QAction(mw)
    shortcut_copy.setShortcut(QKeySequence("Ctrl+C"))
    shortcut_copy.triggered.connect(mw.on_copy_shortcut) # MainWindow
    mw.addAction(shortcut_copy)
