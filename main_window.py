import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox, QFrame
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont
from PyQt5.QtCore import Qt, QSize, QStandardPaths

from config import config
from file_explorer import FilteredFileSystemModel, CheckableProxyModel
from main_controller import MainController
from custom_text_edit import CustomTextEdit
from tab_manager import is_tab_deletable
from utils import get_resource_path
from PyQt5.QtWidgets import QTabBar

# 새로 import
from system_prompt_controller import apply_default_system_prompt, select_default_system_prompt

class CustomTabBar(QTabBar):
    def __init__(self, parent: QTabWidget, main_window: QMainWindow):
        super().__init__(parent)
        self.main_window = main_window
        self.setTabsClosable(False)
        self.setMovable(True)
        self.addTab("+")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            index = self.tabAt(pos)
            if index >= 0 and self.tabText(index) == "+":
                self.main_window.add_new_custom_tab()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            pos = event.pos()
            index = self.tabAt(pos)
            if index >= 0:
                tab_text = self.tabText(index)
                if is_tab_deletable(tab_text):
                    self.parent().removeTab(index)
                else:
                    QMessageBox.warning(None, "경고", "이 탭은 제거할 수 없습니다.")
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            index = self.tabAt(pos)
            if index >= 0:
                tab_text = self.tabText(index)
                if is_tab_deletable(tab_text):
                    new_name, ok = QInputDialog.getText(None, "탭 이름 변경", "새 탭 이름을 입력하세요:", text=tab_text)
                    if ok and new_name.strip():
                        self.setTabText(index, new_name.strip())
        super().mouseDoubleClickEvent(event)

