import os
import io
import logging
import datetime
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import ( # PyQt5 -> PyQt6
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget,
    QStatusBar, QPushButton, QLabel, QCheckBox, QGroupBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu,
    QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox,
    QFrame, QLineEdit, QDialog, QListWidget, QListWidgetItem, QStyle
)
from PyQt6.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont, QDesktopServices, QPixmap, QImage, QAction, QKeyEvent # PyQt5 -> PyQt6, QAction, QKeyEvent 추가
from PyQt6.QtCore import Qt, QSize, QStandardPaths, QModelIndex, QItemSelection, QUrl, QThread, pyqtSignal, QObject, QBuffer, QIODevice, QTimer, QEvent # PyQt5 -> PyQt6, QEvent 추가

# FAH 아키텍처에 필요한 서비스만 import
from src.features.database.organisms.database_service import DatabaseService
from src.features.config.organisms.config_service import ConfigurationService
# ... 다른 필요한 FAH 서비스들 ...

# UI 관련 import
from src.ui.models.file_system_models import CachedFileSystemModel, CheckableProxyModel
from src.ui.widgets.custom_text_edit import CustomTextEdit
from src.ui.widgets.custom_tab_bar import CustomTabBar
from src.utils.helpers import get_resource_path
from src.utils.notifications import show_notification

# Pillow import 시도
try:
    from PIL import Image
    from PIL.ImageQt import ImageQt
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False

