
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel,
    QAbstractItemView, QScrollArea, QToolButton, QFrame, QLineEdit,
    QInputDialog, QMessageBox, QMenuBar, QSplitter, QStyleFactory, QApplication, QToolBar, QMenu, QTreeWidget, QTreeWidgetItem, QComboBox
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor
from PyQt5.QtCore import Qt, QSize, QPoint, QStandardPaths
from config import config
from file_explorer import FilteredFileSystemModel, CheckableProxyModel
from main_controller import MainController
from custom_text_edit import CustomTextEdit

class ClickableFileWidget(QWidget):
    """
    파일명과 용량을 표시하는 위젯.
    마우스 클릭 시 해당 파일 체크 토글을 수행한다.
    """
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Prompt Builder")
        self.resize(1200, 800)

        # Fusion 스타일 적용
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        # QSS로 간단한 테마 적용
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #ffffff;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #eaeaea;
            }
            QToolBar {
                border: none;
                background-color: #fafafa;
                spacing: 4px;
                padding: 4px;
                margin: 2px;
            }
            QToolBar QToolButton {
                border: 1px solid #aaa;
                background-color: #f0f0f0;
                padding: 6px;
                border-radius: 4px;
                margin: 1px;
            }
            QToolBar QToolButton:hover {
                background-color: #e0e0e0;
                border-color: #888;
            }
            QToolBar QToolButton:pressed {
                background-color: #d0d0d0;
            }
            QStatusBar {
                background: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background: white;
                top: -1px;
            }
            QTabBar::tab {
                padding: 8px 15px;
                border: 1px solid #c0c0c0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 80px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                margin-bottom: -1px;
                border-bottom-color: white;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
                background-color: #f0f0f0;
            }
            QTabBar::tab:first:!selected {
                background-color: #E8F5E9;
            }
            QTabBar::tab:first:selected {
                background-color: white;
            }
            QTabBar::tab:nth-child(2):!selected {
                background-color: #E3F2FD;
            }
            QTabBar::tab:nth-child(2):selected {
                background-color: white;
            }
            QTabBar::tab:nth-child(3):!selected {
                background-color: #FFF9C4;
            }
            QTabBar::tab:nth-child(3):selected {
                background-color: white;
            }
            QTabBar::tab:nth-child(4):!selected {
                background-color: #E1F5FE;
            }
            QTabBar::tab:nth-child(4):selected {
                background-color: white;
            }
            QTabBar::tab:nth-child(5):!selected {
                background-color: #E1F5FE;
            }
            QTabBar::tab:nth-child(5):selected {
                background-color: white;
            }
            QTabBar::tab:nth-child(6):!selected {
                background-color: #E1F5FE;
            }
            QTabBar::tab:nth-child(6):selected {
                background-color: white;
            }
        """)

        self.reset_state()

        menubar = QMenuBar()
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("File")
        select_folder_action = QAction("Select Project Folder", self)
        file_menu.addAction(select_folder_action)

        filter_menu = menubar.addMenu("Filter")
        set_extensions_action = QAction("Set Allowed Extensions", self)
        set_excluded_dirs_action = QAction("Set Excluded Directories", self)
        filter_menu.addAction(set_extensions_action)
        filter_menu.addAction(set_excluded_dirs_action)

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

        # 우클릭 메뉴
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.on_tree_view_context_menu)

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

        # 프롬프트 탭
        self.build_tabs = QTabWidget()
        self.build_tabs.setMovable(True)
        self.system_tab = CustomTextEdit()
        self.user_tab = CustomTextEdit()
        self.dir_structure_tab = CustomTextEdit()
        self.dir_structure_tab.setReadOnly(True)
        self.prompt_output_tab = CustomTextEdit()
        self.prompt_output_tab.setReadOnly(False)
        self.xml_input_tab = CustomTextEdit()
        self.xml_input_tab.setPlaceholderText("Enter XML content here...")

        self.system_tab.setPlaceholderText("Enter System Prompt...")
        self.user_tab.setPlaceholderText("Enter User Prompt...")

        self.build_tabs.addTab(self.system_tab, "System")
        self.build_tabs.addTab(self.user_tab, "User")
        self.build_tabs.addTab(self.dir_structure_tab, "File Tree")
        self.build_tabs.addTab(self.prompt_output_tab, "Prompt Output")
        self.build_tabs.addTab(self.xml_input_tab, "XML Input")

        # Template Manager 탭
        self.template_manager_tab = QWidget()
        tm_layout = QVBoxLayout(self.template_manager_tab)
        tm_layout.setContentsMargins(5,5,5,5)

        tm_label = QLabel("Select a template below to load or save:")
        tm_layout.addWidget(tm_label)

        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderHidden(True)
        tm_layout.addWidget(self.template_tree)

        tm_bottom_layout = QHBoxLayout()
        self.load_selected_template_btn = QPushButton("Load Selected Template")
        self.save_as_template_btn = QPushButton("Save Current as Template")

        self.template_type_combo = QComboBox()
        self.template_type_combo.addItem("System")
        self.template_type_combo.addItem("User")

        tm_bottom_layout.addWidget(self.load_selected_template_btn)
        tm_bottom_layout.addWidget(QLabel("Save as:"))
        tm_bottom_layout.addWidget(self.template_type_combo)
        tm_bottom_layout.addWidget(self.save_as_template_btn)

        # 추가 버튼: Delete/Update Template
        self.delete_template_btn = QPushButton("Delete Selected Template")
        self.update_template_btn = QPushButton("Update Current Template")
        tm_bottom_layout.addWidget(self.delete_template_btn)
        tm_bottom_layout.addWidget(self.update_template_btn)

        tm_layout.addLayout(tm_bottom_layout)

        self.build_tabs.addTab(self.template_manager_tab, "Template Manager")

        # 상단 분할
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(self.tree_view)
        top_splitter.addWidget(self.build_tabs)
        top_splitter.setStretchFactor(0, 3)
        top_splitter.setStretchFactor(1, 5)

        main_layout.addWidget(top_splitter, stretch=4)
        main_layout.addWidget(selected_files_frame)

        # Ribbon 툴바
        ribbon = QToolBar("Ribbon")
        ribbon.setMovable(False)
        ribbon.setIconSize(QSize(32,32))
        self.addToolBar(Qt.TopToolBarArea, ribbon)

        self.select_project_btn = QAction(QIcon(), "Select Project", self)
        self.generate_tree_action = QAction(QIcon(), "Generate Tree", self)
        self.generate_action = QAction(QIcon(), "Generate Prompt", self)
        self.copy_action = QAction(QIcon(), "Copy to Clipboard", self)
        self.add_tab_action = QAction(QIcon(), "Add Tab", self)
        self.remove_tab_action = QAction(QIcon(), "Remove Tab", self)
        self.run_xml_parser_action = QAction(QIcon(), "Run XML Parser", self)

        ribbon.addAction(self.select_project_btn)
        ribbon.addAction(self.generate_tree_action)
        ribbon.addAction(self.generate_action)
        ribbon.addAction(self.copy_action)
        ribbon.addAction(self.add_tab_action)
        ribbon.addAction(self.remove_tab_action)
        ribbon.addAction(self.run_xml_parser_action)

        self.run_xml_parser_action.setCheckable(True)
        ribbon_widget = ribbon.widgetForAction(self.run_xml_parser_action)
        if ribbon_widget:
            ribbon_widget.setStyleSheet("background-color: #E1F5FE;")

        # 하단 필터 설정 영역
        bottom_config_widget = QWidget()
        bottom_config_layout = QHBoxLayout(bottom_config_widget)
        bottom_config_layout.setContentsMargins(0,0,0,0)
        bottom_config_layout.setSpacing(5)

        self.extensions_edit = QLineEdit(",".join(config.allowed_extensions))
        self.excluded_dirs_edit = QLineEdit(",".join(config.excluded_dirs))
        self.apply_filter_btn = QPushButton("Apply Filters")

        bottom_config_layout.addWidget(QLabel("Allowed Extensions:"))
        bottom_config_layout.addWidget(self.extensions_edit)
        bottom_config_layout.addWidget(QLabel("Excluded Dirs:"))
        bottom_config_layout.addWidget(self.excluded_dirs_edit)
        bottom_config_layout.addWidget(self.apply_filter_btn)
        bottom_config_layout.addStretch(1)

        main_layout.addWidget(bottom_config_widget)

        self.char_count_label = QLabel("Chars: 0")
        self.status_bar = QStatusBar()

        char_status_layout = QVBoxLayout()
        char_status_layout.setContentsMargins(0,0,0,0)
        char_status_layout.setSpacing(2)
        char_container = QWidget()
        char_status_layout.addWidget(self.char_count_label)
        char_status_layout.addWidget(self.status_bar)
        char_container.setLayout(char_status_layout)
        main_layout.addWidget(char_container)

        self.controller = MainController(self)

        select_folder_action.triggered.connect(self.controller.select_project_folder)
        set_extensions_action.triggered.connect(self.controller.set_allowed_extensions)
        set_excluded_dirs_action.triggered.connect(self.controller.set_excluded_dirs)

        self.tree_view.doubleClicked.connect(self.controller.load_file_preview)
        self.checkable_proxy.dataChanged.connect(self.controller.on_data_changed)
        self.tree_view.selectionModel().selectionChanged.connect(self.controller.on_selection_changed)

        self.select_project_btn.triggered.connect(self.controller.select_project_folder)
        self.generate_action.triggered.connect(self.controller.generate_prompt)
        self.copy_action.triggered.connect(self.controller.copy_to_clipboard)
        self.apply_filter_btn.clicked.connect(self.controller.apply_filters)
        self.selected_files_toolbtn.clicked.connect(self.toggle_selected_files)
        self.generate_tree_action.triggered.connect(self.controller.generate_directory_tree_structure)
        self.add_tab_action.triggered.connect(self.add_custom_tab)
        self.remove_tab_action.triggered.connect(self.remove_current_tab)
        self.run_xml_parser_action.triggered.connect(self.controller.run_xml_parser)

        # 템플릿 관련 버튼
        self.load_selected_template_btn.clicked.connect(self.controller.load_selected_template)
        self.save_as_template_btn.clicked.connect(self.controller.save_current_as_template)
        self.delete_template_btn.clicked.connect(self.controller.delete_selected_template)
        self.update_template_btn.clicked.connect(self.controller.update_current_template)

        # Ctrl+Enter -> 프롬프트 생성
        shortcut = QAction(self)
        shortcut.setShortcut(QKeySequence("Ctrl+Return"))
        shortcut.triggered.connect(self.controller.generate_prompt)
        self.addAction(shortcut)

        # Ctrl+C -> Prompt Output 탭 선택 시 복사
        copy_shortcut = QAction(self)
        copy_shortcut.setShortcut(QKeySequence("Ctrl+C"))
        copy_shortcut.triggered.connect(self.on_copy_shortcut)
        self.addAction(copy_shortcut)

        # 초기 템플릿 목록 로드
        self.controller.load_templates_list()

        try:
            default_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            os.environ['DEFAULT_PATH'] = default_path
        except Exception as e:
            print(f"초기화 중 오류 발생: {e}")

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

    def update_char_count(self):
        total_chars = 0
        project_folder = self.current_project_folder
        checked_files = self.checkable_proxy.get_checked_files()
        for fpath in checked_files:
            if os.path.isfile(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8') as fp:
                        content = fp.read()
                    total_chars += len(content)
                except:
                    pass
        self.char_count_label.setText(f"Chars: {format(total_chars, ',')}")

    def add_custom_tab(self):
        tab_name, ok = QInputDialog.getText(self, "Add Tab", "Enter tab name:")
        if ok and tab_name.strip():
            new_tab = CustomTextEdit()
            self.build_tabs.insertTab(2, new_tab, tab_name.strip())
            self.status_bar.showMessage(f"Tab '{tab_name.strip()}' added!")

    def remove_current_tab(self):
        current_index = self.build_tabs.currentIndex()
        if current_index <= 5:
            QMessageBox.information(self, "Info", "Cannot remove core tabs.")
            return
        tab_name = self.build_tabs.tabText(current_index)
        self.build_tabs.removeTab(current_index)
        self.status_bar.showMessage(f"Tab '{tab_name}' removed!")

    def on_tree_view_context_menu(self, pos):
        index = self.tree_view.indexAt(pos)
        if not index.isValid():
            return
        src_index = self.checkable_proxy.mapToSource(index)
        file_path = self.dir_model.filePath(src_index)
        rename_action = QAction("Rename", self)
        delete_action = QAction("Delete", self)
        rename_action.triggered.connect(lambda: self.controller.rename_item(file_path))
        delete_action.triggered.connect(lambda: self.controller.delete_item(file_path))
        menu = QMenu(self)
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.exec_(self.tree_view.viewport().mapToGlobal(pos))

    def on_copy_shortcut(self):
        if self.build_tabs.currentWidget() == self.prompt_output_tab:
            self.controller.copy_to_clipboard()