class MainWindow(QMainWindow):
    def __init__(self, mode="Code Enhancer Prompt Builder"):
        super().__init__()
        self.mode = mode
        self.base_title = "DuckPrompt" # 기본 제목
        self.update_window_title() # 초기 제목 설정

        QApplication.setStyle(QStyleFactory.create("Fusion"))

        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        mode_menu = menubar.addMenu("모드")

        switch_to_code_action = QAction("코드 강화 빌더로 전환", self)
        switch_to_meta_action = QAction("메타 프롬프트 빌더로 전환", self)

        def restart_with_mode(new_mode):
            self.close()
            new_window = MainWindow(mode=new_mode)
            new_window.resize(1200, 800)
            new_window.show()
            new_window.build_tabs.setCurrentIndex(0)
            new_window.show()

        switch_to_code_action.triggered.connect(lambda: restart_with_mode("Code Enhancer Prompt Builder"))
        switch_to_meta_action.triggered.connect(lambda: restart_with_mode("Meta Prompt Builder"))

        mode_menu.addAction(switch_to_code_action)
        mode_menu.addAction(switch_to_meta_action)

        state_menu = menubar.addMenu("상태")
        save_state_action = QAction("상태 저장(기본)", self)
        load_state_action = QAction("상태 불러오기(기본)", self)
        export_state_action = QAction("상태 내보내기", self)
        import_state_action = QAction("상태 가져오기", self)

        state_menu.addAction(save_state_action)
        state_menu.addAction(load_state_action)
        state_menu.addAction(export_state_action)
        state_menu.addAction(import_state_action)

        self.reset_state()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        top_button_container = QWidget()
        top_button_layout = QHBoxLayout(top_button_container)
        top_button_layout.setSpacing(10)
        top_button_layout.setContentsMargins(0, 0, 0, 0)

        self.mode_toggle_btn = QPushButton("🔄 모드 전환")
        self.mode_toggle_btn.setFixedHeight(30)

        self.reset_program_btn = QPushButton("🗑️ 전체 프로그램 리셋")
        self.reset_program_btn.setFixedHeight(30)

        self.select_project_btn = QPushButton("📁 프로젝트 폴더 선택")
        self.select_project_btn.setFixedHeight(30)

        self.select_default_prompt_btn = QPushButton("⚙️ 기본 시스템 프롬프트 지정")
        self.select_default_prompt_btn.setFixedHeight(30)

        top_button_layout.addWidget(self.mode_toggle_btn)
        top_button_layout.addWidget(self.reset_program_btn)
        top_button_layout.addWidget(self.select_project_btn)
        top_button_layout.addWidget(self.select_default_prompt_btn)

        self.project_folder_label = QLabel("현재 프로젝트 폴더: (선택 안 됨)")
        font_lbl = self.project_folder_label.font()
        font_lbl.setPointSize(10)
        font_lbl.setBold(True)
        self.project_folder_label.setFont(font_lbl)

        top_layout_wrapper = QVBoxLayout()
        top_layout_wrapper.setSpacing(5)
        top_layout_wrapper.setContentsMargins(0, 0, 0, 0)
        top_layout_wrapper.addWidget(top_button_container)
        top_layout_wrapper.addWidget(self.project_folder_label)

        main_layout.addLayout(top_layout_wrapper)

        center_splitter = QSplitter(Qt.Horizontal)

        left_side_widget = QWidget()
        left_side_layout = QVBoxLayout(left_side_widget)
        left_side_layout.setContentsMargins(2, 2, 2, 2)
        left_side_layout.setSpacing(5)

        self.dir_model = FilteredFileSystemModel(config)

        def get_current_folder():
            return self.current_project_folder

        self.tree_view = QTreeView()
        self.checkable_proxy = CheckableProxyModel(self.dir_model, get_current_folder, self.tree_view)
        self.checkable_proxy.setSourceModel(self.dir_model)

        self.tree_view.setModel(self.checkable_proxy)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)
        self.tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)

        self.dir_model.setRootPath(os.path.expanduser("~"))
        left_side_layout.addWidget(self.tree_view)
        center_splitter.addWidget(left_side_widget)

        right_side_widget = QWidget()
        right_side_layout = QVBoxLayout(right_side_widget)
        right_side_layout.setContentsMargins(0, 0, 0, 0)
        right_side_layout.setSpacing(0)

        self.build_tabs = QTabWidget()
        custom_tab_bar = CustomTabBar(self.build_tabs, self)
        self.build_tabs.setTabBar(custom_tab_bar)

        if self.mode == "Meta Prompt Builder":
            system_tab_label = "메타 프롬프트 템플릿"
            user_tab_label = "메타 사용자 입력"
            copy_btn_label = "📋 메타 프롬프트 복사"
        else:
            system_tab_label = "시스템"
            user_tab_label = "사용자"
            copy_btn_label = "📋 클립보드에 복사"

        self.system_tab = CustomTextEdit()
        placeholder_system = (
            "Enter META Prompt Template..." if self.mode == "Meta Prompt Builder"
            else "Enter System Prompt..."
        )
        self.system_tab.setPlaceholderText(placeholder_system)
        self.build_tabs.addTab(self.system_tab, system_tab_label)

        self.user_tab = CustomTextEdit()
        placeholder_user = (
            "Enter META User Prompt..." if self.mode == "Meta Prompt Builder"
            else "Enter User Prompt..."
        )
        self.user_tab.setPlaceholderText(placeholder_user)
        self.build_tabs.addTab(self.user_tab, user_tab_label)

        if self.mode != "Meta Prompt Builder":
            self.dir_structure_tab = CustomTextEdit()
            self.dir_structure_tab.setReadOnly(True)
            self.build_tabs.addTab(self.dir_structure_tab, "파일 트리")

        self.prompt_output_tab = CustomTextEdit()
        self.prompt_output_tab.setReadOnly(False)
        self.prompt_output_tab.setFont(QFont("Consolas", 10))
        self.prompt_output_tab.setStyleSheet("QTextEdit { padding: 10px; }")

        if self.mode == "Meta Prompt Builder":
            self.build_tabs.addTab(self.prompt_output_tab, "메타 프롬프트 출력")
        else:
            self.build_tabs.addTab(self.prompt_output_tab, "프롬프트 출력")

        if self.mode != "Meta Prompt Builder":
            self.xml_input_tab = CustomTextEdit()
            self.xml_input_tab.setPlaceholderText("Enter XML content here...")
            self.build_tabs.addTab(self.xml_input_tab, "XML 입력")

        if self.mode == "Meta Prompt Builder":
            self.separator_tab = CustomTextEdit()
            self.separator_tab.setReadOnly(True)
            self.separator_tab.setText("   |   ")
            self.build_tabs.addTab(self.separator_tab, "   |   ")

            self.meta_prompt_tab = CustomTextEdit()
            self.meta_prompt_tab.setPlaceholderText("META Prompt Content...")
            self.build_tabs.addTab(self.meta_prompt_tab, "메타 프롬프트")

            self.user_prompt_tab = CustomTextEdit()
            self.user_prompt_tab.setPlaceholderText("Enter user-prompt content...")
            self.build_tabs.addTab(self.user_prompt_tab, "사용자 프롬프트")

            self.final_prompt_tab = CustomTextEdit()
            self.final_prompt_tab.setReadOnly(False)
            self.final_prompt_tab.setFont(QFont("Consolas", 10))
            self.final_prompt_tab.setStyleSheet("QTextEdit { padding: 10px; }")
            self.build_tabs.addTab(self.final_prompt_tab, "최종 프롬프트")

        run_buttons_container = QWidget()
        run_layout = QHBoxLayout(run_buttons_container)
        run_layout.setContentsMargins(5, 5, 5, 5)
        run_layout.setSpacing(10)
        run_layout.setAlignment(Qt.AlignLeft)

        if self.mode != "Meta Prompt Builder":
            self.generate_tree_btn = QPushButton("🌳 트리 생성")
            self.generate_btn = QPushButton("✨ 프롬프트 생성")
            self.copy_btn = QPushButton(copy_btn_label)
            self.run_xml_parser_btn = QPushButton("▶️ XML 파서 실행")
            self.generate_all_btn = QPushButton("⚡️ 한번에 실행") # 새 버튼
            run_buttons = [self.generate_tree_btn, self.generate_btn, self.copy_btn, self.run_xml_parser_btn, self.generate_all_btn] # 새 버튼 추가
        else:
            self.generate_btn = QPushButton("🚀 메타 프롬프트 생성")
            self.copy_btn = QPushButton(copy_btn_label)
            self.generate_final_prompt_btn = QPushButton("🚀 최종 프롬프트 생성")
            run_buttons = [self.generate_btn, self.copy_btn, self.generate_final_prompt_btn]

        for btn in run_buttons:
            run_layout.addWidget(btn)

        line_frame = QFrame()
        line_frame.setFixedHeight(2)
        line_frame.setStyleSheet("background-color: #ccc;")

        right_side_layout.addWidget(run_buttons_container)
        right_side_layout.addWidget(line_frame)
        right_side_layout.addWidget(self.build_tabs)
        center_splitter.addWidget(right_side_widget)

        main_layout.addWidget(center_splitter, stretch=4)

        bottom_splitter = QSplitter(Qt.Horizontal)

        template_manager_frame = QFrame()
        tm_layout = QVBoxLayout(template_manager_frame)
        tm_layout.setContentsMargins(5, 5, 5, 5)
        tm_layout.setSpacing(5)

        self.template_manager_tab = QWidget()
        tm_vertical_layout = QVBoxLayout(self.template_manager_tab)
        tm_vertical_layout.setContentsMargins(5, 5, 5, 5)
        tm_vertical_layout.setSpacing(5)

        self.resource_mode_combo = QComboBox()
        self.resource_mode_combo.addItem("프롬프트")
        self.resource_mode_combo.addItem("상태")
        tm_vertical_layout.addWidget(QLabel("리소스 타입 선택:"))
        tm_vertical_layout.addWidget(self.resource_mode_combo)

        tm_label = QLabel("아래에서 로드하거나 저장할 리소스를 선택하세요:")
        tm_vertical_layout.addWidget(tm_label)

        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderHidden(True)
        tm_vertical_layout.addWidget(self.template_tree)

        self.load_selected_template_btn = QPushButton("📥 선택한 프롬프트 불러오기")
        self.save_as_template_btn = QPushButton("💾 현재 프롬프트로 저장")
        self.template_type_combo = QComboBox()
        self.template_type_combo.addItem("시스템")
        self.template_type_combo.addItem("사용자")
        self.delete_template_btn = QPushButton("❌ 선택한 프롬프트 삭제")
        self.update_template_btn = QPushButton("🔄 현재 프롬프트 업데이트")

        self.backup_button = QPushButton("📦 모든 상태 백업")
        self.restore_button = QPushButton("🔙 백업에서 상태 복원")

        tm_bottom_layout = QVBoxLayout()

        first_row = QHBoxLayout()
        first_row.addWidget(self.load_selected_template_btn)
        tm_bottom_layout.addLayout(first_row)

        second_row = QHBoxLayout()
        self.template_type_label = QLabel("저장 타입:") # 라벨 추가
        second_row.addWidget(self.template_type_label)
        second_row.addWidget(self.template_type_combo)
        second_row.addWidget(self.save_as_template_btn)
        tm_bottom_layout.addLayout(second_row)

        third_row = QHBoxLayout()
        third_row.addWidget(self.delete_template_btn)
        third_row.addWidget(self.update_template_btn)
        tm_bottom_layout.addLayout(third_row)

        fourth_row = QHBoxLayout()
        fourth_row.addWidget(self.backup_button)
        fourth_row.addWidget(self.restore_button)
        tm_bottom_layout.addLayout(fourth_row)

        tm_vertical_layout.addLayout(tm_bottom_layout)
        tm_layout.addWidget(self.template_manager_tab)

        bottom_splitter.addWidget(template_manager_frame)

        gitignore_frame = QFrame()
        gitignore_layout = QVBoxLayout(gitignore_frame)
        gitignore_layout.setContentsMargins(5, 5, 5, 5)
        gitignore_layout.setSpacing(5)

        self.gitignore_tabwidget = QTabWidget()
        self.gitignore_edit_tab = QWidget()
        gitignore_edit_layout = QVBoxLayout(self.gitignore_edit_tab)
        gitignore_edit_layout.setContentsMargins(5, 5, 5, 5)
        gitignore_edit_layout.setSpacing(5)

        self.save_gitignore_btn = QPushButton("💾 .gitignore 저장")
        self.gitignore_edit = CustomTextEdit()
        self.gitignore_edit.setPlaceholderText(".gitignore 내용...")

        gitignore_edit_layout.addWidget(QLabel(".gitignore 보기/편집:"))
        gitignore_edit_layout.addWidget(self.gitignore_edit)
        gitignore_edit_layout.addWidget(self.save_gitignore_btn)
        self.gitignore_tabwidget.addTab(self.gitignore_edit_tab, ".gitignore")

        gitignore_layout.addWidget(self.gitignore_tabwidget)
        bottom_splitter.addWidget(gitignore_frame)

        main_layout.addWidget(bottom_splitter, stretch=2)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.char_count_label = QLabel("Chars: 0")
        self.token_count_label = QLabel("Calculated Total Token: N/A")

        char_status_layout = QHBoxLayout()
        char_status_layout.setContentsMargins(0, 0, 0, 0)
        char_status_layout.setSpacing(10)
        char_status_layout.addWidget(self.char_count_label)

        self.auto_token_calc_check = QCheckBox("토큰 자동 계산")
        self.auto_token_calc_check.setChecked(True)
        char_status_layout.addWidget(self.auto_token_calc_check)
        char_status_layout.addWidget(self.token_count_label)
        char_status_layout.addStretch(1)

        status_container = QWidget()
        status_container.setLayout(char_status_layout)
        self.status_bar.addPermanentWidget(status_container)

        self.controller = MainController(self)

        self.mode_toggle_btn.clicked.connect(self._toggle_mode)
        self.reset_program_btn.clicked.connect(self.controller.reset_program)
        self.save_gitignore_btn.clicked.connect(self.controller.save_gitignore_settings)
        self.select_project_btn.clicked.connect(self.controller.select_project_folder)
        self.select_default_prompt_btn.clicked.connect(lambda: select_default_system_prompt(self))

        self.template_tree.customContextMenuRequested.connect(self.on_tree_view_context_menu)
        # selectionChanged 시그널 연결 복원
        self.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed_handler)

        if self.mode != "Meta Prompt Builder":
            self.generate_tree_btn.clicked.connect(self.controller.generate_directory_tree_structure)
            self.run_xml_parser_btn.clicked.connect(self.controller.run_xml_parser)
            self.generate_all_btn.clicked.connect(self.controller.generate_all_and_copy) # 새 버튼 시그널 연결
        else:
            meta_prompt_path = get_resource_path(os.path.join("resources", "prompts", "system", "META_Prompt.md"))
            if os.path.exists(meta_prompt_path):
                with open(meta_prompt_path, "r", encoding="utf-8") as f:
                    self.system_tab.setText(f.read())

        if self.mode == "Code Enhancer Prompt Builder":
            apply_default_system_prompt(self)
            if not self.system_tab.toPlainText().strip():
                xml_guide_path = get_resource_path(os.path.join("resources", "prompts", "system", "XML_Prompt_Guide.md"))
                if os.path.exists(xml_guide_path):
                    try:
                        with open(xml_guide_path, "r", encoding="utf-8") as f:
                            xml_guide_content = f.read()
                        self.system_tab.setText(xml_guide_content)
                    except Exception as e:
                        print(f"XML_Prompt_Guide.md 로드 중 오류: {e}")
        else:
            apply_default_system_prompt(self)
            if not self.system_tab.toPlainText().strip():
                meta_prompt_path = get_resource_path(os.path.join("resources", "prompts", "system", "META_Prompt.md"))
                if os.path.exists(meta_prompt_path):
                    with open(meta_prompt_path, "r", encoding="utf-8") as f:
                        self.system_tab.setText(f.read())

        if self.mode == "Meta Prompt Builder":
            self.generate_btn.clicked.connect(self.controller.generate_meta_prompt)
            if hasattr(self, "generate_final_prompt_btn"):
                self.generate_final_prompt_btn.clicked.connect(self.controller.generate_final_meta_prompt)
        else:
            self.generate_btn.clicked.connect(self.controller.generate_prompt)

        self.copy_btn.clicked.connect(self.controller.copy_to_clipboard)
        self.load_selected_template_btn.clicked.connect(self.controller.load_selected_item)
        self.save_as_template_btn.clicked.connect(self.controller.save_current_as_item)
        self.delete_template_btn.clicked.connect(self.controller.delete_selected_item)
        self.update_template_btn.clicked.connect(self.controller.update_current_item)
        self.backup_button.clicked.connect(self.controller.backup_all_states_action)
        self.restore_button.clicked.connect(self.controller.restore_states_from_backup_action)
        self.resource_mode_combo.currentIndexChanged.connect(self.controller.load_templates_list) # load_templates_list 호출로 변경

        shortcut = QAction(self)
        shortcut.setShortcut(QKeySequence("Ctrl+Return"))
        if self.mode == "Meta Prompt Builder":
            shortcut.triggered.connect(self.controller.generate_meta_prompt)
        else:
            shortcut.triggered.connect(self.controller.generate_prompt)
        self.addAction(shortcut)

        copy_shortcut = QAction(self)
        copy_shortcut.setShortcut(QKeySequence("Ctrl+C"))
        copy_shortcut.triggered.connect(self.on_copy_shortcut)
        self.addAction(copy_shortcut)

        self.controller.load_templates_list()

        try:
            default_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            os.environ["DEFAULT_PATH"] = default_path
        except Exception as e:
            print(f"초기화 중 오류 발생: {e}")

        save_state_action.triggered.connect(self.controller.save_state_to_default)
        load_state_action.triggered.connect(self.controller.load_state_from_default)
        export_state_action.triggered.connect(self.controller.export_state_to_file)
        import_state_action.triggered.connect(self.controller.import_state_from_file)

        self.status_bar.showMessage("Ready")
        self.resize(1200, 800)
        self.build_tabs.setCurrentIndex(1)

    def reset_state(self):
        self.current_project_folder = None
        self.last_generated_prompt = []
        self.selected_files_data = []
        # 윈도우 제목 리셋
        self.update_window_title()

    def on_copy_shortcut(self):
        if self.build_tabs.currentWidget() == self.prompt_output_tab:
            self.controller.copy_to_clipboard()

    def on_tree_view_context_menu(self, position):
        index = self.template_tree.indexAt(position)
        if not index.isValid():
            return
        item = self.template_tree.currentItem()
        if not item:
            return
        menu = QMenu()
        menu.exec_(self.template_tree.viewport().mapToGlobal(position))

    # 파일/폴더 선택 시 체크 상태 토글 로직 복원
    def on_selection_changed_handler(self, selected, deselected):
        for index in selected.indexes():
            if not index.isValid() or index.column() != 0: # 첫번째 컬럼만 처리
                continue

            # 프록시 모델 인덱스 사용
            proxy_index = index

            # 소스 모델 인덱스 가져오기 (폴더 로딩 확인용)
            src_index = self.checkable_proxy.mapToSource(proxy_index)
            if src_index.isValid() and self.dir_model.isDir(src_index):
                self.checkable_proxy.ensure_loaded(src_index)

            # 현재 체크 상태 가져오기
            current_state = self.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
            # 새 체크 상태 결정 (토글)
            new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
            # 체크 상태 업데이트 (setData 호출)
            self.checkable_proxy.setData(proxy_index, new_state, Qt.CheckStateRole)

        # deselected 인덱스에 대해서도 동일하게 처리 (선택 해제 시에도 토글)
        for index in deselected.indexes():
            if not index.isValid() or index.column() != 0:
                 continue
            proxy_index = index
            # deselected는 이미 로드된 상태일 것이므로 ensure_loaded 생략 가능
            current_state = self.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
            new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
            # 중요: deselected는 이미 선택 해제된 상태이므로, 여기서 setData를 호출하면
            # 의도치 않게 다시 체크될 수 있음. 따라서 deselected는 처리하지 않거나,
            # 선택 모델의 동작 방식(클릭 시 선택/해제 동시 발생 여부)을 고려해야 함.
            # 여기서는 deselected 처리를 제거하여 클릭/드래그 시 선택된 항목만 토글하도록 함.
            pass # deselected 항목은 처리하지 않음


    def get_current_state(self) -> dict:
        checked_paths = self.checkable_proxy.get_all_checked_paths()
        state = {
            "mode": self.mode,
            "project_folder": self.current_project_folder,
            "system_prompt": self.system_tab.toPlainText(),
            "user_prompt": self.user_tab.toPlainText(),
            "last_generated_prompt": self.last_generated_prompt,
            "checked_files": checked_paths
        }
        return state

    def set_current_state(self, state: dict):
        self.reset_state()
        self.mode = state.get("mode", self.mode)
        project_folder = state.get("project_folder", None)
        folder_name = None
        if project_folder and os.path.isdir(project_folder):
            self.current_project_folder = project_folder
            folder_name = os.path.basename(project_folder) # 폴더 이름 추출
            self.project_folder_label.setText(f"현재 프로젝트 폴더: {project_folder}")
            idx = self.dir_model.setRootPathFiltered(project_folder)
            self.tree_view.setRootIndex(self.checkable_proxy.mapFromSource(idx))
            self.statusBar().showMessage(f"Project Folder: {project_folder}")

        self.system_tab.setText(state.get("system_prompt", ""))
        self.user_tab.setText(state.get("user_prompt", ""))
        self.last_generated_prompt = state.get("last_generated_prompt", "")

        self.uncheck_all_files()
        for fpath in state.get("checked_files", []):
            self.controller.toggle_file_check(fpath)

        # 상태 로드 시 윈도우 제목 업데이트
        self.update_window_title(folder_name)

    def uncheck_all_files(self):
        def recurse_uncheck(index):
            row_count = self.dir_model.rowCount(index)
            for i in range(row_count):
                child_index = self.dir_model.index(i, 0, index)
                if child_index.isValid():
                    proxy_index = self.checkable_proxy.mapToSource(child_index)
                    self.checkable_proxy.setData(proxy_index, Qt.Unchecked, Qt.CheckStateRole)
                    if self.dir_model.isDir(child_index):
                        recurse_uncheck(child_index)

        root_index = self.dir_model.index(self.dir_model.rootPath())
        recurse_uncheck(root_index)

    def create_tree_item(self, text, parent=None):
        if parent is None:
            item = QTreeWidgetItem([text])
            self.template_tree.addTopLevelItem(item)
            return item
        else:
            item = QTreeWidgetItem([text])
            parent.addChild(item)
            return item

    def add_new_custom_tab(self):
        new_tab = CustomTextEdit()
        new_tab.setPlaceholderText("New custom tab...")
        idx = self.build_tabs.count() - 1
        self.build_tabs.insertTab(idx, new_tab, "New Tab")

    def _toggle_mode(self):
        if self.mode == "Code Enhancer Prompt Builder":
            self.close()
            new_window = MainWindow(mode="Meta Prompt Builder")
            new_window.resize(1200, 800)
            new_window.show()
            new_window.build_tabs.setCurrentIndex(0)
        else:
            self.close()
            new_window = MainWindow(mode="Code Enhancer Prompt Builder")
            new_window.resize(1200, 800)
            new_window.show()
            new_window.build_tabs.setCurrentIndex(0)

    # 윈도우 제목 업데이트 메서드 수정
    def update_window_title(self, folder_name: Optional[str] = None):
        if folder_name:
            # 폴더명만 표시
            self.setWindowTitle(folder_name)
        else:
            # 기본 제목 표시
            self.setWindowTitle(self.base_title)
