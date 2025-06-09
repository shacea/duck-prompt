import os
import io
import logging
import datetime
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import ( # PyQt5 -> PyQt6
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu,
    QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox,
    QFrame, QLineEdit, QDialog, QListWidget, QListWidgetItem, QStyle
)
from PyQt6.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont, QDesktopServices, QPixmap, QImage, QAction, QKeyEvent # PyQt5 -> PyQt6, QAction, QKeyEvent 추가
from PyQt6.QtCore import Qt, QSize, QStandardPaths, QModelIndex, QItemSelection, QUrl, QThread, pyqtSignal, QObject, QBuffer, QIODevice, QTimer, QEvent # PyQt5 -> PyQt6, QEvent 추가

# 서비스 및 모델 import
from core.pydantic_models.app_state import AppState
from core.services.db_service import DbService
from core.services.config_service import ConfigService
from core.services.state_service import StateService
from core.services.template_service import TemplateService
from core.services.prompt_service import PromptService
from core.services.xml_service import XmlService
from core.services.filesystem_service import FilesystemService
from core.services.token_service import TokenCalculationService
from core.services.gemini_service import build_gemini_graph
from core.services.directory_cache_service import DirectoryCacheService, CacheNode # Added
from core.langgraph_state import GeminiGraphState

# UI 관련 import
# from ui.models.file_system_models import FilteredFileSystemModel, CheckableProxyModel # Removed QFileSystemModel based
from ui.models.file_system_models import CachedFileSystemModel, CheckableProxyModel # Use new models
from ui.controllers.main_controller import MainController # MainController import 수정
from ui.controllers.resource_controller import ResourceController
from ui.controllers.prompt_controller import PromptController
from ui.controllers.xml_controller import XmlController
from ui.controllers.file_tree_controller import FileTreeController
from ui.controllers.system_prompt_controller import apply_default_system_prompt

from .main_window_setup_ui import create_menu_bar, create_widgets, create_layout, create_status_bar
from .main_window_setup_signals import connect_signals
from .settings_dialog import SettingsDialog
from ui.widgets.custom_text_edit import CustomTextEdit
from ui.widgets.custom_tab_bar import CustomTabBar
from utils.helpers import get_resource_path
from utils.notifications import show_notification # 알림 기능 임포트

# Pillow import 시도
try:
    from PIL import Image
    from PIL.ImageQt import ImageQt
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False

# 로거 설정
logger = logging.getLogger(__name__)

# --- Gemini API 호출을 위한 Worker 클래스 ---
class GeminiWorker(QObject):
    finished = pyqtSignal(str, str) # XML, Summary 결과 전달
    error = pyqtSignal(str)         # 오류 메시지 전달

    def __init__(self, graph_app, initial_state: GeminiGraphState): # 초기 상태 직접 받기
        super().__init__()
        self.graph_app = graph_app
        self.initial_state = initial_state # 전달받은 초기 상태 저장

    def run(self):
        """LangGraph 워크플로우를 실행합니다."""
        try:
            logger.info("Starting Gemini worker thread.")
            # LangGraph 실행 (.invoke 사용, 저장된 초기 상태 전달)
            final_state = self.graph_app.invoke(self.initial_state)
            logger.info(f"Gemini worker finished. Final state error: {final_state.get('error_message')}")

            if final_state.get("error_message"):
                self.error.emit(final_state["error_message"])
            else:
                xml_result = final_state.get("xml_output", "")
                summary_result = final_state.get("summary_output", "")
                self.finished.emit(xml_result, summary_result)
        except Exception as e:
            logger.exception("Error during LangGraph execution in worker thread.")
            self.error.emit(f"LangGraph 실행 오류: {str(e)}")


