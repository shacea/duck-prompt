import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QScrollArea, QToolButton, QFrame, QLineEdit,
    QInputDialog, QMessageBox, QMenuBar, QSplitter, QStyleFactory, QApplication, QToolBar, QMenu, QTreeWidget, QTreeWidgetItem, QComboBox
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont
from PyQt5.QtCore import Qt, QSize, QStandardPaths

from config import config
from file_explorer import FilteredFileSystemModel, CheckableProxyModel
from main_controller import MainController
from custom_text_edit import CustomTextEdit
from tab_manager import is_tab_deletable  # 탭 삭제 가능 여부 판단 함수

def load_meta_prompt():
    meta_prompt_path = os.path.join("resources", "Meta_Prompt.md")
    try:
        with open(meta_prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "<Meta Prompt Not Found>"

from PyQt5.QtWidgets import QTabBar

class CustomTabBar(QTabBar):
    def __init__(self, parent: QTabWidget, main_window: QMainWindow):
        super().__init__(parent)
        self.main_window = main_window
        self.setTabsClosable(False)
        self.setMovable(True)
        self.addTab("+")  # 플러스 탭 추가

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            index = self.tabAt(pos)
            # 탭 텍스트가 "+"라면 새 탭 추가
            if index >= 0 and self.tabText(index) == "+":
                self.main_window.add_new_custom_tab()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        # 가운데 버튼으로 탭 삭제 처리
        if event.button() == Qt.MiddleButton:
            pos = event.pos()
            index = self.tabAt(pos)
            if index >= 0:
                tab_text = self.tabText(index)
                # 탭 삭제 가능 여부 판단
                if is_tab_deletable(tab_text):
                    self.parent().removeTab(index)
                else:
                    QMessageBox.warning(None, "경고", "이 탭은 제거할 수 없습니다.")
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        # 더블클릭 시 탭 이름 변경 (삭제 가능 탭만)
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            index = self.tabAt(pos)
            if index >= 0:
                tab_text = self.tabText(index)
                if is_tab_deletable(tab_text):
                    new_name, ok = QInputDialog.getText(None, "Rename Tab", "Enter new tab name:", text=tab_text)
                    if ok and new_name.strip():
                        self.setTabText(index, new_name.strip())
        super().mouseDoubleClickEvent(event)


class ClickableFileWidget(QWidget):
    def __init__(self, file_path, size, controller):
        super().__init__()
        self.setWindowTitle("Duck Prompt Builder")
        icon = QIcon("resources/rubber_duck.ico")
        self.setWindowIcon(icon)
        self.file_path = file_path
        self.controller = controller
        self.setCursor(QCursor(Qt.PointingHandCursor))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5)
        layout.setSpacing(2)
        fname_label = QLabel(os.path.basename(file_path))
        fsize_label = QLabel(f"{size:,} bytes")
        layout.addWidget(fname_label)
        layout.addWidget(fsize_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.controller.toggle_file_check(self.file_path)
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, mode="Code Enhancer Prompt Builder"):
        super().__init__()
        self.mode = mode
        self.setWindowTitle("LLM Prompt Builder")
        self.resize(1200, 800)

        QApplication.setStyle(QStyleFactory.create("Fusion"))

        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        mode_menu = menubar.addMenu("Mode")

        switch_to_code_action = QAction("Switch to Code Enhancer Builder", self)
        switch_to_meta_action = QAction("Switch to Meta Prompt Builder", self)

        def restart_with_mode(mode):
            self.close()
            new_window = MainWindow(mode=mode)
            new_window.show()

        switch_to_code_action.triggered.connect(lambda: restart_with_mode("Code Enhancer Prompt Builder"))
        switch_to_meta_action.triggered.connect(lambda: restart_with_mode("Meta Prompt Builder"))

        mode_menu.addAction(switch_to_code_action)
        mode_menu.addAction(switch_to_meta_action)

        self.reset_state()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5,5,5,5)
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

        # Template Manager 탭을 사이드바 형태로 만들기 위해 별도 위젯으로 구성
        self.template_manager_tab = QWidget()
        tm_layout = QVBoxLayout(self.template_manager_tab)
        tm_layout.setContentsMargins(5,5,5,5)
        tm_layout.setSpacing(5)
        tm_label = QLabel("Select a prompt below to load or save:")
        tm_layout.addWidget(tm_label)
        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderHidden(True)
        tm_layout.addWidget(self.template_tree)

        # 버튼과 콤보박스 초기화
        self.load_selected_template_btn = QPushButton("Load Selected Prompt")
        self.save_as_template_btn = QPushButton("Save Current as Prompt")
        self.template_type_combo = QComboBox()
        self.template_type_combo.addItem("System")
        self.template_type_combo.addItem("User")
        self.delete_template_btn = QPushButton("Delete Selected Prompt")
        self.update_template_btn = QPushButton("Update Current Prompt")

        # 버튼들을 3단으로 재배치
        tm_bottom_layout = QVBoxLayout()  # 수직 레이아웃으로 변경
        
        # 첫 번째 줄: Load Selected Template
        first_row = QHBoxLayout()
        first_row.addWidget(self.load_selected_template_btn)
        tm_bottom_layout.addLayout(first_row)
        
        # 두 번째 줄: Save as + combo box + Save Current as Template
        second_row = QHBoxLayout()
        second_row.addWidget(QLabel("Save as:"))
        second_row.addWidget(self.template_type_combo)
        second_row.addWidget(self.save_as_template_btn)
        tm_bottom_layout.addLayout(second_row)
        
        # 세 번째 줄: Delete Selected Template + Update Current Template
        third_row = QHBoxLayout()
        third_row.addWidget(self.delete_template_btn)
        third_row.addWidget(self.update_template_btn)
        tm_bottom_layout.addLayout(third_row)
        
        tm_layout.addLayout(tm_bottom_layout)

        # 빌드 탭
        self.build_tabs = QTabWidget()
        custom_tab_bar = CustomTabBar(self.build_tabs, self)
        self.build_tabs.setTabBar(custom_tab_bar)

        self.system_tab = CustomTextEdit()
        self.system_tab.setPlaceholderText("Enter System Prompt...")
        self.build_tabs.addTab(self.system_tab, "System")

        self.user_tab = CustomTextEdit()
        self.user_tab.setPlaceholderText("Enter User Prompt...")
        self.build_tabs.addTab(self.user_tab, "User")

        self.dir_structure_tab = CustomTextEdit()
        self.dir_structure_tab.setReadOnly(True)
        if self.mode != "Meta Prompt Builder":
            self.build_tabs.addTab(self.dir_structure_tab, "File Tree")

        self.prompt_output_tab = CustomTextEdit()
        self.prompt_output_tab.setReadOnly(False)
        # 가독성 좋은 폰트와 여백 조정
        self.prompt_output_tab.setFont(QFont("Consolas", 10))
        self.prompt_output_tab.setStyleSheet("QTextEdit { padding: 10px; }")
        if self.mode == "Meta Prompt Builder":
            self.build_tabs.addTab(self.prompt_output_tab, "Meta Prompt Output")
        else:
            self.build_tabs.addTab(self.prompt_output_tab, "Prompt Output")

        self.xml_input_tab = CustomTextEdit()
        self.xml_input_tab.setPlaceholderText("Enter XML content here...")
        if self.mode != "Meta Prompt Builder":
            self.build_tabs.addTab(self.xml_input_tab, "XML Input")

        self.selected_files_toolbtn = QToolButton()
        self.selected_files_toolbtn.setText("Selected Files")
        self.selected_files_toolbtn.setCheckable(True)
        self.selected_files_toolbtn.setChecked(True)
        self.selected_files_toolbtn.setArrowType(Qt.DownArrow)

        self.selected_files_container = QWidget()
        self.selected_files_layout = QVBoxLayout(self.selected_files_container)
        self.selected_files_layout.setContentsMargins(5,5,5,5)
        self.selected_files_layout.setSpacing(5)

        self.selected_files_scroll = QScrollArea()
        self.selected_files_scroll.setWidgetResizable(True)
        self.selected_files_list_widget = QWidget()
        self.selected_files_list_layout = QHBoxLayout(self.selected_files_list_widget)
        self.selected_files_list_layout.setContentsMargins(0,0,0,0)
        self.selected_files_list_layout.setSpacing(5)
        self.selected_files_list_widget.setStyleSheet("background-color: white; border: 1px solid #c0c0c0;")
        self.selected_files_scroll.setWidget(self.selected_files_list_widget)
        self.selected_files_layout.addWidget(self.selected_files_scroll)

        selected_files_frame = QFrame()
        sf_main_layout = QVBoxLayout(selected_files_frame)
        sf_main_layout.setContentsMargins(0,0,0,0)
        sf_main_layout.setSpacing(2)
        sf_main_layout.addWidget(self.selected_files_toolbtn)
        sf_main_layout.addWidget(self.selected_files_container)

        # 상단에 프로젝트 폴더 선택 버튼 크게 배치
        self.select_project_btn_large = QPushButton("Select Project Folder")
        self.select_project_btn_large.setFixedHeight(40)
        font = self.select_project_btn_large.font()
        font.setPointSize(12)
        font.setBold(True)
        self.select_project_btn_large.setFont(font)

        # 왼쪽 사이드바: Template Manager 위, File Explorer 아래 (Meta 모드에서는 File Explorer 없음)
        left_side_widget = QWidget()
        left_side_layout = QVBoxLayout(left_side_widget)
        left_side_layout.setContentsMargins(0,0,0,0)
        left_side_layout.setSpacing(5)
        left_side_layout.addWidget(self.select_project_btn_large)
        left_side_layout.addWidget(self.template_manager_tab)

        if self.mode != "Meta Prompt Builder":
            left_side_layout.addWidget(self.tree_view)

        # 수직으로 Template Manager와 파일 탐색기 배치 후, 우측에 빌드 탭
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(left_side_widget)
        top_splitter.addWidget(self.build_tabs)
        top_splitter.setStretchFactor(0, 2)
        top_splitter.setStretchFactor(1, 5)

        main_layout.addWidget(top_splitter, stretch=4)
        main_layout.addWidget(selected_files_frame)

        ribbon = QToolBar("Ribbon")
        ribbon.setMovable(False)
        ribbon.setIconSize(QSize(32,32))
        self.addToolBar(Qt.TopToolBarArea, ribbon)

        # 버튼 재배치: "Run XML Parser"를 "Copy to Clipboard" 오른쪽으로 이동
        if self.mode != "Meta Prompt Builder":
            self.generate_tree_action = QAction(QIcon(), "Generate Tree", self)
            self.run_xml_parser_action = QAction(QIcon(), "Run XML Parser", self)
            self.generate_action = QAction(QIcon(), "Generate Prompt", self)
            self.copy_action = QAction(QIcon(), "Copy to Clipboard", self)

            ribbon.addAction(self.generate_tree_action)
            ribbon.addSeparator()
            ribbon.addAction(self.generate_action)
            ribbon.addSeparator()
            ribbon.addAction(self.copy_action)
            # "Copy to Clipboard" 오른쪽에 Run XML Parser
            ribbon.addAction(self.run_xml_parser_action)
        else:
            self.generate_action = QAction(QIcon(), "Generate META Prompt", self)
            self.copy_action = QAction(QIcon(), "Copy to Clipboard", self)
            ribbon.addAction(self.generate_action)
            ribbon.addSeparator()
            ribbon.addAction(self.copy_action)

        # 필터 기능 제거로 인한 하단 위젯 삭제
        # char/token count와 status_bar만 하단에 남김
        self.char_count_label = QLabel("Chars: 0")
        self.token_count_label = QLabel("Calculated Total Token: N/A")

        self.status_bar = QStatusBar()

        char_status_layout = QHBoxLayout()
        char_status_layout.setContentsMargins(0,0,0,0)
        char_status_layout.setSpacing(10)
        char_status_layout.addWidget(self.char_count_label)

        self.auto_token_calc_check = QCheckBox("토큰 자동 계산")
        self.auto_token_calc_check.setChecked(True)
        char_status_layout.addWidget(self.auto_token_calc_check)

        char_status_layout.addWidget(self.token_count_label)
        char_status_layout.addStretch(1)

        char_container = QWidget()
        cmain_layout = QVBoxLayout(char_container)
        cmain_layout.setContentsMargins(0,0,0,0)
        cmain_layout.setSpacing(2)
        cmain_layout.addLayout(char_status_layout)
        cmain_layout.addWidget(self.status_bar)

        main_layout.addWidget(char_container)

        self.controller = MainController(self)

        # 프로젝트 폴더 선택 버튼 연결
        if self.mode != "Meta Prompt Builder":
            self.select_project_btn_large.clicked.connect(self.controller.select_project_folder)
            self.generate_tree_action.triggered.connect(self.controller.generate_directory_tree_structure)
            self.run_xml_parser_action.triggered.connect(self.controller.run_xml_parser)
        else:
            self.select_project_btn_large.setDisabled(True)  # Meta 모드에서는 폴더 선택 불필요

        if self.mode == "Meta Prompt Builder":
            self.generate_action.triggered.connect(self.controller.generate_meta_prompt)
        else:
            self.generate_action.triggered.connect(self.controller.generate_prompt)

        self.copy_action.triggered.connect(self.controller.copy_to_clipboard)
        self.selected_files_toolbtn.clicked.connect(self.toggle_selected_files)

        self.load_selected_template_btn.clicked.connect(self.controller.load_selected_template)
        self.save_as_template_btn.clicked.connect(self.controller.save_current_as_template)
        self.delete_template_btn.clicked.connect(self.controller.delete_selected_template)
        self.update_template_btn.clicked.connect(self.controller.update_current_template)

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

        if self.mode == "Meta Prompt Builder":
            # File Tree, XML Input 탭 제거
            # 이미 추가되지 않았거나 제거함
            pass

        # 시작 시 Template Manager UI에 포커스
        # Template Manager는 이제 사이드바 형태이므로 탭 전환 대신 포커스만 유지
        self.status_bar.showMessage("Ready")

    def reset_state(self):
        self.current_project_folder = None
        self.last_generated_prompt = []
        self.selected_files_data = []

    def toggle_selected_files(self):
        if self.selected_files_toolbtn.isChecked():
            self.selected_files_toolbtn.setArrowType(Qt.DownArrow)
            self.selected_files_container.show()
        else:
            self.selected_files_toolbtn.setArrowType(Qt.RightArrow)
            self.selected_files_container.hide()

    def update_selected_files_panel(self):
        while self.selected_files_list_layout.count():
            item = self.selected_files_list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for fpath, size in self.selected_files_data:
            file_widget = ClickableFileWidget(fpath, size, self.controller)
            self.selected_files_list_layout.addWidget(file_widget)

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
        check_action = menu.addAction("Toggle Check")
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        action = menu.exec_(self.tree_view.viewport().mapToGlobal(position))

        if action == check_action:
            self.controller.toggle_file_check(file_path)
        elif action == rename_action:
            self.controller.rename_item(file_path)
        elif action == delete_action:
            self.controller.delete_item(file_path)

    def add_new_custom_tab(self):
        new_tab = CustomTextEdit()
        plus_index = self.build_tabs.count() - 1  # '+' 탭 위치는 항상 마지막
        self.build_tabs.insertTab(plus_index, new_tab, "New Tab")
        self.build_tabs.setCurrentWidget(new_tab)
        self.status_bar.showMessage("새 탭이 추가되었습니다: New Tab")

    def on_selection_changed_handler(self, selected, deselected):
        self.controller.on_selection_changed(selected, deselected)