# 로거 설정
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    # 자동 저장 타이머 시그널
    state_changed_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._initialized = False
        self.base_title = "DuckPrompt"
        self.update_window_title()

        QApplication.setStyle(QStyleFactory.create("Fusion"))

        # --- 상태 변수 ---
        self.current_project_folder: Optional[str] = None
        self.last_generated_prompt: str = ""
        self.attached_items: List[Dict[str, Any]] = []
        self.api_call_start_time: Optional[datetime.datetime] = None
        self.api_timer = QTimer(self)
        self.api_timer.timeout.connect(self._update_api_elapsed_time)

        # --- 자동 저장 타이머 ---
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(30000)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.save_state_to_default_handler) # 핸들러 연결

        # --- UI 구성 ---
        # UI 생성 로직은 외부 모듈로 분리 (가정)
        # from .main_window_setup_ui import create_menu_bar, create_widgets, create_layout, create_status_bar
        # create_menu_bar(self)
        # create_widgets(self)
        # create_layout(self)
        # create_status_bar(self)
        # 참고: 실제로는 이 파일에 UI 생성 코드가 모두 포함되어 있음.
        # 여기서는 설명을 위해 분리된 것처럼 가정합니다.
        # 기존 코드에서 UI 생성 부분을 그대로 가져옵니다.
        self.setup_ui() # UI 생성 메서드 호출

        # 시그널 연결 (새로운 FAH 컨트롤러에 연결하는 로직은 app.py에서 처리)
        # 자동 저장 타이머 시그널만 내부적으로 연결
        self.state_changed_signal.connect(self.restart_auto_save_timer)

        self._initialized = True
        self.restart_auto_save_timer()

    def setup_ui(self):
        """
        UI 위젯을 생성하고 레이아웃을 설정합니다.
        이 메서드는 main_window_setup_ui.py와 main_window_setup_layout.py의 내용을 통합합니다.
        """
        # --- 메뉴바 ---
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)
        state_menu = self.menubar.addMenu("상태")
        self.export_state_action = QAction("상태 내보내기", self)
        self.import_state_action = QAction("상태 가져오기", self)
        state_menu.addAction(self.export_state_action)
        state_menu.addAction(self.import_state_action)
        help_menu = self.menubar.addMenu("도움말")
        open_readme_action = QAction("README 열기", self)
        open_readme_action.triggered.connect(self._open_readme)
        help_menu.addAction(open_readme_action)

        # --- 위젯 ---
        self.reset_program_btn = QPushButton("🗑️ 전체 프로그램 리셋")
        self.load_previous_work_btn = QPushButton("⏪ 마지막 작업 불러오기")
        self.save_current_work_btn = QPushButton("💾 현재 작업 저장")
        self.select_project_btn = QPushButton("📁 프로젝트 폴더 선택")
        self.project_folder_label = QLabel("현재 프로젝트 폴더: (선택 안 됨)")

        self.cached_model = CachedFileSystemModel()
        self.tree_view = QTreeView()
        # CheckableProxyModel 초기화는 컨트롤러에서 수행되거나 app.py에서 주입받아야 함
        # 여기서는 일단 생성만 해둠
        self.checkable_proxy = CheckableProxyModel(lambda: self.current_project_folder, None, self.tree_view)
        self.checkable_proxy.setSourceModel(self.cached_model)
        self.tree_view.setModel(self.checkable_proxy)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.attachment_group = QGroupBox("첨부 파일")
        attachment_layout = QVBoxLayout(self.attachment_group)
        self.attach_file_btn = QPushButton("📎 파일 첨부")
        self.paste_clipboard_btn = QPushButton("📋 클립보드 붙여넣기")
        self.remove_attachment_btn = QPushButton("➖ 선택 제거")
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.attach_file_btn)
        btn_layout.addWidget(self.paste_clipboard_btn)
        btn_layout.addWidget(self.remove_attachment_btn)
        self.attachment_list_widget = QListWidget()
        attachment_layout.addLayout(btn_layout)
        attachment_layout.addWidget(self.attachment_list_widget)

        self.build_tabs = QTabWidget()
        self.build_tabs.setTabBar(CustomTabBar(self.build_tabs, self))
        self.system_tab = CustomTextEdit()
        self.user_tab = CustomTextEdit()
        self.dir_structure_tab = CustomTextEdit()
        self.prompt_output_tab = CustomTextEdit()
        self.xml_input_tab = CustomTextEdit()
        self.summary_tab = CustomTextEdit()
        self.build_tabs.addTab(self.system_tab, "시스템")
        self.build_tabs.addTab(self.user_tab, "사용자")
        self.build_tabs.addTab(self.dir_structure_tab, "파일 트리")
        self.build_tabs.addTab(self.prompt_output_tab, "프롬프트 출력")
        self.build_tabs.addTab(self.xml_input_tab, "XML/DMP 입력")
        self.build_tabs.addTab(self.summary_tab, "Summary")

        self.generate_tree_btn = QPushButton("🌳 트리 생성")
        self.generate_btn = QPushButton("✨ 프롬프트 생성")
        self.send_to_gemini_btn = QPushButton("♊ Gemini로 전송")
        self.copy_btn = QPushButton("📋 클립보드에 복사")
        self.run_xml_parser_btn = QPushButton("▶️ DMP 파서 실행")
        self.generate_all_btn = QPushButton("⚡️ 한번에 실행")
        self.run_buttons = [self.generate_tree_btn, self.generate_btn, self.send_to_gemini_btn, self.copy_btn, self.run_xml_parser_btn, self.generate_all_btn]
        
        self.llm_combo = QComboBox(); self.llm_combo.addItems(["Gemini", "Claude", "GPT"])
        self.model_name_combo = QComboBox(); self.model_name_combo.setEditable(True)
        self.gemini_param_widget = QWidget()
        gemini_param_layout = QHBoxLayout(self.gemini_param_widget)
        self.gemini_temp_edit = QLineEdit()
        self.gemini_thinking_checkbox = QCheckBox()
        self.gemini_budget_edit = QLineEdit()
        self.gemini_search_checkbox = QCheckBox()
        self.gemini_dmp_checkbox = QCheckBox()
        gemini_param_layout.addWidget(QLabel("Temp:"))
        gemini_param_layout.addWidget(self.gemini_temp_edit)
        gemini_param_layout.addWidget(QLabel("Search:"))
        gemini_param_layout.addWidget(self.gemini_search_checkbox)
        gemini_param_layout.addWidget(QLabel("DMP:"))
        gemini_param_layout.addWidget(self.gemini_dmp_checkbox)
        gemini_param_layout.addWidget(QLabel("Thinking:"))
        gemini_param_layout.addWidget(self.gemini_thinking_checkbox)
        gemini_param_layout.addWidget(QLabel("Budget:"))
        gemini_param_layout.addWidget(self.gemini_budget_edit)
        
        # --- 레이아웃 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        top_buttons_layout = QHBoxLayout()
        top_buttons_layout.addWidget(self.reset_program_btn)
        top_buttons_layout.addWidget(self.load_previous_work_btn)
        top_buttons_layout.addWidget(self.save_current_work_btn)
        top_buttons_layout.addWidget(self.select_project_btn)
        top_buttons_layout.addStretch(1)
        main_layout.addLayout(top_buttons_layout)
        main_layout.addWidget(self.project_folder_label)
        llm_params_layout = QHBoxLayout()
        llm_params_layout.addWidget(QLabel("Model:"))
        llm_params_layout.addWidget(self.llm_combo)
        llm_params_layout.addWidget(self.model_name_combo)
        llm_params_layout.addWidget(self.gemini_param_widget)
        llm_params_layout.addStretch(1)
        main_layout.addLayout(llm_params_layout)
        
        self.center_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.addWidget(self.tree_view)
        left_splitter.addWidget(self.attachment_group)
        left_layout.addWidget(left_splitter)
        self.center_splitter.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_top_widget = QWidget()
        right_top_layout = QVBoxLayout(right_top_widget)
        run_buttons_layout = QHBoxLayout()
        for btn in self.run_buttons:
            run_buttons_layout.addWidget(btn)
        right_top_layout.addLayout(run_buttons_layout)
        right_top_layout.addWidget(self.build_tabs, 1)
        right_layout.addWidget(right_top_widget)
        self.center_splitter.addWidget(right_panel)
        
        main_layout.addWidget(self.center_splitter, 1)

        # --- 상태바 ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.char_count_label = QLabel("Chars: 0")
        self.token_count_label = QLabel("토큰 계산: -")
        self.api_time_label = QLabel("API 시간: -")
        self.status_bar.addPermanentWidget(self.api_time_label)
        self.status_bar.addPermanentWidget(self.token_count_label)
        self.status_bar.addPermanentWidget(self.char_count_label)

    def _open_readme(self):
        readme_path = str(Path(__file__).parent.parent.parent / "README.md")
        if os.path.exists(readme_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(readme_path))
        else:
            QMessageBox.warning(self, "오류", "README.md 파일을 찾을 수 없습니다.")

    def update_window_title(self, folder_name: Optional[str] = None):
        title = f"{folder_name} - {self.base_title}" if folder_name else self.base_title
        self.setWindowTitle(title)

    def _update_api_elapsed_time(self):
        if self.api_call_start_time and hasattr(self, 'api_time_label'):
            elapsed = datetime.datetime.now() - self.api_call_start_time
            self.api_time_label.setText(f"API 경과: {str(elapsed).split('.')[0]}")

    def save_state_to_default_handler(self):
        # This is a placeholder. The actual logic is now in FAHMainController.
        # This could emit a signal that the controller listens to.
        logger.debug("Auto-save triggered. In a full FAH app, this would be handled by the controller.")
        pass

    def restart_auto_save_timer(self):
        if self._initialized:
            self.auto_save_timer.start(30000)

    def closeEvent(self, event):
        logger.info("Closing MainWindow.")
        self.auto_save_timer.stop()
        self.api_timer.stop()
        # Additional cleanup can be handled by the controller's shutdown method.
        super().closeEvent(event)