class MainWindow(QMainWindow):
    # 자동 저장 타이머 시그널 (상태 변경 시 타이머 재시작용)
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
        self.selected_files_data: List[tuple] = [] # Still used by PromptController? Maybe remove.
        self.tree_generated: bool = False # Still used by PromptController? Maybe remove.
        self._is_saving_gemini_settings = False # Still needed to prevent signal loops
        self.attached_items: List[Dict[str, Any]] = []
        self.api_call_start_time: Optional[datetime.datetime] = None # API 호출 시작 시간 저장
        self.api_timer = QTimer(self) # API 경과 시간 업데이트용 타이머 추가
        self.api_timer.timeout.connect(self._update_api_elapsed_time) # 타이머 시그널 연결

        # --- 자동 저장 타이머 ---
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(30000) # 30초 간격으로 변경
        self.auto_save_timer.setSingleShot(True) # 한 번만 실행 (상태 변경 시 재시작)

        # --- 서비스 인스턴스 생성 ---
        try:
            self.db_service = DbService() # Initialize DbService first
            self.config_service = ConfigService(self.db_service) # Inject DbService
        except ConnectionError as e:
             QMessageBox.critical(self, "Database Error", f"데이터베이스 연결 실패: {e}\n프로그램을 종료합니다.")
             # Exit the application gracefully
             # QApplication.instance().quit() # This might not work before app.exec()
             # Instead, prevent further initialization and let the app close
             raise SystemExit(f"Database connection failed: {e}") # Exit if DB fails
        except ValueError as e:
             QMessageBox.critical(self, "Configuration Error", f"설정 로드 실패: {e}\n프로그램을 종료합니다.")
             raise SystemExit(f"Configuration load failed: {e}") # Exit if config load fails

        self.state_service = StateService()
        self.template_service = TemplateService()
        self.prompt_service = PromptService()
        self.xml_service = XmlService()
        self.fs_service = FilesystemService(self.config_service) # Pass DB-backed config
        self.token_service = TokenCalculationService(self.config_service) # Pass DB-backed config
        self.cache_service = DirectoryCacheService(self.fs_service) # Added Cache Service
        self.gemini_graph = build_gemini_graph(self.config_service) # Pass DB-backed config
        self.gemini_thread: Optional[QThread] = None
        self.gemini_worker: Optional[GeminiWorker] = None

        # --- UI 구성 요소 생성 ---
        create_menu_bar(self)
        create_widgets(self) # This now creates CachedFileSystemModel and CheckableProxyModel
        create_layout(self)
        create_status_bar(self)

        # --- 컨트롤러 생성 및 연결 ---
        self.main_controller = MainController(self)
        self.resource_controller = ResourceController(self, self.template_service, self.state_service)
        self.prompt_controller = PromptController(self, self.prompt_service)
        self.xml_controller = XmlController(self, self.xml_service)
        # Pass cache_service to FileTreeController
        self.file_tree_controller = FileTreeController(self, self.fs_service, self.config_service, self.cache_service)

        # --- 시그널 연결 ---
        connect_signals(self)
        # 자동 저장 타이머 시그널 연결
        self.auto_save_timer.timeout.connect(self.resource_controller.save_state_to_default)
        self.state_changed_signal.connect(self.restart_auto_save_timer) # 상태 변경 시 타이머 재시작
        # Connect cache update signal to model population slot
        self.cache_service.cache_updated.connect(self.cached_model.update_model_from_cache_change)
        # Connect check state changes in proxy model to state changed signal
        self.checkable_proxy.check_state_changed.connect(self.state_changed_signal.emit)


        # --- 초기화 작업 ---
        self.resource_controller.load_templates_list()
        self._apply_initial_settings() # 기본 설정 적용 (DB 로드 등)

        self.status_bar.showMessage("Ready (DB Connected)")
        initial_width = 1200; initial_height = 800
        self.resize(initial_width, initial_height)
        left_width = int(initial_width * 0.35)
        right_width = initial_width - left_width
        self.center_splitter.setSizes([left_width, right_width])
        self.build_tabs.setCurrentIndex(1) # 사용자 탭을 기본으로
        self.file_tree_controller.reset_file_tree() # 파일 트리 초기화

        # --- 사용자 탭에 이벤트 필터 설치 ---
        if hasattr(self, 'user_tab'):
            self.user_tab.installEventFilter(self)
            logger.info("Event filter installed on user_tab.")
        # ---------------------------------

        self._initialized = True
        # 프로그램 시작 시 기본 상태 로드 제거 -> 사용자가 버튼 클릭 시 로드
        # self.resource_controller.load_state_from_default()
        self.restart_auto_save_timer() # 초기 로드 후 자동 저장 시작

    def _apply_initial_settings(self):
        """Applies initial settings loaded from ConfigService."""
        logger.info("Applying initial settings from ConfigService...")
        # 1. 기본 시스템 프롬프트 적용
        apply_default_system_prompt(self)

        # 2. LLM 및 모델 콤보박스 설정 (기본값 선택)
        self.llm_combo.setCurrentIndex(self.llm_combo.findText("Gemini")) # 기본 LLM 설정
        self.main_controller.on_llm_selected() # 모델 목록 로드 및 기본 모델 선택

        # 3. Gemini 파라미터 UI 업데이트
        self.load_gemini_settings_to_ui()

        # 4. 파일 필터링/gitignore 설정 로드 (Controller가 CacheService 업데이트)
        self.file_tree_controller.load_gitignore_settings()

        # 5. 리소스 관리 버튼 레이블 업데이트
        self.resource_controller.update_buttons_label()
        logger.info("Initial settings applied.")

    def _open_readme(self):
        """Opens the README.md file."""
        readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'README.md'))
        if os.path.exists(readme_path):
            url = QUrl.fromLocalFile(readme_path)
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(self, "오류", "README.md 파일을 여는 데 실패했습니다.")
        else:
            QMessageBox.warning(self, "오류", "README.md 파일을 찾을 수 없습니다.")

    def open_settings_dialog(self):
        """Opens the settings dialog."""
        dialog = SettingsDialog(self, self)
        # Dialog is now mostly read-only for config settings
        # It only saves .gitignore changes now
        dialog.exec() # exec_() -> exec()
        # SettingsDialog에서 설정을 저장하면 MainWindow의 UI도 업데이트해야 함
        # (SettingsDialog.save_config_settings 에서 MainWindow 업데이트 로직 호출)
        logger.info("Settings dialog closed.")


    # --- Public Methods ---

    def reset_state(self):
        """Resets internal state variables."""
        logger.info("Resetting application state...")
        was_initialized = self._initialized
        self._initialized = False
        self.auto_save_timer.stop() # 리셋 시 타이머 중지
        self.cache_service.stop_scan() # Stop scan on reset
        self.cache_service.stop_monitoring() # Stop monitoring on reset

        self.current_project_folder = None
        self.last_generated_prompt = ""
        self.selected_files_data = []
        self.tree_generated = False
        self.attached_items = []
        self.api_call_start_time = None # API 시작 시간 초기화
        self.api_timer.stop() # API 타이머 중지

        # 체크 상태 딕셔너리 초기화
        if hasattr(self, 'checkable_proxy'):
            logger.debug("Clearing checked_files_dict in reset_state.")
            self.checkable_proxy.checked_files_dict.clear()

        if hasattr(self, 'attachment_list_widget'): self.attachment_list_widget.clear()
        self.update_window_title()

        # 파일 트리 리셋 (모델 클리어)
        if hasattr(self, 'file_tree_controller'):
            self.file_tree_controller.reset_file_tree()

        # LLM 및 토큰 상태 리셋
        if hasattr(self, 'main_controller'):
            self.main_controller.on_llm_selected() # 기본 LLM/모델 설정
            self.main_controller._stop_token_calculation_thread() # 토큰 계산 스레드 중지
            self.main_controller.reset_token_label() # 토큰 라벨 리셋

        # 탭 내용 클리어
        if hasattr(self, 'system_tab'): self.system_tab.clear()
        if hasattr(self, 'user_tab'): self.user_tab.clear()
        if hasattr(self, 'dir_structure_tab'): self.dir_structure_tab.clear()
        if hasattr(self, 'xml_input_tab'): self.xml_input_tab.clear()
        if hasattr(self, 'prompt_output_tab'): self.prompt_output_tab.clear()
        if hasattr(self, 'summary_tab'): self.summary_tab.clear()
        # Meta 모드 탭 클리어 (존재 시)
        if hasattr(self, 'meta_prompt_tab'): self.meta_prompt_tab.clear()
        if hasattr(self, 'user_prompt_tab'):
            user_prompt_tab_widget = getattr(self, 'user_prompt_tab', None)
            if user_prompt_tab_widget: user_prompt_tab_widget.clear()
        if hasattr(self, 'final_prompt_tab'):
            final_prompt_tab_widget = getattr(self, 'final_prompt_tab', None)
            if final_prompt_tab_widget: final_prompt_tab_widget.clear()

        # 기타 UI 초기화
        if hasattr(self, 'project_folder_label'): self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
        if hasattr(self, 'api_time_label'): self.api_time_label.setText("API 시간: -") # API 시간 라벨 초기화

        # 기본 설정 다시 적용 (시스템 프롬프트 등)
        self._apply_initial_settings()

        self._initialized = was_initialized # 원래 초기화 상태 복원
        self.restart_auto_save_timer() # 리셋 후 자동 저장 재시작
        logger.info("Application state reset complete.")


    def update_window_title(self, folder_name: Optional[str] = None):
        """Updates the window title."""
        title = f"{folder_name} - {self.base_title}" if folder_name else self.base_title
        self.setWindowTitle(title)

    def get_current_state(self) -> AppState:
        """Gathers the current UI state for saving (full or partial)."""
        checked_paths = self.checkable_proxy.get_all_checked_paths() if hasattr(self, 'checkable_proxy') else []
        selected_llm = self.llm_combo.currentText() if hasattr(self, 'llm_combo') else "Gemini"
        selected_model_name = self.model_name_combo.currentText().strip() if hasattr(self, 'model_name_combo') else ""

        # 첨부 파일 메타데이터만 직렬화
        serializable_attachments = []
        for item in self.attached_items:
            s_item = item.copy()
            s_item.pop('data', None) # 데이터 제외
            serializable_attachments.append(s_item)

        # AppState 모델 생성 (모든 필드 포함)
        state_data = {
            "project_folder": self.current_project_folder,
            "system_prompt": self.system_tab.toPlainText(),
            "user_prompt": self.user_tab.toPlainText(),
            "checked_files": checked_paths, # checked_files_dict의 키 리스트 저장
            "selected_llm": selected_llm,
            "selected_model_name": selected_model_name,
            "attached_items": serializable_attachments,
        }
        try:
            app_state = AppState(**state_data)
            return app_state
        except Exception as e:
             logger.error(f"Error creating AppState model: {e}")
             # 오류 발생 시 최소한의 정보로 기본 상태 반환
             return AppState(
                 project_folder=self.current_project_folder,
                 user_prompt=self.user_tab.toPlainText(),
                 checked_files=checked_paths,
                 attached_items=serializable_attachments,
                 selected_llm=selected_llm,
                 selected_model_name=selected_model_name
             )

    def set_current_state(self, state: AppState, partial_load: bool = False):
        """
        Sets the UI state based on the provided AppState model.
        If partial_load is True, only loads project folder, checked files, user prompt, and attachments.
        Triggers background scan if project folder changes.
        """
        logger.info(f"Setting current state. Partial load: {partial_load}")
        # UI 업데이트 중 시그널/타이머 방지
        was_initialized = self._initialized
        self._initialized = False
        self.auto_save_timer.stop()

        folder_changed = False
        new_folder = state.project_folder
        old_folder = self.current_project_folder

        # Determine if folder needs update and trigger scan if necessary
        if new_folder and os.path.isdir(new_folder):
            if old_folder != new_folder:
                logger.info(f"Project folder changed: {old_folder} -> {new_folder}")
                folder_changed = True
                self.current_project_folder = new_folder
                folder_name = os.path.basename(new_folder)
                self.project_folder_label.setText(f"현재 프로젝트 폴더: {new_folder}")
                self.update_window_title(folder_name)
                # Clear check state dict immediately on folder change
                if hasattr(self, 'checkable_proxy'):
                    self.checkable_proxy.checked_files_dict.clear()
                    logger.debug("Cleared checked_files_dict due to project folder change.")
                # Load gitignore and start scan
                ignore_patterns = self.file_tree_controller.load_gitignore_settings()
                self.cache_service.start_scan(new_folder, ignore_patterns)
            else:
                # Folder is the same, no need to rescan unless forced
                folder_name = os.path.basename(new_folder)
        elif not new_folder and old_folder:
            # Folder removed in state
            folder_changed = True
            self.current_project_folder = None
            self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
            self.update_window_title()
            self.file_tree_controller.reset_file_tree() # Clear model
            self.cache_service.stop_scan()
            self.cache_service.stop_monitoring()
            if hasattr(self, 'checkable_proxy'): self.checkable_proxy.checked_files_dict.clear()
        # else: new_folder is None and old_folder is None - no change

        # --- Load common fields (partial and full) ---
        self.user_tab.setText(state.user_prompt)
        self.attached_items = state.attached_items or []
        self._update_attachment_list_ui()

        # --- Full Load Specific Fields ---
        if not partial_load:
            self.system_tab.setText(state.system_prompt)

            llm_index = self.llm_combo.findText(state.selected_llm)
            if llm_index != -1:
                self.llm_combo.setCurrentIndex(llm_index)
                # on_llm_selected updates model list and selects default/saved
                self.main_controller.on_llm_selected() # Call this first
                # Now try to select the specific model from the state
                model_index = self.model_name_combo.findText(state.selected_model_name)
                if model_index != -1:
                    self.model_name_combo.setCurrentIndex(model_index)
                else:
                    logger.warning(f"Saved model '{state.selected_model_name}' not found for {state.selected_llm} after loading state.")
            else:
                # Saved LLM not found, default to Gemini
                self.llm_combo.setCurrentIndex(self.llm_combo.findText("Gemini"))
                self.main_controller.on_llm_selected()

            # Load Gemini settings if needed (already done by on_llm_selected if Gemini)
            # self.load_gemini_settings_to_ui()
            self.resource_controller.update_buttons_label()

        # --- Restore Check States (Common for partial and full, AFTER scan potentially finishes) ---
        # Check states should be restored *after* the model is populated by the scan.
        # We store the desired check states and apply them once the scan finishes.
        self._pending_check_states = set(state.checked_files or [])
        if folder_changed:
            # Connect to scan_finished signal to apply checks
            logger.info(f"Scan triggered for folder change. Will apply {len(self._pending_check_states)} check states upon completion.")
            # Ensure only one connection
            try: self.cache_service.scan_finished.disconnect(self._apply_pending_check_states)
            except TypeError: pass # Ignore if not connected
            self.cache_service.scan_finished.connect(self._apply_pending_check_states)
        elif self.current_project_folder:
            # If folder didn't change, apply checks immediately (assuming model is already populated)
            logger.info("Folder unchanged. Applying check states immediately.")
            self._apply_pending_check_states()
        else:
            # No folder, clear pending checks
            self._pending_check_states = set()


        # --- Final UI Updates ---
        status_msg = "마지막 작업 상태 로드 완료." if partial_load else "상태 로드 완료."
        self.status_bar.showMessage(status_msg)
        self._initialized = was_initialized
        self.main_controller.update_char_count_for_active_tab()
        self.token_count_label.setText("토큰 계산: -")
        if hasattr(self, 'api_time_label'): self.api_time_label.setText("API 시간: -")
        self.restart_auto_save_timer()

    def _apply_pending_check_states(self):
        """Applies check states stored in self._pending_check_states to the current model."""
        logger.info(f"Applying {len(self._pending_check_states)} pending check states...")
        if not hasattr(self, 'checkable_proxy') or not hasattr(self, 'cached_model'):
            logger.warning("Cannot apply check states: Models not available.")
            self._pending_check_states = set()
            return

        # Disconnect the signal after applying
        try: self.cache_service.scan_finished.disconnect(self._apply_pending_check_states)
        except TypeError: pass

        # Clear current checks before applying pending ones
        self.checkable_proxy.checked_files_dict.clear()
        items_to_check_indices = []

        for path in self._pending_check_states:
            item = self.cached_model.find_item_by_path(path)
            if item:
                source_index = self.cached_model.indexFromItem(item)
                proxy_index = self.checkable_proxy.mapFromSource(source_index)
                if proxy_index.isValid():
                    items_to_check_indices.append(proxy_index)
                else:
                    logger.warning(f"Could not map source index to proxy for pending check: {path}")
            else:
                logger.warning(f"Item not found in model for pending check state: {path}")

        # Apply checks using setData (will handle dictionary update and recursion)
        logger.info(f"Applying check state for {len(items_to_check_indices)} restored items using setData.")
        # Set data in batches or individually? Individual seems safer with recursion flag.
        for proxy_index in items_to_check_indices:
            self.checkable_proxy.setData(proxy_index, Qt.CheckState.Checked, Qt.ItemDataRole.CheckStateRole)
            # logger.debug(f"  Called setData(Checked) for pending state: {self.checkable_proxy.get_file_path_from_index(proxy_index)}")

        self._pending_check_states = set() # Clear pending states
        logger.info("Finished applying pending check states.")
        # Emit state changed signal after applying checks
        self.state_changed_signal.emit()


    def uncheck_all_files(self):
        """Unchecks all items in the file tree view by clearing the dictionary."""
        if not hasattr(self, 'checkable_proxy'): return
        if not self.checkable_proxy.checked_files_dict: return # Nothing to uncheck

        logger.info("Unchecking all files.")
        # Clear the dictionary
        self.checkable_proxy.checked_files_dict.clear()
        # Signal the proxy model to update the UI based on the cleared dictionary
        self.checkable_proxy.update_check_states_from_dict()
        # Emit state changed signal
        self.state_changed_signal.emit()

    def create_tree_item(self, text, parent=None) -> QTreeWidgetItem:
        """Helper method to create items in the template/state tree."""
        item = QTreeWidgetItem([text])
        if parent is None: self.template_tree.addTopLevelItem(item)
        else: parent.addChild(item)
        return item

    def add_new_custom_tab(self):
        """Adds a new custom tab."""
        new_tab_name, ok = QInputDialog.getText(self, "새 탭 추가", "새 탭의 이름을 입력하세요:")
        if ok and new_tab_name and new_tab_name.strip():
            new_name = new_tab_name.strip()
            from ui.widgets.tab_manager import is_tab_deletable
            if not is_tab_deletable(new_name):
                 QMessageBox.warning(self, "경고", f"'{new_name}'은(는) 사용할 수 없는 탭 이름입니다.")
                 return
            for i in range(self.build_tabs.count()):
                if self.build_tabs.tabText(i) == new_name:
                    QMessageBox.warning(self, "경고", f"'{new_name}' 탭이 이미 존재합니다.")
                    return
            new_tab = CustomTextEdit(); new_tab.setPlaceholderText(f"{new_name} 내용 입력...")
            plus_tab_index = -1
            for i in range(self.build_tabs.count()):
                if self.build_tabs.tabText(i) == "+": plus_tab_index = i; break
            if plus_tab_index != -1:
                 self.build_tabs.insertTab(plus_tab_index, new_tab, new_name)
                 self.build_tabs.setCurrentIndex(plus_tab_index)
            else:
                 self.build_tabs.addTab(new_tab, new_name)
                 self.build_tabs.setCurrentIndex(self.build_tabs.count() - 1)
            # 새 탭의 textChanged 시그널 연결
            new_tab.textChanged.connect(self.main_controller.handle_text_changed)
            self.state_changed_signal.emit() # 상태 변경 시그널 발생
        elif ok: QMessageBox.warning(self, "경고", "탭 이름은 비워둘 수 없습니다.")

    # --- Attachment UI Update ---
    def _update_attachment_list_ui(self):
        """Updates the attachment list widget based on self.attached_items."""
        if not hasattr(self, 'attachment_list_widget'): return
        self.attachment_list_widget.clear()
        for item in self.attached_items:
            item_name = item.get('name', 'Unknown')
            item_type = item.get('type', 'unknown')
            display_text = f"[{item_type.upper()}] {item_name}"
            list_item = QListWidgetItem(display_text)
            icon = QIcon()
            if item_type == 'image':
                img_data = item.get('data')
                if not img_data and item.get('path') and os.path.exists(item['path']):
                    try:
                        with open(item['path'], 'rb') as f: img_data = f.read()
                    except Exception: pass

                if img_data:
                    try:
                        pixmap = QPixmap()
                        pixmap.loadFromData(img_data)
                        if not pixmap.isNull():
                            icon = QIcon(pixmap.scaled(QSize(32, 32), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)) # Qt.KeepAspectRatio -> Qt.AspectRatioMode.KeepAspectRatio, Qt.SmoothTransformation -> Qt.TransformationMode.SmoothTransformation
                        else:
                           icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon) # QStyle.SP_FileIcon -> QStyle.StandardPixmap.SP_FileIcon
                    except Exception as e:
                        logger.error(f"Error creating thumbnail for {item_name}: {e}")
                        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon) # QStyle.SP_FileIcon -> QStyle.StandardPixmap.SP_FileIcon
                else:
                    icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon) # QStyle.SP_FileIcon -> QStyle.StandardPixmap.SP_FileIcon

            elif item_type == 'file':
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon) # QStyle.SP_FileIcon -> QStyle.StandardPixmap.SP_FileIcon
            else:
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon) # QStyle.SP_FileIcon -> QStyle.StandardPixmap.SP_FileIcon
            list_item.setIcon(icon)
            self.attachment_list_widget.addItem(list_item)
        # 첨부 목록 변경 시 상태 변경 시그널 발생 (자동 저장용)
        # self.state_changed_signal.emit() # 여기서 호출하면 너무 빈번할 수 있음. attach/paste/remove 함수에서 호출.

    # --- LangGraph 관련 메서드 ---
    def send_prompt_to_gemini(self):
        """ Sends the prompt and attachments to Gemini via LangGraph worker thread. """
        if not hasattr(self, 'prompt_output_tab'):
            QMessageBox.warning(self, "오류", "프롬프트 출력 탭을 찾을 수 없습니다.")
            return

        prompt_text = self.prompt_output_tab.toPlainText()
        loaded_attachments = []
        for item in self.attached_items:
            if not item.get('data') and item.get('path') and os.path.exists(item['path']):
                try:
                    with open(item['path'], 'rb') as f:
                        item['data'] = f.read()
                    logger.info(f"Loaded data for attachment: {item['name']}")
                except Exception as e:
                    QMessageBox.warning(self, "첨부 파일 오류", f"첨부 파일 '{item['name']}' 로드 실패: {e}")
            loaded_attachments.append(item)


        if not prompt_text.strip() and not loaded_attachments:
            QMessageBox.warning(self, "경고", "Gemini에 전송할 프롬프트 내용이나 첨부 파일이 없습니다.")
            return

        if hasattr(self, 'send_to_gemini_btn'): self.send_to_gemini_btn.setEnabled(False)
        self.status_bar.showMessage("Gemini API 호출 중...")
        # API 호출 시작 시간 기록 및 표시
        self.api_call_start_time = datetime.datetime.now()
        start_time_str = self.api_call_start_time.strftime('%H:%M:%S')
        if hasattr(self, 'api_time_label'):
            self.api_time_label.setText(f"API 시작: {start_time_str}, 경과: 0:00:00") # 초기 경과 시간 표시
        self.api_timer.start(1000) # 1초마다 업데이트 타이머 시작
        QApplication.processEvents()

        if self.gemini_thread and self.gemini_thread.isRunning():
            logger.warning("Terminating previous Gemini thread...")
            self.gemini_thread.quit(); self.gemini_thread.wait()

        selected_model_name = self.model_name_combo.currentText().strip()
        initial_state: GeminiGraphState = {
            "input_prompt": prompt_text,
            "input_attachments": loaded_attachments,
            "selected_model_name": selected_model_name,
            "gemini_response": "",
            "xml_output": "",
            "summary_output": "",
            "error_message": None,
            "log_id": None # log_id 추가
        }

        self.gemini_thread = QThread()
        self.gemini_worker = GeminiWorker(self.gemini_graph, initial_state)
        self.gemini_worker.moveToThread(self.gemini_thread)

        self.gemini_thread.started.connect(self.gemini_worker.run)
        self.gemini_worker.finished.connect(self.handle_gemini_response)
        self.gemini_worker.error.connect(self.handle_gemini_error)
        self.gemini_worker.finished.connect(self.gemini_thread.quit)
        self.gemini_worker.finished.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)
        self.gemini_worker.error.connect(self.gemini_thread.quit)
        self.gemini_worker.error.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.cleanup_gemini_thread)

        self.gemini_thread.start()

    def _update_api_elapsed_time(self):
        """ Updates the API elapsed time label. """
        if self.api_call_start_time and hasattr(self, 'api_time_label'):
            elapsed_time = datetime.datetime.now() - self.api_call_start_time
            elapsed_str = str(elapsed_time).split('.')[0] # HH:MM:SS 형식
            start_time_str = self.api_call_start_time.strftime('%H:%M:%S')
            self.api_time_label.setText(f"API 시작: {start_time_str}, 경과: {elapsed_str}")
        else:
            # Stop timer if start time is somehow lost
            self.api_timer.stop()

    def handle_gemini_response(self, xml_result: str, summary_result: str):
        """ Handles Gemini response. """
        logger.info("--- Handling Gemini Response ---")
        self.api_timer.stop() # 타이머 중지
        if hasattr(self, 'xml_input_tab'):
            self.xml_input_tab.setPlainText(xml_result)
            logger.info(f"XML Output Length: {len(xml_result)}")
        if hasattr(self, 'summary_tab'):
            self.summary_tab.setPlainText(summary_result)
            logger.info(f"Summary Output Length: {len(summary_result)}")
            self.build_tabs.setCurrentWidget(self.summary_tab)

        # API 경과 시간 계산 및 표시 (최종)
        if self.api_call_start_time and hasattr(self, 'api_time_label'):
            end_time = datetime.datetime.now()
            elapsed_time = end_time - self.api_call_start_time
            elapsed_str = str(elapsed_time).split('.')[0] # HH:MM:SS 형식
            start_time_str = self.api_call_start_time.strftime('%H:%M:%S')
            self.api_time_label.setText(f"API 시작: {start_time_str}, 경과: {elapsed_str} (완료)")

        self.status_bar.showMessage("Gemini 응답 처리 완료.")
        if hasattr(self, 'send_to_gemini_btn'): self.send_to_gemini_btn.setEnabled(True)

        # --- 작업 완료 알림 ---
        show_notification("Gemini 응답 완료", "Gemini API 응답 처리가 완료되었습니다.")

    def handle_gemini_error(self, error_msg: str):
        """ Handles Gemini error, showing user-friendly message for specific API response issues. """
        logger.error(f"--- Handling Gemini Error: {error_msg} ---")
        self.api_timer.stop() # 타이머 중지

        # API 경과 시간 계산 및 표시 (오류 시에도)
        if self.api_call_start_time and hasattr(self, 'api_time_label'):
            end_time = datetime.datetime.now()
            elapsed_time = end_time - self.api_call_start_time
            elapsed_str = str(elapsed_time).split('.')[0] # HH:MM:SS 형식
            start_time_str = self.api_call_start_time.strftime('%H:%M:%S')
            self.api_time_label.setText(f"API 시작: {start_time_str}, 경과: {elapsed_str} (오류)")

        user_display_error = error_msg
        if "Gemini API 응답 처리 오류" in error_msg or "Gemini API 응답 문제 발생" in error_msg:
             user_display_error = "Gemini API 응답 문제입니다. 자세한 내용은 Summary 탭을 확인하세요."
             if hasattr(self, 'summary_tab'):
                 self.summary_tab.setPlainText(f"Gemini 오류 상세:\n{error_msg}")

        QMessageBox.critical(self, "Gemini API 오류", user_display_error)
        self.status_bar.showMessage("Gemini API 호출 오류.")
        if hasattr(self, 'send_to_gemini_btn'): self.send_to_gemini_btn.setEnabled(True)

        # --- 작업 오류 알림 ---
        # 오류 메시지가 너무 길 수 있으므로 일부만 표시
        notification_msg = f"Gemini API 호출 중 오류 발생: {error_msg[:100]}"
        if len(error_msg) > 100: notification_msg += "..."
        show_notification("Gemini 오류", notification_msg)


    def cleanup_gemini_thread(self):
        """ Cleans up Gemini thread and worker objects. """
        logger.info("--- Cleaning up Gemini thread and worker ---")
        self.api_timer.stop() # 스레드 정리 시 타이머 중지
        self.gemini_thread = None
        self.gemini_worker = None
        if hasattr(self, 'send_to_gemini_btn'): self.send_to_gemini_btn.setEnabled(True)


    # --- Gemini 파라미터 관리 메서드 ---
    def load_gemini_settings_to_ui(self):
        """Loads Gemini parameters from DB (via config_service) to UI."""
        # _initialized 체크 제거: 초기화 중에도 호출될 수 있음
        # if not self._initialized: return
        try:
            settings = self.config_service.get_settings()
            if not settings:
                logger.warning("Cannot load Gemini settings to UI: Config settings not available.")
                return

            logger.info("Loading Gemini settings to UI...")
            # 시그널 차단
            self.gemini_temp_edit.blockSignals(True); self.gemini_thinking_checkbox.blockSignals(True)
            self.gemini_budget_edit.blockSignals(True); self.gemini_search_checkbox.blockSignals(True)

            # UI 업데이트
            self.gemini_temp_edit.setText(str(settings.gemini_temperature))
            self.gemini_thinking_checkbox.setChecked(settings.gemini_enable_thinking)
            self.gemini_budget_edit.setText(str(settings.gemini_thinking_budget))
            self.gemini_search_checkbox.setChecked(settings.gemini_enable_search)
            logger.info(f"  Temp: {settings.gemini_temperature}, Thinking: {settings.gemini_enable_thinking}, Budget: {settings.gemini_thinking_budget}, Search: {settings.gemini_enable_search}")

            # 시그널 복구
            self.gemini_temp_edit.blockSignals(False); self.gemini_thinking_checkbox.blockSignals(False)
            self.gemini_budget_edit.blockSignals(False); self.gemini_search_checkbox.blockSignals(False)

            # 위젯 가시성 설정
            is_gemini_selected = (self.llm_combo.currentText() == "Gemini")
            if hasattr(self, 'gemini_param_widget'): self.gemini_param_widget.setVisible(is_gemini_selected)
            logger.info("Gemini settings loaded to UI successfully.")

        except Exception as e:
            logger.error(f"Error loading Gemini settings to UI: {e}", exc_info=True)
            QMessageBox.warning(self, "오류", f"Gemini 설정을 UI에 로드하는 중 오류 발생: {e}")


    def save_gemini_settings(self):
        """Saves Gemini parameters from UI to DB (Not Implemented)."""
        # This function is now disabled because saving config back to DB is not implemented.
        # We keep the method to avoid breaking signal connections, but it does nothing.
        if not self._initialized or self._is_saving_gemini_settings: return
        # logger.warning("Saving Gemini parameters to database is currently disabled.")

        # --- Keep the logic to prevent signal loops ---
        self._is_saving_gemini_settings = True
        # Read UI values (optional, could be removed if truly disabled)
        try:
            temp_str = self.gemini_temp_edit.text().strip(); temperature = float(temp_str) if temp_str else 0.0
            enable_thinking = self.gemini_thinking_checkbox.isChecked()
            budget_str = self.gemini_budget_edit.text().strip(); thinking_budget = int(budget_str) if budget_str else 0
            enable_search = self.gemini_search_checkbox.isChecked()
            # print(f"Gemini UI Params: T={temperature}, Think={enable_thinking}, Bud={thinking_budget}, Srch={enable_search}")
        except ValueError:
            pass # Ignore errors if UI has invalid temp values temporarily
        finally:
            self._is_saving_gemini_settings = False
        # --- End of signal loop prevention ---

        # --- Actual saving logic is removed ---
        # try:
        #     # ... (read UI values) ...
        #     update_data = { ... }
        #     # self.config_service.update_settings(**update_data) # This line is removed/commented
        #     print(f"Gemini settings UI changed, but saving to DB is disabled.")
        # except Exception as e:
        #     print(f"Error preparing Gemini settings (saving disabled): {e}")
        # finally: self._is_saving_gemini_settings = False


    # --- Event Handlers ---
    def on_copy_shortcut(self):
        """Handles Ctrl+C shortcut."""
        current_widget = self.build_tabs.currentWidget()
        if isinstance(current_widget, CustomTextEdit):
            if current_widget.textCursor().hasSelection(): current_widget.copy()
            elif current_widget == self.prompt_output_tab or \
                 (hasattr(self, 'final_prompt_tab') and current_widget == self.final_prompt_tab):
                self.prompt_controller.copy_to_clipboard()

    def on_tree_view_context_menu(self, position):
        """Handles context menu requests on the file tree view."""
        index = self.tree_view.indexAt(position)
        if not index.isValid(): return
        # Get path from proxy model using the new method
        file_path = self.checkable_proxy.get_file_path_from_index(index)
        if not file_path: return
        menu = QMenu()
        rename_action = QAction("이름 변경", self) # PyQt6: QAction(text, parent)
        delete_action = QAction("삭제", self) # PyQt6: QAction(text, parent)
        refresh_action = QAction("새로고침", self) # Add refresh action
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(refresh_action)
        action = menu.exec(self.tree_view.viewport().mapToGlobal(position)) # exec_() -> exec()
        if action == rename_action: self.file_tree_controller.rename_item(file_path)
        elif action == delete_action: self.file_tree_controller.delete_item(file_path)
        elif action == refresh_action: self.file_tree_controller.refresh_tree() # Call refresh

    def on_tree_view_item_clicked(self, index: QModelIndex):
        """
        Handles item clicks in the tree view to toggle check state for selected items.
        Applies the toggled state of the clicked item to all currently selected items.
        Uses the CheckableProxyModel's setData.
        """
        if not index.isValid() or index.column() != 0:
            return

        # Get the target state based on the *clicked* item's current state
        current_state_value = self.checkable_proxy.data(index, Qt.ItemDataRole.CheckStateRole)
        if isinstance(current_state_value, Qt.CheckState):
            current_check_state = current_state_value
        elif isinstance(current_state_value, int):
            current_check_state = Qt.CheckState(current_state_value)
        else:
            logger.warning(f"on_tree_view_item_clicked: Unexpected data type for CheckStateRole: {type(current_state_value)}")
            return

        # Determine the state to apply to all selected items (toggle of the clicked item)
        target_check_state = Qt.CheckState.Unchecked if current_check_state == Qt.CheckState.Checked else Qt.CheckState.Checked

        # Get all currently selected proxy indices
        selection_model = self.tree_view.selectionModel()
        selected_proxy_indices = selection_model.selectedIndexes()

        # Filter for unique column 0 indices
        unique_col0_indices = {idx for idx in selected_proxy_indices if idx.column() == 0}

        logger.debug(f"Clicked item: {self.checkable_proxy.get_file_path_from_index(index)}, Target state: {target_check_state}, Selected count: {len(unique_col0_indices)}")

        # Apply the target state to all unique selected items using setData
        # setData will handle the dictionary update and recursive logic
        for proxy_idx in unique_col0_indices:
            if proxy_idx.isValid():
                # logger.debug(f"  Calling setData for selected index: {self.checkable_proxy.get_file_path_from_index(proxy_idx)} with state {target_check_state}")
                # Let setData handle the logic, including checking if state actually needs changing
                self.checkable_proxy.setData(proxy_idx, target_check_state, Qt.ItemDataRole.CheckStateRole)

        # No need to emit state_changed_signal here, it's connected to checkable_proxy.check_state_changed


    def restart_auto_save_timer(self):
        """Restarts the auto-save timer."""
        if self._initialized:
            # logger.debug("Restarting auto-save timer.")
            self.auto_save_timer.start(30000) # 30초 후 저장으로 변경

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """
        Filters events for specific widgets, handling Ctrl+Enter in the user tab.
        Modified to run "Generate All" then "Send to Gemini".
        Checks if prompt was generated before sending.
        """
        # 사용자 탭(user_tab)에서 발생하는 키 입력 이벤트인지 확인
        if source == self.user_tab and event.type() == QEvent.Type.KeyPress:
            # QKeyEvent 타입으로 캐스팅 (PyQt6에서는 필요 없을 수 있으나 명시적)
            key_event = event
            if isinstance(key_event, QKeyEvent):
                # Ctrl 키와 Enter 키가 함께 눌렸는지 확인
                is_control_pressed = bool(key_event.modifiers() & Qt.KeyboardModifier.ControlModifier) # Qt.ControlModifier -> Qt.KeyboardModifier.ControlModifier
                is_enter_key = key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)

                if is_control_pressed and is_enter_key:
                    logger.info("Ctrl+Enter detected in user_tab. Triggering 'Generate All' then 'Send to Gemini'.")

                    logger.info("Running 'Generate All'...")
                    # generate_all_and_copy는 프롬프트 생성 성공 시 True 반환
                    success_generate_all = self.prompt_controller.generate_all_and_copy()

                    # 프롬프트가 실제로 생성되었는지 확인 (last_generated_prompt 사용)
                    prompt_generated = bool(self.last_generated_prompt and self.last_generated_prompt.strip())

                    if prompt_generated:
                        logger.info("Prompt generated. Proceeding to 'Send to Gemini'.")
                        if not success_generate_all:
                            # 프롬프트는 생성되었지만, 트리 생성 또는 복사 실패 시 정보 메시지
                            logger.warning("'Generate All' returned False, but prompt was generated. Sending to Gemini anyway.")
                            # 사용자에게 알릴 필요는 없을 수 있음 (상태바 메시지로 대체 가능)
                            # QMessageBox.information(self, "정보", "일부 작업(트리 생성 또는 복사)에 실패했지만 Gemini 전송을 시도합니다.")
                            self.status_bar.showMessage("일부 작업 실패, Gemini 전송 시도...")
                        # Gemini 전송 실행
                        self.send_prompt_to_gemini()
                    else:
                        # 프롬프트 생성 자체가 실패한 경우
                        logger.error("'Generate All' failed to generate a prompt. Skipping 'Send to Gemini'.")
                        QMessageBox.warning(self, "실패", "'한번에 실행' 작업 중 프롬프트 생성에 실패하여 Gemini로 전송하지 못했습니다.")

                    return True # 이벤트 처리 완료 (기본 동작 방지)

        # 다른 위젯이나 이벤트는 기본 처리
        return super().eventFilter(source, event)


    def closeEvent(self, event):
        """Ensure database connection is closed and threads are stopped when the window closes."""
        logger.info("Closing MainWindow. Stopping threads and disconnecting database.")
        self.auto_save_timer.stop() # 윈도우 닫을 때 자동 저장 타이머 중지
        self.api_timer.stop() # 윈도우 닫을 때 API 타이머 중지
        self.cache_service.stop_monitoring() # Stop monitoring
        self.cache_service.stop_scan() # Stop scan
        # 진행 중인 스레드 중지 시도
        if hasattr(self, 'main_controller'):
            self.main_controller._stop_token_calculation_thread()
        if self.gemini_thread and self.gemini_thread.isRunning():
            logger.warning("Terminating Gemini thread on close...")
            self.gemini_thread.quit()
            self.gemini_thread.wait(1000) # Wait up to 1 second
            if self.gemini_thread and self.gemini_thread.isRunning():
                self.gemini_thread.terminate()
                self.gemini_thread.wait()
            self.cleanup_gemini_thread()

        # 마지막 상태 저장 시도 (선택적)
        try:
            logger.info("Attempting to save final state before closing...")
            self.resource_controller.save_state_to_default()
        except Exception as e:
            logger.error(f"Error saving final state: {e}")

        if hasattr(self, 'db_service'):
            self.db_service.disconnect()
        super().closeEvent(event)
