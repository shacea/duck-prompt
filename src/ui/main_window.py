
import os
import io
import logging
import datetime
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu,
    QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox,
    QFrame, QLineEdit, QDialog, QListWidget, QListWidgetItem, QStyle
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont, QDesktopServices, QPixmap, QImage
from PyQt5.QtCore import Qt, QSize, QStandardPaths, QModelIndex, QItemSelection, QUrl, QThread, pyqtSignal, QObject, QBuffer, QIODevice, QTimer

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
from core.langgraph_state import GeminiGraphState

# UI 관련 import
from ui.models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
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

    def __init__(self, mode="Code Enhancer Prompt Builder"):
        super().__init__()
        self._initialized = False
        self.mode = mode
        self.base_title = "DuckPrompt"
        self.update_window_title()

        QApplication.setStyle(QStyleFactory.create("Fusion"))

        # --- 상태 변수 ---
        self.current_project_folder: Optional[str] = None
        self.last_generated_prompt: str = ""
        self.selected_files_data: List[tuple] = []
        self.tree_generated: bool = False
        self._is_saving_gemini_settings = False # Still needed to prevent signal loops
        self.attached_items: List[Dict[str, Any]] = []
        self.api_call_start_time: Optional[datetime.datetime] = None # API 호출 시작 시간 저장
        self.api_timer = QTimer(self) # API 경과 시간 업데이트용 타이머 추가
        self.api_timer.timeout.connect(self._update_api_elapsed_time) # 타이머 시그널 연결

        # --- 자동 저장 타이머 ---
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(10000) # 10초 간격
        self.auto_save_timer.setSingleShot(True) # 한 번만 실행 (상태 변경 시 재시작)

        # --- 서비스 인스턴스 생성 ---
        try:
            self.db_service = DbService() # Initialize DbService first
            self.config_service = ConfigService(self.db_service) # Inject DbService
        except ConnectionError as e:
             QMessageBox.critical(self, "Database Error", f"데이터베이스 연결 실패: {e}\n프로그램을 종료합니다.")
             # Exit the application gracefully
             # QApplication.instance().quit() # This might not work before app.exec_()
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
        self.gemini_graph = build_gemini_graph(self.config_service) # Pass DB-backed config
        self.gemini_thread: Optional[QThread] = None
        self.gemini_worker: Optional[GeminiWorker] = None

        # --- UI 구성 요소 생성 ---
        create_menu_bar(self)
        create_widgets(self)
        create_layout(self)
        create_status_bar(self)

        # --- 컨트롤러 생성 및 연결 ---
        self.main_controller = MainController(self)
        self.resource_controller = ResourceController(self, self.template_service, self.state_service)
        self.prompt_controller = PromptController(self, self.prompt_service)
        self.xml_controller = XmlController(self, self.xml_service)
        self.file_tree_controller = FileTreeController(self, self.fs_service, self.config_service)

        # --- 시그널 연결 ---
        connect_signals(self)
        # 자동 저장 타이머 시그널 연결
        self.auto_save_timer.timeout.connect(self.resource_controller.save_state_to_default)
        self.state_changed_signal.connect(self.restart_auto_save_timer) # 상태 변경 시 타이머 재시작

        # --- 초기화 작업 ---
        self.resource_controller.load_templates_list()
        self._apply_initial_settings()

        self.status_bar.showMessage("Ready (DB Connected)")
        initial_width = 1200; initial_height = 800
        self.resize(initial_width, initial_height)
        left_width = int(initial_width * 0.35)
        right_width = initial_width - left_width
        self.center_splitter.setSizes([left_width, right_width])
        self.build_tabs.setCurrentIndex(1)
        self.file_tree_controller.reset_file_tree()

        self._initialized = True
        # 프로그램 시작 시 기본 상태 로드 시도 (자동 저장된 내용 복구)
        self.resource_controller.load_state_from_default()
        self.restart_auto_save_timer() # 초기 로드 후 자동 저장 시작

    def _apply_initial_settings(self):
        """Applies initial settings."""
        apply_default_system_prompt(self) # Uses config_service which now reads from DB

        if self.mode == "Meta Prompt Builder":
            meta_prompt_path_relative = os.path.join("prompts", "system", "META_Prompt.md")
            try:
                meta_prompt_path = get_resource_path(meta_prompt_path_relative)
                if os.path.exists(meta_prompt_path):
                    with open(meta_prompt_path, "r", encoding="utf-8") as f:
                        self.system_tab.setText(f.read())
            except Exception as e: logger.error(f"Error loading default META prompt: {e}")

        self.llm_combo.setCurrentIndex(self.llm_combo.findText("Gemini"))
        self.main_controller.on_llm_selected() # Reads default model from DB via config_service
        self.load_gemini_settings_to_ui() # Reads params from DB via config_service
        self.file_tree_controller.load_gitignore_settings() # Reads ignore lists from DB via config_service
        self.resource_controller.update_buttons_label()

    def _restart_with_mode(self, new_mode: str):
        """Restarts the application with the specified mode."""
        self._initialized = False
        self.auto_save_timer.stop() # 타이머 중지
        self.db_service.disconnect() # Disconnect DB before closing
        self.close()
        # Note: Restarting might re-trigger DB connection errors if they persist
        new_window = MainWindow(mode=new_mode)
        new_window.show()

    def _toggle_mode(self):
        """Toggles between application modes."""
        new_mode = "Meta Prompt Builder" if self.mode == "Code Enhancer Prompt Builder" else "Code Enhancer Prompt Builder"
        self._restart_with_mode(new_mode)

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
        dialog.exec_()
        # No need to reload config settings here unless .gitignore affects something immediately
        # Refreshing the filter is handled within the dialog's save_gitignore
        logger.info("Settings dialog closed.")


    # --- Public Methods ---

    def reset_state(self):
        """Resets internal state variables."""
        self._initialized = False
        self.auto_save_timer.stop() # 리셋 시 타이머 중지
        self.current_project_folder = None
        self.last_generated_prompt = ""
        self.selected_files_data = []
        self.tree_generated = False
        self.attached_items = []
        self.api_call_start_time = None # API 시작 시간 초기화
        self.api_timer.stop() # API 타이머 중지
        if hasattr(self, 'checkable_proxy'): self.checkable_proxy.checked_files_dict.clear()
        if hasattr(self, 'attachment_list_widget'): self.attachment_list_widget.clear()
        self.update_window_title()
        if hasattr(self, 'file_tree_controller'): self.file_tree_controller.reset_file_tree()
        if hasattr(self, 'main_controller'):
            self.main_controller.on_llm_selected()
            self.main_controller._stop_token_calculation_thread() # 토큰 계산 스레드 중지
        if hasattr(self, 'summary_tab'): self.summary_tab.clear()
        if hasattr(self, 'api_time_label'): self.api_time_label.setText("API 시간: -") # API 시간 라벨 초기화
        self.load_gemini_settings_to_ui() # Reload settings from DB
        self._initialized = True
        self.restart_auto_save_timer() # 리셋 후 자동 저장 재시작

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
            "mode": self.mode,
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
                 mode=self.mode,
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
        """
        logger.info(f"Setting current state. Partial load: {partial_load}")
        # UI 업데이트 중 시그널/타이머 방지
        was_initialized = self._initialized
        self._initialized = False
        self.auto_save_timer.stop()

        # --- 부분 로드 (마지막 작업 불러오기) ---
        if partial_load:
            # 1. 프로젝트 폴더 로드
            folder_name = None
            if state.project_folder and os.path.isdir(state.project_folder):
                if self.current_project_folder != state.project_folder:
                    self.current_project_folder = state.project_folder
                    folder_name = os.path.basename(state.project_folder)
                    self.project_folder_label.setText(f"현재 프로젝트 폴더: {state.project_folder}")
                    if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                        idx = self.dir_model.setRootPathFiltered(state.project_folder)
                        root_proxy_index = self.checkable_proxy.mapFromSource(idx)
                        self.tree_view.setRootIndex(root_proxy_index)
                    self.status_bar.showMessage(f"Project Folder: {state.project_folder}")
                    self.file_tree_controller.load_gitignore_settings() # 폴더 변경 시 gitignore 다시 로드
                    self.update_window_title(folder_name)
            elif not state.project_folder and self.current_project_folder:
                # 상태 파일에 폴더 정보가 없으면 현재 폴더 유지 (리셋 안 함)
                folder_name = os.path.basename(self.current_project_folder)
                pass
            else:
                # 상태 파일에도 없고 현재도 없으면 초기화
                self.current_project_folder = None
                self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
                self.file_tree_controller.reset_file_tree()
                self.update_window_title()

            # 2. 사용자 프롬프트 로드
            self.user_tab.setText(state.user_prompt)

            # 3. 첨부 파일 로드
            self.attached_items = state.attached_items or []
            self._update_attachment_list_ui()

            # 4. 체크된 파일 복원 (프로젝트 폴더 로드 후에 수행)
            if self.current_project_folder and hasattr(self, 'checkable_proxy'):
                self.checkable_proxy.checked_files_dict.clear() # 기존 체크 상태 초기화
                items_to_check = []
                logger.info(f"Restoring checked files from state: {len(state.checked_files)} items")
                for fpath in state.checked_files:
                    # 상태 파일의 경로는 절대 경로일 수 있으므로, 프로젝트 폴더와 비교하여 상대 경로로 변환 시도
                    try:
                        abs_fpath = os.path.abspath(fpath)
                        abs_proj_folder = os.path.abspath(self.current_project_folder)
                        if abs_fpath.startswith(abs_proj_folder):
                            # 상태 파일에 저장된 경로가 현재 프로젝트 폴더 내에 있는지 확인
                            if os.path.exists(abs_fpath):
                                src_index = self.dir_model.index(abs_fpath)
                                if src_index.isValid():
                                    proxy_index = self.checkable_proxy.mapFromSource(src_index)
                                    if proxy_index.isValid():
                                        # checked_files_dict에는 절대 경로 저장
                                        self.checkable_proxy.checked_files_dict[abs_fpath] = True
                                        items_to_check.append(proxy_index)
                                        logger.debug(f"  Marking {abs_fpath} as checked.")
                                    else:
                                        logger.warning(f"  Could not map source index to proxy for: {abs_fpath}")
                                else:
                                    logger.warning(f"  Could not get source index for: {abs_fpath}")
                            else:
                                logger.warning(f"  Checked file path from state does not exist: {abs_fpath}")
                        else:
                            logger.warning(f"  Checked file path from state is outside current project folder: {abs_fpath}")
                    except Exception as e:
                        logger.error(f"  Error processing checked file path '{fpath}': {e}")

                # UI 업데이트 (dataChanged 시그널 발생)
                logger.info(f"Emitting dataChanged for {len(items_to_check)} restored checked items.")
                for proxy_index in items_to_check:
                    self.checkable_proxy.dataChanged.emit(proxy_index, proxy_index, [Qt.CheckStateRole])
                # 트리 새로고침 대신 시그널 사용

            # 부분 로드 시 다른 UI 요소는 변경하지 않음
            self.status_bar.showMessage("마지막 작업 상태 로드 완료.")

        # --- 전체 로드 (상태 가져오기 등) ---
        else:
            if self.mode != state.mode:
                logger.info(f"Mode mismatch. Restarting...")
                self._restart_with_mode(state.mode)
                return # 재시작 후에는 이 함수 다시 호출 안 됨

            # 전체 리셋 대신 필요한 부분만 업데이트
            # self.reset_state() # 전체 리셋 제거

            folder_name = None
            if state.project_folder and os.path.isdir(state.project_folder):
                self.current_project_folder = state.project_folder
                folder_name = os.path.basename(state.project_folder)
                self.project_folder_label.setText(f"현재 프로젝트 폴더: {state.project_folder}")
                if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                    idx = self.dir_model.setRootPathFiltered(state.project_folder)
                    root_proxy_index = self.checkable_proxy.mapFromSource(idx)
                    self.tree_view.setRootIndex(root_proxy_index)
                self.status_bar.showMessage(f"Project Folder: {state.project_folder}")
            else:
                 self.current_project_folder = None
                 self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
                 self.file_tree_controller.reset_file_tree()

            self.system_tab.setText(state.system_prompt)
            self.user_tab.setText(state.user_prompt)

            llm_index = self.llm_combo.findText(state.selected_llm)
            if llm_index != -1:
                self.llm_combo.setCurrentIndex(llm_index)
                # on_llm_selected 호출 전에 모델 목록 로드
                available_models = self.config_service.get_available_models(state.selected_llm)
                self.model_name_combo.blockSignals(True)
                self.model_name_combo.clear()
                self.model_name_combo.addItems(available_models)
                self.model_name_combo.blockSignals(False)
                # 저장된 모델명 선택 시도
                model_index = self.model_name_combo.findText(state.selected_model_name)
                if model_index != -1:
                    self.model_name_combo.setCurrentIndex(model_index)
                elif available_models:
                    self.model_name_combo.setCurrentIndex(0) # 없으면 첫 번째 모델 선택
                    logger.warning(f"Warning: Saved model '{state.selected_model_name}' not found for {state.selected_llm}. Selecting first available.")
                else:
                    logger.warning(f"No available models found for {state.selected_llm}.")
            else:
                # 저장된 LLM 자체가 없으면 기본값으로 설정
                self.llm_combo.setCurrentIndex(self.llm_combo.findText("Gemini"))
                self.main_controller.on_llm_selected()

            # 첨부 파일 복원
            self.attached_items = state.attached_items or []
            self._update_attachment_list_ui()

            # 체크된 파일 복원 (부분 로드와 동일 로직)
            if self.current_project_folder and hasattr(self, 'checkable_proxy'):
                self.checkable_proxy.checked_files_dict.clear()
                items_to_check = []
                logger.info(f"Restoring checked files from state: {len(state.checked_files)} items")
                for fpath in state.checked_files:
                    try:
                        abs_fpath = os.path.abspath(fpath)
                        abs_proj_folder = os.path.abspath(self.current_project_folder)
                        if abs_fpath.startswith(abs_proj_folder):
                            if os.path.exists(abs_fpath):
                                src_index = self.dir_model.index(abs_fpath)
                                if src_index.isValid():
                                    proxy_index = self.checkable_proxy.mapFromSource(src_index)
                                    if proxy_index.isValid():
                                        self.checkable_proxy.checked_files_dict[abs_fpath] = True
                                        items_to_check.append(proxy_index)
                                        logger.debug(f"  Marking {abs_fpath} as checked.")
                                    else: logger.warning(f"  Could not map source index to proxy for: {abs_fpath}")
                                else: logger.warning(f"  Could not get source index for: {abs_fpath}")
                            else: logger.warning(f"  Checked file path from state does not exist: {abs_fpath}")
                        else: logger.warning(f"  Checked file path from state is outside current project folder: {abs_fpath}")
                    except Exception as e: logger.error(f"  Error processing checked file path '{fpath}': {e}")

                logger.info(f"Emitting dataChanged for {len(items_to_check)} restored checked items.")
                for proxy_index in items_to_check:
                    self.checkable_proxy.dataChanged.emit(proxy_index, proxy_index, [Qt.CheckStateRole])

            self.file_tree_controller.load_gitignore_settings() # gitignore 로드
            self.update_window_title(folder_name)
            self.resource_controller.update_buttons_label()
            self.load_gemini_settings_to_ui() # Gemini 파라미터 로드

            self.status_bar.showMessage("State loaded successfully!")

        # 공통 마무리 작업
        self._initialized = was_initialized # 원래 상태로 복원
        self.main_controller.update_char_count_for_active_tab()
        self.token_count_label.setText("토큰 계산: -")
        if hasattr(self, 'api_time_label'): self.api_time_label.setText("API 시간: -")
        self.restart_auto_save_timer() # 상태 로드 후 자동 저장 재시작

    def uncheck_all_files(self):
        """Unchecks all items in the file tree view."""
        if not hasattr(self, 'checkable_proxy'): return
        paths_to_uncheck = list(self.checkable_proxy.checked_files_dict.keys())
        self.checkable_proxy.checked_files_dict.clear()
        for fpath in paths_to_uncheck:
            src_index = self.dir_model.index(fpath)
            if src_index.isValid():
                proxy_index = self.checkable_proxy.mapFromSource(src_index)
                if proxy_index.isValid():
                    self.checkable_proxy.dataChanged.emit(proxy_index, proxy_index, [Qt.CheckStateRole])
        self.state_changed_signal.emit() # 상태 변경 시그널 발생

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
                            icon = QIcon(pixmap.scaled(QSize(32, 32), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        else:
                           icon = self.style().standardIcon(QStyle.SP_FileIcon)
                    except Exception as e:
                        logger.error(f"Error creating thumbnail for {item_name}: {e}")
                        icon = self.style().standardIcon(QStyle.SP_FileIcon)
                else:
                    icon = self.style().standardIcon(QStyle.SP_FileIcon)

            elif item_type == 'file':
                icon = self.style().standardIcon(QStyle.SP_FileIcon)
            else:
                icon = self.style().standardIcon(QStyle.SP_FileIcon)
            list_item.setIcon(icon)
            self.attachment_list_widget.addItem(list_item)
        # 첨부 목록 변경 시 상태 변경 시그널 발생 (자동 저장용)
        # self.state_changed_signal.emit() # 여기서 호출하면 너무 빈번할 수 있음. attach/paste/remove 함수에서 호출.

    # --- LangGraph 관련 메서드 ---
    def send_prompt_to_gemini(self):
        """ Sends the prompt and attachments to Gemini via LangGraph worker thread. """
        if self.mode == "Meta Prompt Builder":
            QMessageBox.information(self, "정보", "Meta Prompt Builder 모드에서는 Gemini 전송 기능을 사용할 수 없습니다.")
            return
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
            "error_message": None
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
        if not self._initialized: return
        try:
            settings = self.config_service.get_settings()
            self.gemini_temp_edit.blockSignals(True); self.gemini_thinking_checkbox.blockSignals(True)
            self.gemini_budget_edit.blockSignals(True); self.gemini_search_checkbox.blockSignals(True)

            self.gemini_temp_edit.setText(str(settings.gemini_temperature))
            self.gemini_thinking_checkbox.setChecked(settings.gemini_enable_thinking)
            self.gemini_budget_edit.setText(str(settings.gemini_thinking_budget))
            self.gemini_search_checkbox.setChecked(settings.gemini_enable_search)

            self.gemini_temp_edit.blockSignals(False); self.gemini_thinking_checkbox.blockSignals(False)
            self.gemini_budget_edit.blockSignals(False); self.gemini_search_checkbox.blockSignals(False)
            is_gemini_selected = (self.llm_combo.currentText() == "Gemini")
            if hasattr(self, 'gemini_param_widget'): self.gemini_param_widget.setVisible(is_gemini_selected)
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
        file_path = self.checkable_proxy.get_file_path_from_index(index)
        if not file_path: return
        menu = QMenu()
        rename_action = menu.addAction("이름 변경"); delete_action = menu.addAction("삭제")
        action = menu.exec_(self.tree_view.viewport().mapToGlobal(position))
        if action == rename_action: self.file_tree_controller.rename_item(file_path)
        elif action == delete_action: self.file_tree_controller.delete_item(file_path)

    def on_tree_view_item_clicked(self, index: QModelIndex):
        """Handles item clicks in the tree view to toggle check state."""
        if not index.isValid() or index.column() != 0: return
        current_state = self.checkable_proxy.data(index, Qt.CheckStateRole)
        new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
        self.checkable_proxy.setData(index, new_state, Qt.CheckStateRole)
        # 체크 상태 변경 시 자동 저장 타이머 재시작
        self.state_changed_signal.emit()

    def restart_auto_save_timer(self):
        """Restarts the auto-save timer."""
        if self._initialized:
            # logger.debug("Restarting auto-save timer.")
            self.auto_save_timer.start(10000) # 10초 후 저장

    def closeEvent(self, event):
        """Ensure database connection is closed and threads are stopped when the window closes."""
        logger.info("Closing MainWindow. Stopping threads and disconnecting database.")
        self.auto_save_timer.stop() # 윈도우 닫을 때 자동 저장 타이머 중지
        self.api_timer.stop() # 윈도우 닫을 때 API 타이머 중지
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

