
import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QScrollArea, QToolButton, QFrame, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox
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
        self.setWindowTitle("Duck Prompt Builder")

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

        self.dir_model = FilteredFileSystemModel(config)
        self.dir_model.setRootPath(os.path.expanduser("~"))

        def get_current_folder():
            return self.current_project_folder

        self.checkable_proxy = CheckableProxyModel(self.dir_model, get_current_folder)
        self.checkable_proxy.setSourceModel(self.dir_model)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.checkable_proxy)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)
        self.tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.on_tree_view_context_menu)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed_handler)

        self.template_manager_tab = QWidget()
        tm_layout = QVBoxLayout(self.template_manager_tab)
        tm_layout.setContentsMargins(5, 5, 5, 5)
        tm_layout.setSpacing(5)

        self.resource_mode_combo = QComboBox()
        self.resource_mode_combo.addItem("프롬프트")
        self.resource_mode_combo.addItem("상태")
        tm_layout.addWidget(QLabel("리소스 타입 선택:"))
        tm_layout.addWidget(self.resource_mode_combo)

        tm_label = QLabel("아래에서 로드하거나 저장할 리소스를 선택하세요:")
        tm_layout.addWidget(tm_label)
        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderHidden(True)
        tm_layout.addWidget(self.template_tree)

        self.template_tree.itemDoubleClicked.connect(lambda item, col: self.controller.load_selected_item())

        self.load_selected_template_btn = QPushButton("선택한 프롬프트 불러오기")
        self.save_as_template_btn = QPushButton("현재 프롬프트로 저장")
        self.template_type_combo = QComboBox()
        self.template_type_combo.addItem("시스템")
        self.template_type_combo.addItem("사용자")
        self.delete_template_btn = QPushButton("선택한 프롬프트 삭제")
        self.update_template_btn = QPushButton("현재 프롬프트 업데이트")

        self.backup_button = QPushButton("모든 상태 백업")
        self.restore_button = QPushButton("백업에서 상태 복원")

        tm_bottom_layout = QVBoxLayout()

        first_row = QHBoxLayout()
        first_row.addWidget(self.load_selected_template_btn)
        tm_bottom_layout.addLayout(first_row)

        second_row = QHBoxLayout()
        second_row.addWidget(QLabel("저장 타입:"))
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

        tm_layout.addLayout(tm_bottom_layout)

        self.build_tabs = QTabWidget()
        custom_tab_bar = CustomTabBar(self.build_tabs, self)
        self.build_tabs.setTabBar(custom_tab_bar)

        if self.mode == "Meta Prompt Builder":
            system_tab_label = "메타 프롬프트 템플릿"
            user_tab_label = "메타 사용자 입력"
            copy_btn_label = "메타 프롬프트 복사"
        else:
            system_tab_label = "시스템"
            user_tab_label = "사용자"
            copy_btn_label = "클립보드에 복사"

        self.system_tab = CustomTextEdit()
        if self.mode == "Meta Prompt Builder":
            self.system_tab.setPlaceholderText("Enter META Prompt Template...")
        else:
            self.system_tab.setPlaceholderText("Enter System Prompt...")
        self.build_tabs.addTab(self.system_tab, system_tab_label)

        self.user_tab = CustomTextEdit()
        if self.mode == "Meta Prompt Builder":
            self.user_tab.setPlaceholderText("Enter META User Prompt...")
        else:
            self.user_tab.setPlaceholderText("Enter User Prompt...")
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

        self.mode_toggle_btn = QPushButton("모드 전환")
        self.mode_toggle_btn.setFixedHeight(40)
        font = self.mode_toggle_btn.font()
        font.setPointSize(12)
        font.setBold(True)
        self.mode_toggle_btn.setFont(font)
        self.mode_toggle_btn.setStyleSheet("QPushButton { background-color: #e0f7fa; border: 1px solid #b2ebf2; border-radius: 5px;}")

        def toggle_mode():
            if self.mode == "Code Enhancer Prompt Builder":
                restart_with_mode("Meta Prompt Builder")
            else:
                restart_with_mode("Code Enhancer Prompt Builder")

        self.mode_toggle_btn.clicked.connect(toggle_mode)

        self.select_project_btn_large = QPushButton("프로젝트 폴더 선택")
        self.select_project_btn_large.setFixedHeight(40)
        font2 = self.select_project_btn_large.font()
        font2.setPointSize(12)
        font2.setBold(True)
        self.select_project_btn_large.setFont(font2)
        self.select_project_btn_large.setStyleSheet("QPushButton { background-color: #e8f5e9; border: 1px solid #c8e6c9; border-radius: 5px;}")

        top_buttons_layout = QHBoxLayout()
        top_buttons_layout.addWidget(self.mode_toggle_btn)
        top_buttons_layout.addWidget(self.select_project_btn_large)

        left_side_widget = QWidget()
        left_side_layout = QVBoxLayout(left_side_widget)
        left_side_layout.setContentsMargins(0, 0, 0, 0)
        left_side_layout.setSpacing(5)

        left_side_layout.addLayout(top_buttons_layout)

        if self.mode != "Meta Prompt Builder":
            # 아래 부분에서 높이를 기존 [350, 650]에서 [420, 580]으로 변경했어!
            splitter_left = QSplitter(Qt.Vertical)
            splitter_left.addWidget(self.template_manager_tab)
            splitter_left.addWidget(self.tree_view)
            splitter_left.setSizes([420, 580])  # 20% 증가 (350 -> 420)
            left_side_layout.addWidget(splitter_left)
        else:
            left_side_layout.addWidget(self.template_manager_tab)

        right_side_widget = QWidget()
        right_side_layout = QVBoxLayout(right_side_widget)
        right_side_layout.setContentsMargins(0, 0, 0, 0)
        right_side_layout.setSpacing(0)

        self.run_buttons_container = QWidget()
        run_layout = QHBoxLayout(self.run_buttons_container)
        run_layout.setContentsMargins(5, 5, 5, 5)
        run_layout.setSpacing(10)
        run_layout.setAlignment(Qt.AlignLeft)

        if self.mode != "Meta Prompt Builder":
            self.generate_tree_btn = QPushButton("트리 생성")
            self.generate_btn = QPushButton("프롬프트 생성")
            self.copy_btn = QPushButton(copy_btn_label)
            self.run_xml_parser_btn = QPushButton("XML 파서 실행")
            run_buttons = [self.generate_tree_btn, self.generate_btn, self.copy_btn, self.run_xml_parser_btn]
        else:
            self.generate_btn = QPushButton("메타 프롬프트 생성")
            self.copy_btn = QPushButton(copy_btn_label)
            self.generate_final_prompt_btn = QPushButton("최종 프롬프트 생성")
            run_buttons = [self.generate_btn, self.copy_btn, self.generate_final_prompt_btn]

        for btn in run_buttons:
            run_layout.addWidget(btn)

        line_frame = QFrame()
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)

        right_side_layout.addWidget(self.run_buttons_container)
        right_side_layout.addWidget(line_frame)
        right_side_layout.addWidget(self.build_tabs)

        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(left_side_widget)
        top_splitter.addWidget(right_side_widget)
        top_splitter.setStretchFactor(0, 2)
        top_splitter.setStretchFactor(1, 5)

        main_layout.addWidget(top_splitter, stretch=4)

        self.char_count_label = QLabel("Chars: 0")
        self.token_count_label = QLabel("Calculated Total Token: N/A")

        self.status_bar = QStatusBar()

        char_status_layout = QHBoxLayout()
        char_status_layout.setContentsMargins(0, 0, 0, 0)
        char_status_layout.setSpacing(10)
        char_status_layout.addWidget(self.char_count_label)

        self.auto_token_calc_check = QCheckBox("토큰 자동 계산")
        self.auto_token_calc_check.setChecked(True)
        char_status_layout.addWidget(self.auto_token_calc_check)

        char_status_layout.addWidget(self.token_count_label)
        char_status_layout.addStretch(1)

        char_container = QWidget()
        cmain_layout = QVBoxLayout(char_container)
        cmain_layout.setContentsMargins(0, 0, 0, 0)
        cmain_layout.setSpacing(2)
        cmain_layout.addLayout(char_status_layout)
        cmain_layout.addWidget(self.status_bar)

        main_layout.addWidget(char_container)

        self.controller = MainController(self)

        if self.mode != "Meta Prompt Builder":
            self.select_project_btn_large.clicked.connect(self.controller.select_project_folder)
            self.generate_tree_btn.clicked.connect(self.controller.generate_directory_tree_structure)
            self.run_xml_parser_btn.clicked.connect(self.controller.run_xml_parser)
        else:
            meta_prompt_path = get_resource_path(os.path.join("resources", "prompts", "system", "META_Prompt.md"))
            if os.path.exists(meta_prompt_path):
                with open(meta_prompt_path, 'r', encoding='utf-8') as f:
                    self.system_tab.setText(f.read())

        if self.mode == "Meta Prompt Builder":
            self.generate_btn.clicked.connect(self.controller.generate_meta_prompt)
            if hasattr(self, 'generate_final_prompt_btn'):
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

        self.resource_mode_combo.currentIndexChanged.connect(self.controller.on_mode_changed)

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
            os.environ['DEFAULT_PATH'] = default_path
        except Exception as e:
            print(f"초기화 중 오류 발생: {e}")

        save_state_action.triggered.connect(self.controller.save_state_to_default)
        load_state_action.triggered.connect(self.controller.load_state_from_default)
        export_state_action.triggered.connect(self.controller.export_state_to_file)
        import_state_action.triggered.connect(self.controller.import_state_from_file)

        self.status_bar.showMessage("Ready")

        self.build_tabs.setCurrentIndex(0)
        self.show()
        self.resize(1200, 800)

    def reset_state(self):
        self.current_project_folder = None
        self.last_generated_prompt = []
        self.selected_files_data = []

    def on_copy_shortcut(self):
        if self.build_tabs.currentWidget() == self.prompt_output_tab:
            self.controller.copy_to_clipboard()

    def on_tree_view_context_menu(self, position):
        if self.mode == "Meta Prompt Builder":
            return

        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        src_index = self.checkable_proxy.mapToSource(index)
        file_path = self.dir_model.filePath(src_index)

        menu = QMenu()
        check_action = menu.addAction("체크 토글")
        rename_action = menu.addAction("이름 변경")
        delete_action = menu.addAction("삭제")

        action = menu.exec_(self.tree_view.viewport().mapToGlobal(position))

        if action == check_action:
            self.controller.toggle_file_check(file_path)
        elif action == rename_action:
            self.controller.rename_item(file_path)
        elif action == delete_action:
            self.controller.delete_item(file_path)

    def add_new_custom_tab(self):
        new_tab = CustomTextEdit()
        plus_index = self.build_tabs.count() - 1
        self.build_tabs.insertTab(plus_index, new_tab, "New Tab")
        self.build_tabs.setCurrentWidget(new_tab)
        self.status_bar.showMessage("New tab added: New Tab")

    def on_selection_changed_handler(self, selected, deselected):
        self.controller.on_selection_changed(selected, deselected)

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
        if project_folder and os.path.isdir(project_folder):
            self.current_project_folder = project_folder
            idx = self.dir_model.setRootPathFiltered(project_folder)
            self.tree_view.setRootIndex(self.checkable_proxy.mapFromSource(idx))
            self.status_bar.showMessage(f"Project Folder: {project_folder}")

        self.system_tab.setText(state.get("system_prompt", ""))
        self.user_tab.setText(state.get("user_prompt", ""))
        self.last_generated_prompt = state.get("last_generated_prompt", "")

        self.uncheck_all_files()
        for fpath in state.get("checked_files", []):
            self.controller.toggle_file_check(fpath)

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
