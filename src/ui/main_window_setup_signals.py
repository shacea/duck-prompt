
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QKeySequence

# MainWindow 타입 힌트
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .main_window import MainWindow

# 컨트롤러 import (함수 호출용)
def connect_signals(mw: 'MainWindow'):
    """Connects widget signals to controller slots."""
    # 상단 버튼
    mw.mode_toggle_btn.clicked.connect(mw._toggle_mode)
    mw.reset_program_btn.clicked.connect(mw.main_controller.reset_program) # MainController
    mw.load_previous_work_btn.clicked.connect(mw.resource_controller.load_state_from_default) # 새 버튼 연결 (ResourceController)
    mw.select_project_btn.clicked.connect(mw.file_tree_controller.select_project_folder) # FileTreeController

    # 파일 트리
    mw.tree_view.customContextMenuRequested.connect(mw.on_tree_view_context_menu) # MainWindow (컨트롤러 호출)
    mw.checkable_proxy.dataChanged.connect(mw.file_tree_controller.on_data_changed) # FileTreeController

    # 실행 버튼
    if mw.mode != "Meta Prompt Builder":
        mw.generate_tree_btn.clicked.connect(mw.file_tree_controller.generate_directory_tree_structure) # FileTreeController
        mw.generate_btn.clicked.connect(mw.prompt_controller.generate_prompt) # PromptController (Calculates tokens)
        mw.send_to_gemini_btn.clicked.connect(mw.send_prompt_to_gemini) # MainWindow (LangGraph 호출)
        mw.copy_btn.clicked.connect(mw.prompt_controller.copy_to_clipboard) # PromptController
        mw.run_xml_parser_btn.clicked.connect(mw.xml_controller.run_xml_parser) # XmlController
        mw.generate_all_btn.clicked.connect(mw.prompt_controller.generate_all_and_copy) # PromptController (Calculates tokens via generate_prompt)
    else:
        mw.generate_btn.clicked.connect(mw.prompt_controller.generate_meta_prompt) # PromptController (Calculates tokens)
        mw.copy_btn.clicked.connect(mw.prompt_controller.copy_to_clipboard) # PromptController
        if hasattr(mw, "generate_final_prompt_btn"):
            mw.generate_final_prompt_btn.clicked.connect(mw.prompt_controller.generate_final_meta_prompt) # PromptController (Calculates tokens)

    # 리소스 관리
    mw.resource_mode_combo.currentIndexChanged.connect(mw.resource_controller.load_templates_list) # ResourceController
    mw.load_selected_template_btn.clicked.connect(mw.resource_controller.load_selected_item) # ResourceController
    mw.save_as_template_btn.clicked.connect(mw.resource_controller.save_current_as_item) # ResourceController
    mw.delete_template_btn.clicked.connect(mw.resource_controller.delete_selected_item) # ResourceController
    mw.update_template_btn.clicked.connect(mw.resource_controller.update_current_item) # ResourceController
    mw.backup_button.clicked.connect(mw.resource_controller.backup_all_states_action) # ResourceController
    mw.restore_button.clicked.connect(mw.resource_controller.restore_states_from_backup_action) # ResourceController
    mw.template_tree.itemDoubleClicked.connect(mw.resource_controller.load_selected_item) # ResourceController

    # 첨부 파일 관리 버튼 (추가)
    if hasattr(mw, 'attach_file_btn'):
        mw.attach_file_btn.clicked.connect(mw.main_controller.attach_files) # MainController
    if hasattr(mw, 'paste_clipboard_btn'):
        mw.paste_clipboard_btn.clicked.connect(mw.main_controller.paste_from_clipboard) # MainController
    if hasattr(mw, 'remove_attachment_btn'):
        mw.remove_attachment_btn.clicked.connect(mw.main_controller.remove_selected_attachment) # MainController

    # 상태바 & 모델 선택
    mw.llm_combo.currentIndexChanged.connect(mw.main_controller.on_llm_selected) # MainController (Resets token label)

    # --- Gemini 파라미터 변경 시그널 연결 제거 (DB 저장 비활성화) ---
    # mw.gemini_temp_edit.textChanged.connect(mw.save_gemini_settings)
    # mw.gemini_thinking_checkbox.stateChanged.connect(mw.save_gemini_settings)
    # mw.gemini_budget_edit.textChanged.connect(mw.save_gemini_settings)
    # mw.gemini_search_checkbox.stateChanged.connect(mw.save_gemini_settings)
    # -----------------------------------------------------------

    # 텍스트 변경 시 문자 수 업데이트 및 토큰 레이블 리셋 (현재 활성 탭 기준)
    mw.build_tabs.currentChanged.connect(mw.main_controller.update_char_count_for_active_tab) # Update char counts when tab changes
    # Connect textChanged for all relevant text edit widgets to the new handler
    mw.system_tab.textChanged.connect(mw.main_controller.handle_text_changed)
    mw.user_tab.textChanged.connect(mw.main_controller.handle_text_changed)
    mw.prompt_output_tab.textChanged.connect(mw.main_controller.handle_text_changed)
    if hasattr(mw, 'dir_structure_tab'):
        mw.dir_structure_tab.textChanged.connect(mw.main_controller.handle_text_changed) # ReadOnly, but connect anyway
    if hasattr(mw, 'xml_input_tab'):
        mw.xml_input_tab.textChanged.connect(mw.main_controller.handle_text_changed)
    if hasattr(mw, 'summary_tab'): # Summary 탭 연결 추가
        mw.summary_tab.textChanged.connect(mw.main_controller.handle_text_changed) # ReadOnly, but connect anyway
    if hasattr(mw, 'meta_prompt_tab'):
        mw.meta_prompt_tab.textChanged.connect(mw.main_controller.handle_text_changed)
    if hasattr(mw, 'user_prompt_tab'):
        user_prompt_tab_widget = getattr(mw, 'user_prompt_tab', None)
        if user_prompt_tab_widget:
            user_prompt_tab_widget.textChanged.connect(mw.main_controller.handle_text_changed)
    if hasattr(mw, 'final_prompt_tab'):
        final_prompt_tab_widget = getattr(mw, 'final_prompt_tab', None)
        if final_prompt_tab_widget:
            final_prompt_tab_widget.textChanged.connect(mw.main_controller.handle_text_changed)
    # Custom tabs added later will have their signals connected in add_new_custom_tab

    # 메뉴 액션
    mw.settings_action.triggered.connect(mw.open_settings_dialog) # 설정 메뉴 연결
    mw.save_state_action.triggered.connect(mw.resource_controller.save_state_to_default) # ResourceController
    mw.load_state_action.triggered.connect(mw.resource_controller.load_state_from_default) # ResourceController
    mw.export_state_action.triggered.connect(mw.resource_controller.export_state_to_file) # ResourceController
    mw.import_state_action.triggered.connect(mw.resource_controller.import_state_from_file) # ResourceController

    # 단축키
    shortcut_generate = QAction(mw)
    shortcut_generate.setShortcut(QKeySequence("Ctrl+Return"))
    if mw.mode == "Meta Prompt Builder":
         if hasattr(mw, "generate_final_prompt_btn"):
             shortcut_generate.triggered.connect(mw.prompt_controller.generate_final_meta_prompt) # PromptController (Calculates tokens)
         else:
             shortcut_generate.triggered.connect(mw.prompt_controller.generate_meta_prompt) # PromptController (Calculates tokens)
    else:
         shortcut_generate.triggered.connect(mw.prompt_controller.generate_all_and_copy) # PromptController (Calculates tokens)
    mw.addAction(shortcut_generate)

    shortcut_copy = QAction(mw)
    shortcut_copy.setShortcut(QKeySequence("Ctrl+C"))
    shortcut_copy.triggered.connect(mw.on_copy_shortcut) # MainWindow
    mw.addAction(shortcut_copy)
