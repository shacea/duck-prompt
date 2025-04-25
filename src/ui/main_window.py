
import os
import io
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu,
    QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox,
    QFrame, QLineEdit, QDialog, QListWidget, QListWidgetItem, QStyle
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont, QDesktopServices, QPixmap, QImage # QPixmap, QImage 추가
from PyQt5.QtCore import Qt, QSize, QStandardPaths, QModelIndex, QItemSelection, QUrl, QThread, pyqtSignal, QObject, QBuffer, QIODevice # QBuffer, QIODevice 추가
import logging # 로깅 추가

# 변경된 경로에서 import
from core.pydantic_models.app_state import AppState
from core.services.config_service import ConfigService
from core.services.state_service import StateService
from core.services.template_service import TemplateService
from core.services.prompt_service import PromptService
from core.services.xml_service import XmlService
from core.services.filesystem_service import FilesystemService
from core.services.token_service import TokenCalculationService
from core.services.gemini_service import build_gemini_graph
from core.langgraph_state import GeminiGraphState

from ui.models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
from ui.controllers.main_controller import MainController
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
        self._is_saving_gemini_settings = False
        self.attached_items: List[Dict[str, Any]] = [] # 첨부 파일 목록 상태 변수

        # --- 서비스 인스턴스 생성 ---
        self.config_service = ConfigService()
        self.state_service = StateService()
        self.template_service = TemplateService()
        self.prompt_service = PromptService()
        self.xml_service = XmlService()
        self.fs_service = FilesystemService(self.config_service)
        self.token_service = TokenCalculationService(self.config_service)
        self.gemini_graph = build_gemini_graph(self.config_service)
        self.gemini_thread: Optional[QThread] = None
        self.gemini_worker: Optional[GeminiWorker] = None

        # --- UI 구성 요소 생성 ---
        create_menu_bar(self)
        create_widgets(self) # attachment_list_widget 등 생성
        create_layout(self)
        create_status_bar(self)

        # --- 컨트롤러 생성 및 연결 ---
        self.main_controller = MainController(self)
        self.resource_controller = ResourceController(self, self.template_service, self.state_service)
        self.prompt_controller = PromptController(self, self.prompt_service)
        self.xml_controller = XmlController(self, self.xml_service)
        self.file_tree_controller = FileTreeController(self, self.fs_service, self.config_service)

        # --- 시그널 연결 ---
        connect_signals(self) # attach_file_btn 등 시그널 연결

        # --- 초기화 작업 ---
        self.resource_controller.load_templates_list()
        self._apply_initial_settings()

        self.status_bar.showMessage("Ready")
        initial_width = 1200; initial_height = 800
        self.resize(initial_width, initial_height)
        left_width = int(initial_width * 0.35)
        right_width = initial_width - left_width
        self.center_splitter.setSizes([left_width, right_width])
        self.build_tabs.setCurrentIndex(1)
        self.file_tree_controller.reset_file_tree()

        self._initialized = True

    def _apply_initial_settings(self):
        """Applies initial settings."""
        apply_default_system_prompt(self)

        if self.mode == "Meta Prompt Builder":
            meta_prompt_path_relative = os.path.join("prompts", "system", "META_Prompt.md")
            try:
                meta_prompt_path = get_resource_path(meta_prompt_path_relative)
                if os.path.exists(meta_prompt_path):
                    with open(meta_prompt_path, "r", encoding="utf-8") as f:
                        self.system_tab.setText(f.read())
            except Exception as e: print(f"Error loading default META prompt: {e}")

        self.llm_combo.setCurrentIndex(self.llm_combo.findText("Gemini"))
        self.main_controller.on_llm_selected()
        self.load_gemini_settings_to_ui()
        self.file_tree_controller.load_gitignore_settings()
        self.resource_controller.update_buttons_label()

    def _restart_with_mode(self, new_mode: str):
        """Restarts the application with the specified mode."""
        self._initialized = False
        self.close()
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
        if dialog.exec_() == QDialog.Accepted:
            print("Settings saved. Applying changes...")
            apply_default_system_prompt(self)
            self.main_controller.on_llm_selected()
            self.file_tree_controller.load_gitignore_settings()
            self.token_service._init_gemini()
            self.token_service._init_anthropic()
            if self._initialized:
                 self.main_controller.update_char_count_for_active_tab()
                 self.token_count_label.setText("토큰 계산: -")
            self.load_gemini_settings_to_ui()
            self.status_bar.showMessage("Settings applied.")
        else:
             self.file_tree_controller.load_gitignore_settings()
             print("Settings dialog cancelled.")

    # --- Public Methods ---

    def reset_state(self):
        """Resets internal state variables."""
        self._initialized = False
        self.current_project_folder = None
        self.last_generated_prompt = ""
        self.selected_files_data = []
        self.tree_generated = False
        self.attached_items = [] # 첨부 파일 목록 초기화
        if hasattr(self, 'checkable_proxy'): self.checkable_proxy.checked_files_dict.clear()
        if hasattr(self, 'attachment_list_widget'): self.attachment_list_widget.clear() # UI 목록 초기화
        self.update_window_title()
        if hasattr(self, 'file_tree_controller'): self.file_tree_controller.reset_file_tree()
        if hasattr(self, 'main_controller'): self.main_controller.on_llm_selected()
        if hasattr(self, 'summary_tab'): self.summary_tab.clear()
        self.load_gemini_settings_to_ui()
        self._initialized = True

    def update_window_title(self, folder_name: Optional[str] = None):
        """Updates the window title."""
        title = f"{folder_name} - {self.base_title}" if folder_name else self.base_title
        self.setWindowTitle(title)

    def get_current_state(self) -> AppState:
        """Gathers the current UI state."""
        checked_paths = self.checkable_proxy.get_all_checked_paths() if hasattr(self, 'checkable_proxy') else []
        selected_llm = self.llm_combo.currentText() if hasattr(self, 'llm_combo') else "Gemini"
        selected_model_name = self.model_name_combo.currentText().strip() if hasattr(self, 'model_name_combo') else ""

        # attached_items에서 data 필드는 제외하고 저장 (용량 문제)
        # 로드 시 path가 있으면 다시 읽어오도록 처리
        serializable_attachments = []
        for item in self.attached_items:
            s_item = item.copy()
            s_item.pop('data', None) # data 필드 제거
            serializable_attachments.append(s_item)

        state_data = {
            "mode": self.mode,
            "project_folder": self.current_project_folder,
            "system_prompt": self.system_tab.toPlainText(),
            "user_prompt": self.user_tab.toPlainText(),
            "checked_files": checked_paths,
            "selected_llm": selected_llm,
            "selected_model_name": selected_model_name,
            "attached_items": serializable_attachments, # 직렬화 가능한 버전 저장
        }
        try:
            app_state = AppState(**state_data)
            return app_state
        except Exception as e:
             print(f"Error creating AppState model: {e}")
             default_state = AppState(mode=self.mode)
             default_state.selected_llm = selected_llm
             default_state.selected_model_name = selected_model_name
             return default_state

    def set_current_state(self, state: AppState):
        """Sets the UI state based on the provided AppState model."""
        if self.mode != state.mode:
            print(f"Mode mismatch. Restarting...")
            self._restart_with_mode(state.mode)
            return

        self._initialized = False
        self.reset_state() # UI 초기화
        self._initialized = False # 토큰 계산 방지

        folder_name = None
        if state.project_folder and os.path.isdir(state.project_folder):
            self.current_project_folder = state.project_folder
            folder_name = os.path.basename(state.project_folder)
            self.project_folder_label.setText(f"현재 프로젝트 폴더: {state.project_folder}")
            if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                idx = self.dir_model.setRootPathFiltered(state.project_folder)
                root_proxy_index = self.checkable_proxy.mapFromSource(idx)
                self.tree_view.setRootIndex(root_proxy_index)
                if root_proxy_index.isValid():
                    self.checkable_proxy.setData(root_proxy_index, Qt.Checked, Qt.CheckStateRole)
            self.status_bar.showMessage(f"Project Folder: {state.project_folder}")
        else:
             self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")

        self.system_tab.setText(state.system_prompt)
        self.user_tab.setText(state.user_prompt)

        llm_index = self.llm_combo.findText(state.selected_llm)
        if llm_index != -1:
            self.llm_combo.setCurrentIndex(llm_index)
            self.main_controller.on_llm_selected()
            model_index = self.model_name_combo.findText(state.selected_model_name)
            if model_index != -1: self.model_name_combo.setCurrentIndex(model_index)
            else: print(f"Warning: Saved model '{state.selected_model_name}' not found.")
        else: self.main_controller.on_llm_selected()

        # Restore attached items (data는 로드하지 않음, 필요 시 path로 접근)
        self.attached_items = state.attached_items or []
        self._update_attachment_list_ui() # UI 업데이트

        if self.current_project_folder and hasattr(self, 'checkable_proxy'):
            self.checkable_proxy.checked_files_dict.clear()
            items_to_check = []
            for fpath in state.checked_files:
                 if fpath.startswith(self.current_project_folder):
                     src_index = self.dir_model.index(fpath)
                     if src_index.isValid():
                         proxy_index = self.checkable_proxy.mapFromSource(src_index)
                         if proxy_index.isValid(): items_to_check.append(proxy_index)
            for proxy_index in items_to_check:
                fpath = self.checkable_proxy.get_file_path_from_index(proxy_index)
                if fpath: self.checkable_proxy.checked_files_dict[fpath] = True
            for proxy_index in items_to_check:
                 self.checkable_proxy.dataChanged.emit(proxy_index, proxy_index, [Qt.CheckStateRole])

        self.file_tree_controller.load_gitignore_settings()
        self.update_window_title(folder_name)
        self.resource_controller.update_buttons_label()
        self.load_gemini_settings_to_ui()

        self._initialized = True
        self.status_bar.showMessage("State loaded successfully!")
        self.main_controller.update_char_count_for_active_tab()
        self.token_count_label.setText("토큰 계산: -")

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
            new_tab.textChanged.connect(self.main_controller.update_char_count_for_active_tab)
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
            # 아이콘 추가 (선택적)
            icon = QIcon()
            if item_type == 'image':
                # 이미지 데이터가 있으면 썸네일 생성 시도
                img_data = item.get('data')
                if not img_data and item.get('path') and os.path.exists(item['path']):
                    try:
                        with open(item['path'], 'rb') as f: img_data = f.read()
                    except Exception: pass # 읽기 실패 시 무시

                if img_data:
                    try:
                        pixmap = QPixmap()
                        pixmap.loadFromData(img_data)
                        if not pixmap.isNull():
                            icon = QIcon(pixmap.scaled(QSize(32, 32), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        else: # 로드 실패 시 기본 아이콘
                           icon = self.style().standardIcon(QStyle.SP_FileIcon) # 기본 파일 아이콘
                    except Exception as e:
                        print(f"Error creating thumbnail for {item_name}: {e}")
                        icon = self.style().standardIcon(QStyle.SP_FileIcon)
                else: # 데이터 없으면 기본 아이콘
                    icon = self.style().standardIcon(QStyle.SP_FileIcon)

            elif item_type == 'file':
                icon = self.style().standardIcon(QStyle.SP_FileIcon)
            else:
                icon = self.style().standardIcon(QStyle.SP_FileIcon)
            list_item.setIcon(icon)
            self.attachment_list_widget.addItem(list_item)

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
        # 첨부 파일 데이터 로드 (API 호출 직전에 수행)
        loaded_attachments = []
        for item in self.attached_items:
            if not item.get('data') and item.get('path') and os.path.exists(item['path']):
                try:
                    with open(item['path'], 'rb') as f:
                        item['data'] = f.read() # 데이터 로드
                    print(f"Loaded data for attachment: {item['name']}")
                except Exception as e:
                    QMessageBox.warning(self, "첨부 파일 오류", f"첨부 파일 '{item['name']}' 로드 실패: {e}")
                    # 로드 실패 시 해당 파일 제외 또는 전체 중단 결정 필요
                    # 여기서는 일단 계속 진행 (Gemini 서비스에서 data 없는 항목은 스킵)
            loaded_attachments.append(item)


        if not prompt_text.strip() and not loaded_attachments:
            QMessageBox.warning(self, "경고", "Gemini에 전송할 프롬프트 내용이나 첨부 파일이 없습니다.")
            return

        if hasattr(self, 'send_to_gemini_btn'): self.send_to_gemini_btn.setEnabled(False)
        self.status_bar.showMessage("Gemini API 호출 중...")
        QApplication.processEvents()

        if self.gemini_thread and self.gemini_thread.isRunning():
            print("Terminating previous Gemini thread...")
            self.gemini_thread.quit(); self.gemini_thread.wait()

        # LangGraph 초기 상태 구성
        selected_model_name = self.model_name_combo.currentText().strip() # 현재 선택된 모델명 가져오기
        initial_state: GeminiGraphState = {
            "input_prompt": prompt_text,
            "input_attachments": loaded_attachments, # 로드된 첨부 데이터 전달
            "selected_model_name": selected_model_name, # 모델명 추가
            "gemini_response": "",
            "xml_output": "",
            "summary_output": "",
            "error_message": None
        }

        self.gemini_thread = QThread()
        self.gemini_worker = GeminiWorker(self.gemini_graph, initial_state) # 초기 상태 전달
        self.gemini_worker.moveToThread(self.gemini_thread)

        self.gemini_thread.started.connect(self.gemini_worker.run)
        self.gemini_worker.finished.connect(self.handle_gemini_response)
        self.gemini_worker.error.connect(self.handle_gemini_error)
        # Ensure thread quits and objects are deleted on finish/error
        self.gemini_worker.finished.connect(self.gemini_thread.quit)
        self.gemini_worker.finished.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)
        self.gemini_worker.error.connect(self.gemini_thread.quit) # Quit thread on error too
        self.gemini_worker.error.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.cleanup_gemini_thread) # Connect cleanup

        self.gemini_thread.start()

    def handle_gemini_response(self, xml_result: str, summary_result: str):
        """ Handles Gemini response. """
        print("--- Handling Gemini Response ---")
        if hasattr(self, 'xml_input_tab'):
            self.xml_input_tab.setPlainText(xml_result)
            print(f"XML Output Length: {len(xml_result)}")
        if hasattr(self, 'summary_tab'):
            self.summary_tab.setPlainText(summary_result)
            print(f"Summary Output Length: {len(summary_result)}")
            self.build_tabs.setCurrentWidget(self.summary_tab)
        self.status_bar.showMessage("Gemini 응답 처리 완료.")
        if hasattr(self, 'send_to_gemini_btn'): self.send_to_gemini_btn.setEnabled(True)

    def handle_gemini_error(self, error_msg: str):
        """ Handles Gemini error, showing user-friendly message for specific API response issues. """
        print(f"--- Handling Gemini Error: {error_msg} ---")
        logger.error(f"Gemini Error Received: {error_msg}") # Log the full error

        user_display_error = error_msg # Default to showing the full message
        # Check for specific error patterns indicating API response issues
        if "Gemini API 응답 처리 오류" in error_msg or "Gemini API 응답 문제 발생" in error_msg:
             user_display_error = "Gemini API 응답 문제입니다. 자세한 내용은 Summary 탭을 확인하세요."
             # Put the detailed error message into the summary tab
             if hasattr(self, 'summary_tab'):
                 self.summary_tab.setPlainText(f"Gemini 오류 상세:\n{error_msg}")
                 # Optionally switch to the summary tab
                 # self.build_tabs.setCurrentWidget(self.summary_tab)

        QMessageBox.critical(self, "Gemini API 오류", user_display_error)
        self.status_bar.showMessage("Gemini API 호출 오류.")
        if hasattr(self, 'send_to_gemini_btn'): self.send_to_gemini_btn.setEnabled(True)


    def cleanup_gemini_thread(self):
        """ Cleans up Gemini thread and worker objects. """
        print("--- Cleaning up Gemini thread and worker ---")
        self.gemini_thread = None
        self.gemini_worker = None
        # Re-enable button just in case it was missed
        if hasattr(self, 'send_to_gemini_btn'): self.send_to_gemini_btn.setEnabled(True)


    # --- Gemini 파라미터 관리 메서드 ---
    def load_gemini_settings_to_ui(self):
        """Loads Gemini parameters from config.yml to UI."""
        if not self._initialized: return
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

    def save_gemini_settings(self):
        """Saves Gemini parameters from UI to config.yml."""
        if not self._initialized or self._is_saving_gemini_settings: return
        self._is_saving_gemini_settings = True
        try:
            try:
                temp_str = self.gemini_temp_edit.text().strip(); temperature = float(temp_str) if temp_str else 0.0
                if not (0.0 <= temperature <= 2.0): raise ValueError("Temp out of range")
            except ValueError: print(f"Invalid temperature"); self._is_saving_gemini_settings = False; return
            enable_thinking = self.gemini_thinking_checkbox.isChecked()
            try:
                budget_str = self.gemini_budget_edit.text().strip(); thinking_budget = int(budget_str) if budget_str else 0
                if thinking_budget < 0: raise ValueError("Budget negative")
            except ValueError: print(f"Invalid budget"); self._is_saving_gemini_settings = False; return
            enable_search = self.gemini_search_checkbox.isChecked()
            update_data = {
                "gemini_temperature": temperature, "gemini_enable_thinking": enable_thinking,
                "gemini_thinking_budget": thinking_budget, "gemini_enable_search": enable_search,
            }
            self.config_service.update_settings(**update_data)
            print(f"Gemini settings saved: {update_data}")
        except Exception as e:
            print(f"Error saving Gemini settings: {e}")
            QMessageBox.warning(self, "오류", f"Gemini 설정 저장 중 오류 발생: {e}")
        finally: self._is_saving_gemini_settings = False

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
