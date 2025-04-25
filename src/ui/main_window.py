

import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu,
    QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox,
    QFrame, QLineEdit, QDialog # QDialog 추가
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont, QDesktopServices
from PyQt5.QtCore import Qt, QSize, QStandardPaths, QModelIndex, QItemSelection, QUrl, QThread, pyqtSignal, QObject # QThread, pyqtSignal, QObject 추가

# 변경된 경로에서 import
from core.pydantic_models.app_state import AppState # 상태 타입 힌트용
from core.services.config_service import ConfigService
from core.services.state_service import StateService
from core.services.template_service import TemplateService
from core.services.prompt_service import PromptService
from core.services.xml_service import XmlService
from core.services.filesystem_service import FilesystemService
from core.services.token_service import TokenCalculationService # Added
from core.services.gemini_service import build_gemini_graph # LangGraph 빌더 함수 임포트
from core.langgraph_state import GeminiGraphState # LangGraph 상태 임포트

from ui.models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
# 컨트롤러 import
from ui.controllers.main_controller import MainController
from ui.controllers.resource_controller import ResourceController
from ui.controllers.prompt_controller import PromptController
from ui.controllers.xml_controller import XmlController
from ui.controllers.file_tree_controller import FileTreeController
from ui.controllers.system_prompt_controller import apply_default_system_prompt

# UI 및 시그널 설정 함수 import
from .main_window_setup_ui import create_menu_bar, create_widgets, create_layout, create_status_bar
from .main_window_setup_signals import connect_signals

# 설정 다이얼로그 import
from .settings_dialog import SettingsDialog

from ui.widgets.custom_text_edit import CustomTextEdit
from ui.widgets.custom_tab_bar import CustomTabBar # CustomTabBar 임포트
from utils.helpers import get_resource_path

# --- Gemini API 호출을 위한 Worker 클래스 ---
class GeminiWorker(QObject):
    finished = pyqtSignal(str, str) # XML, Summary 결과 전달
    error = pyqtSignal(str)         # 오류 메시지 전달

    def __init__(self, graph_app, prompt):
        super().__init__()
        self.graph_app = graph_app
        self.prompt = prompt

    def run(self):
        """LangGraph 워크플로우를 실행합니다."""
        try:
            # LangGraph 실행 (상태 초기화 및 입력 전달)
            # 입력 상태는 LangGraph 상태 정의와 일치해야 함
            initial_state: GeminiGraphState = {"input_prompt": self.prompt, "gemini_response": "", "xml_output": "", "summary_output": "", "error_message": None}
            # LangGraph 실행 (.invoke 사용)
            final_state = self.graph_app.invoke(initial_state)

            # 최종 상태에서 결과 확인
            if final_state.get("error_message"):
                self.error.emit(final_state["error_message"])
            else:
                xml_result = final_state.get("xml_output", "")
                summary_result = final_state.get("summary_output", "")
                self.finished.emit(xml_result, summary_result)
        except Exception as e:
            # LangGraph 실행 자체에서 발생한 예외 처리
            self.error.emit(f"LangGraph execution error: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self, mode="Code Enhancer Prompt Builder"):
        super().__init__()
        self._initialized = False # 초기화 완료 플래그
        self.mode = mode
        self.base_title = "DuckPrompt"
        self.update_window_title() # 초기 제목 설정

        # 스타일 설정
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        # --- 상태 변수 ---
        self.current_project_folder: Optional[str] = None
        self.last_generated_prompt: str = "" # 마지막 생성된 프롬프트 (단순 문자열)
        self.selected_files_data: List[tuple] = [] # 선택된 파일 정보 (UI 표시용)
        self.tree_generated: bool = False # 파일 트리 생성 여부
        self._is_saving_gemini_settings = False # Gemini 설정 저장 중 플래그

        # --- 서비스 인스턴스 생성 ---
        # 서비스 인스턴스는 MainWindow 내에서 생성 및 관리
        self.config_service = ConfigService()
        self.state_service = StateService()
        self.template_service = TemplateService()
        self.prompt_service = PromptService()
        self.xml_service = XmlService()
        self.fs_service = FilesystemService(self.config_service)
        # Pass config_service to TokenCalculationService
        self.token_service = TokenCalculationService(self.config_service) # Modified
        # LangGraph 앱 빌드 (ConfigService 주입)
        self.gemini_graph = build_gemini_graph(self.config_service)
        self.gemini_thread: Optional[QThread] = None # 스레드 관리를 위한 변수
        self.gemini_worker: Optional[GeminiWorker] = None # 워커 관리를 위한 변수

        # --- UI 구성 요소 생성 (외부 함수 호출) ---
        create_menu_bar(self)
        create_widgets(self) # 여기서 summary_tab, send_to_gemini_btn 생성됨
        create_layout(self)
        create_status_bar(self)

        # --- 컨트롤러 생성 및 연결 ---
        # 각 컨트롤러에 MainWindow와 필요한 서비스 주입
        self.main_controller = MainController(self) # Needs token_service, config_service (gets them from mw)
        self.resource_controller = ResourceController(self, self.template_service, self.state_service)
        self.prompt_controller = PromptController(self, self.prompt_service)
        self.xml_controller = XmlController(self, self.xml_service)
        self.file_tree_controller = FileTreeController(self, self.fs_service, self.config_service)

        # --- 시그널 연결 (외부 함수 호출) ---
        connect_signals(self) # 여기서 send_to_gemini_btn 시그널 연결됨

        # --- 초기화 작업 ---
        self.resource_controller.load_templates_list() # 리소스 목록 로드
        self._apply_initial_settings() # 기본 설정 적용 (기본 프롬프트, 모델명, Gemini 파라미터 등)

        # 상태바 메시지 및 창 크기 설정
        self.status_bar.showMessage("Ready")
        initial_width = 1200
        initial_height = 800
        self.resize(initial_width, initial_height)

        # 초기 스플리터 크기 설정 (파일 탐색기+리소스:탭 위젯 비율 조정)
        left_width = int(initial_width * 0.35) # 왼쪽 영역 너비 조정
        right_width = initial_width - left_width
        self.center_splitter.setSizes([left_width, right_width])

        self.build_tabs.setCurrentIndex(1) # 사용자 탭을 기본으로 표시

        # 초기/리셋 시 파일 탐색기 비우기
        self.file_tree_controller.reset_file_tree()

        self._initialized = True # 초기화 완료

    def _apply_initial_settings(self):
        """Applies initial settings like default system prompt, model names, and Gemini parameters."""
        apply_default_system_prompt(self) # 기본 시스템 프롬프트 로드

        if self.mode == "Meta Prompt Builder":
            meta_prompt_path_relative = os.path.join("prompts", "system", "META_Prompt.md")
            try:
                meta_prompt_path = get_resource_path(meta_prompt_path_relative)
                if os.path.exists(meta_prompt_path):
                    with open(meta_prompt_path, "r", encoding="utf-8") as f:
                        self.system_tab.setText(f.read())
            except Exception as e:
                print(f"Error loading default META prompt: {e}")

        # Load initial model settings from config
        self.llm_combo.setCurrentIndex(self.llm_combo.findText("Gemini")) # Default to Gemini UI
        self.main_controller.on_llm_selected() # This will load available models and set the default

        # Load initial Gemini parameters from config
        self.load_gemini_settings_to_ui()

        self.file_tree_controller.load_gitignore_settings() # FileTreeController
        self.resource_controller.update_buttons_label() # ResourceController

    def _restart_with_mode(self, new_mode: str):
        """Restarts the application with the specified mode."""
        self._initialized = False # 재시작 전 초기화 플래그 해제
        self.close()
        new_window = MainWindow(mode=new_mode)
        new_window.show()

    def _toggle_mode(self):
        """Toggles between application modes."""
        if self.mode == "Code Enhancer Prompt Builder":
            self._restart_with_mode("Meta Prompt Builder")
        else:
            self._restart_with_mode("Code Enhancer Prompt Builder")

    def _open_readme(self):
        """Opens the README.md file in the default web browser or text editor."""
        # README.md 파일 경로 찾기 (main.py 기준)
        readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'README.md'))
        if os.path.exists(readme_path):
            # QDesktopServices를 사용하여 파일 열기 시도
            url = QUrl.fromLocalFile(readme_path)
            if not QDesktopServices.openUrl(url):
                QMessageBox.warning(self, "오류", "README.md 파일을 여는 데 실패했습니다.\n파일 탐색기에서 직접 열어주세요.")
        else:
            QMessageBox.warning(self, "오류", "README.md 파일을 찾을 수 없습니다.")

    def open_settings_dialog(self):
        """Opens the settings dialog."""
        # Pass self (MainWindow instance) to the dialog
        dialog = SettingsDialog(self, self)
        if dialog.exec_() == QDialog.Accepted: # QDialog 사용
            # 설정(config.yml)이 저장되면 필요한 UI 업데이트 수행
            print("Settings saved. Applying changes...")
            # 1. 기본 시스템 프롬프트 다시 로드 시도
            apply_default_system_prompt(self)
            # 2. LLM 기본 모델명 및 사용 가능 목록 업데이트 (콤보박스 현재 값 기준)
            self.main_controller.on_llm_selected() # 토큰 계산은 내부 플래그로 제어됨
            # 3. 파일 트리 필터 업데이트 (gitignore 관련 설정 변경 시)
            self.file_tree_controller.load_gitignore_settings()
            # 4. 토큰 서비스 재초기화 (API 키 변경 시)
            self.token_service._init_gemini()
            self.token_service._init_anthropic()
            # 5. 상태바 업데이트 (토큰 계산 등) - 토큰 계산은 하지 않고 레이블만 리셋
            if self._initialized: # 초기화 완료 후 실행
                 self.main_controller.update_char_count_for_active_tab() # 문자수만 업데이트
                 self.token_count_label.setText("토큰 계산: -") # 토큰 레이블 리셋
            # 6. 메인 창의 Gemini 파라미터 UI 업데이트 (설정 다이얼로그에서 변경되었을 수 있으므로)
            self.load_gemini_settings_to_ui()

            self.status_bar.showMessage("Settings applied.")
        else:
            # 사용자가 취소한 경우에도 .gitignore 변경사항이 있을 수 있으므로 필터 업데이트
             self.file_tree_controller.load_gitignore_settings()
             print("Settings dialog cancelled.")


    # --- Public Methods (Controller에서 호출) ---

    def reset_state(self):
        """Resets internal state variables of the MainWindow."""
        self._initialized = False # 리셋 시작 시 플래그 해제
        self.current_project_folder = None
        self.last_generated_prompt = ""
        self.selected_files_data = []
        self.tree_generated = False
        if hasattr(self, 'checkable_proxy'):
            self.checkable_proxy.checked_files_dict.clear()
        self.update_window_title()
        # 파일 트리 비우기 (컨트롤러 호출)
        if hasattr(self, 'file_tree_controller'):
            self.file_tree_controller.reset_file_tree()
        # 모델 선택 UI 초기화 (MainController에서 처리)
        if hasattr(self, 'main_controller'):
             self.main_controller.on_llm_selected() # Resets model combo based on default LLM
        # Summary 탭 내용 지우기
        if hasattr(self, 'summary_tab'):
            self.summary_tab.clear()
        # Gemini 파라미터 UI 초기값 로드
        self.load_gemini_settings_to_ui()
        self._initialized = True # 리셋 완료 후 플래그 설정


    def update_window_title(self, folder_name: Optional[str] = None):
        """Updates the window title based on the project folder."""
        if folder_name:
            self.setWindowTitle(f"{folder_name} - {self.base_title}")
        else:
            self.setWindowTitle(self.base_title)

    def get_current_state(self) -> AppState:
        """Gathers the current UI state and returns it as an AppState model."""
        checked_paths = self.checkable_proxy.get_all_checked_paths() if hasattr(self, 'checkable_proxy') else []
        selected_llm = self.llm_combo.currentText() if hasattr(self, 'llm_combo') else "Gemini"
        selected_model_name = self.model_name_combo.currentText().strip() if hasattr(self, 'model_name_combo') else "" # QComboBox 사용

        state_data = {
            "mode": self.mode,
            "project_folder": self.current_project_folder,
            "system_prompt": self.system_tab.toPlainText(),
            "user_prompt": self.user_tab.toPlainText(),
            "checked_files": checked_paths,
            "selected_llm": selected_llm,
            "selected_model_name": selected_model_name,
            # Gemini 파라미터는 AppState에서 제거됨
        }
        try:
            app_state = AppState(**state_data)
            return app_state
        except Exception as e:
             print(f"Error creating AppState model: {e}")
             # Return default state but preserve current mode
             default_state = AppState(mode=self.mode)
             # Try to preserve model selection if possible
             default_state.selected_llm = selected_llm
             default_state.selected_model_name = selected_model_name
             return default_state


    def set_current_state(self, state: AppState):
        """Sets the UI state based on the provided AppState model."""
        if self.mode != state.mode:
            print(f"Mode mismatch during state load. Current: {self.mode}, Loaded: {state.mode}. Restarting...")
            self._restart_with_mode(state.mode)
            return

        self._initialized = False # 상태 로드 시작 시 플래그 해제
        self.reset_state() # UI 및 내부 상태 초기화 (트리 포함) - 내부에서 _initialized=True 설정됨

        self._initialized = False # reset_state 후 다시 False로 설정하여 아래 로직 중 토큰 계산 방지

        folder_name = None
        if state.project_folder and os.path.isdir(state.project_folder):
            self.current_project_folder = state.project_folder
            folder_name = os.path.basename(state.project_folder)
            self.project_folder_label.setText(f"현재 프로젝트 폴더: {state.project_folder}")
            if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                idx = self.dir_model.setRootPathFiltered(state.project_folder) # dir_model 사용
                root_proxy_index = self.checkable_proxy.mapFromSource(idx) # checkable_proxy 사용
                self.tree_view.setRootIndex(root_proxy_index) # tree_view 사용
                # 루트 폴더 자동 체크 (선택적)
                if root_proxy_index.isValid():
                    self.checkable_proxy.setData(root_proxy_index, Qt.Checked, Qt.CheckStateRole)

            self.status_bar.showMessage(f"Project Folder: {state.project_folder}")
        else:
             self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")

        self.system_tab.setText(state.system_prompt)
        self.user_tab.setText(state.user_prompt)

        # Restore model selection state
        llm_index = self.llm_combo.findText(state.selected_llm)
        if llm_index != -1:
            self.llm_combo.setCurrentIndex(llm_index)
            # Trigger on_llm_selected to populate model_name_combo
            self.main_controller.on_llm_selected()
            # Now set the specific model from the state
            model_index = self.model_name_combo.findText(state.selected_model_name)
            if model_index != -1:
                self.model_name_combo.setCurrentIndex(model_index)
            else:
                # If the saved model isn't in the list, add it and select it (or just select default)
                # For simplicity, let's just log a warning and keep the default selected
                print(f"Warning: Saved model '{state.selected_model_name}' not found in available models for {state.selected_llm}. Using default.")
                # The default is already selected by on_llm_selected
        else:
            # If LLM type itself is invalid, just use the default UI state
            self.main_controller.on_llm_selected()


        # 체크 상태 복원 (프로젝트 폴더가 유효할 때만 의미 있음)
        if self.current_project_folder and hasattr(self, 'checkable_proxy'):
            self.checkable_proxy.checked_files_dict.clear() # Ensure dict is clear before restoring
            items_to_check = []
            for fpath in state.checked_files:
                 if fpath.startswith(self.current_project_folder):
                     src_index = self.dir_model.index(fpath)
                     if src_index.isValid():
                         proxy_index = self.checkable_proxy.mapFromSource(src_index)
                         if proxy_index.isValid():
                             items_to_check.append(proxy_index)

            # Update internal dictionary first
            for proxy_index in items_to_check:
                fpath = self.checkable_proxy.get_file_path_from_index(proxy_index)
                if fpath:
                    self.checkable_proxy.checked_files_dict[fpath] = True

            # Emit dataChanged for all items at once for visual update
            for proxy_index in items_to_check:
                 self.checkable_proxy.dataChanged.emit(proxy_index, proxy_index, [Qt.CheckStateRole])


        self.file_tree_controller.load_gitignore_settings() # FileTreeController
        self.update_window_title(folder_name)
        self.resource_controller.update_buttons_label() # ResourceController
        # Gemini 파라미터는 config.yml에서 로드되므로 상태 파일과 무관
        self.load_gemini_settings_to_ui()

        self._initialized = True # 상태 로드 완료 후 플래그 설정
        self.status_bar.showMessage("State loaded successfully!")
        # 상태 로드 후 현재 탭 기준으로 문자 수 업데이트 및 토큰 레이블 리셋
        self.main_controller.update_char_count_for_active_tab()
        self.token_count_label.setText("토큰 계산: -") # 토큰 레이블 리셋


    def uncheck_all_files(self):
        """Unchecks all items in the file tree view."""
        if not hasattr(self, 'checkable_proxy'): return
        paths_to_uncheck = list(self.checkable_proxy.checked_files_dict.keys())
        self.checkable_proxy.checked_files_dict.clear() # Clear the dict first

        for fpath in paths_to_uncheck:
            src_index = self.dir_model.index(fpath)
            if src_index.isValid():
                proxy_index = self.checkable_proxy.mapFromSource(src_index)
                if proxy_index.isValid():
                    self.checkable_proxy.dataChanged.emit(proxy_index, proxy_index, [Qt.CheckStateRole])


    def _recursive_uncheck(self, proxy_index: QModelIndex):
        """Helper method to recursively uncheck items via setData."""
        if not proxy_index.isValid(): return
        current_state = self.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
        if current_state == Qt.Checked:
            self.checkable_proxy.setData(proxy_index, Qt.Unchecked, Qt.CheckStateRole)


    def create_tree_item(self, text, parent=None) -> QTreeWidgetItem:
        """Helper method to create items in the template/state tree."""
        if parent is None:
            item = QTreeWidgetItem([text])
            self.template_tree.addTopLevelItem(item)
        else:
            item = QTreeWidgetItem([text])
            parent.addChild(item)
        return item

    def add_new_custom_tab(self):
        """Adds a new custom tab to the build_tabs widget."""
        new_tab_name, ok = QInputDialog.getText(self, "새 탭 추가", "새 탭의 이름을 입력하세요:")
        if ok and new_tab_name and new_tab_name.strip():
            new_name = new_tab_name.strip()
            from ui.widgets.tab_manager import is_tab_deletable
            if not is_tab_deletable(new_name):
                 QMessageBox.warning(self, "경고", f"'{new_name}'은(는) 사용할 수 없는 탭 이름입니다.")
                 return
            # 중복 이름 확인
            for i in range(self.build_tabs.count()):
                if self.build_tabs.tabText(i) == new_name:
                    QMessageBox.warning(self, "경고", f"'{new_name}' 탭이 이미 존재합니다.")
                    return

            new_tab = CustomTextEdit()
            new_tab.setPlaceholderText(f"{new_name} 내용 입력...")
            plus_tab_index = -1
            for i in range(self.build_tabs.count()):
                if self.build_tabs.tabText(i) == "+":
                    plus_tab_index = i
                    break
            if plus_tab_index != -1:
                 self.build_tabs.insertTab(plus_tab_index, new_tab, new_name)
                 self.build_tabs.setCurrentIndex(plus_tab_index)
            else:
                 self.build_tabs.addTab(new_tab, new_name)
                 self.build_tabs.setCurrentIndex(self.build_tabs.count() - 1)
            # 새 탭 추가 시 문자 수 업데이트 및 토큰 리셋 연결
            new_tab.textChanged.connect(self.main_controller.update_char_count_for_active_tab)

        elif ok:
             QMessageBox.warning(self, "경고", "탭 이름은 비워둘 수 없습니다.")


    # --- LangGraph 관련 메서드 ---
    def send_prompt_to_gemini(self):
        """ "Gemini로 전송" 버튼 클릭 시 실행될 메서드 """
        if self.mode == "Meta Prompt Builder":
            QMessageBox.information(self, "정보", "Meta Prompt Builder 모드에서는 Gemini 전송 기능을 사용할 수 없습니다.")
            return

        if not hasattr(self, 'prompt_output_tab'):
            QMessageBox.warning(self, "오류", "프롬프트 출력 탭을 찾을 수 없습니다.")
            return

        prompt_text = self.prompt_output_tab.toPlainText()
        if not prompt_text.strip():
            QMessageBox.warning(self, "경고", "Gemini에 전송할 프롬프트 내용이 없습니다.")
            return

        # 버튼 비활성화 및 상태 메시지 업데이트
        if hasattr(self, 'send_to_gemini_btn'):
            self.send_to_gemini_btn.setEnabled(False)
        self.status_bar.showMessage("Gemini API 호출 중...")
        QApplication.processEvents() # UI 업데이트 강제

        # 이전 스레드가 실행 중이면 종료 시도 (선택적)
        if self.gemini_thread and self.gemini_thread.isRunning():
            print("Terminating previous Gemini thread...")
            self.gemini_thread.quit()
            self.gemini_thread.wait() # 종료 대기

        # 스레드 생성 및 시작
        self.gemini_thread = QThread()
        # graph_app과 prompt_text를 전달하여 Worker 생성
        self.gemini_worker = GeminiWorker(self.gemini_graph, prompt_text)
        self.gemini_worker.moveToThread(self.gemini_thread)

        # 시그널 연결
        self.gemini_thread.started.connect(self.gemini_worker.run)
        self.gemini_worker.finished.connect(self.handle_gemini_response)
        self.gemini_worker.error.connect(self.handle_gemini_error)
        # 스레드 종료 시 정리 (finished 시그널에 연결)
        self.gemini_worker.finished.connect(self.gemini_thread.quit)
        self.gemini_worker.finished.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)
        # 오류 발생 시에도 스레드 정리
        self.gemini_worker.error.connect(self.gemini_thread.quit)
        self.gemini_worker.error.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.cleanup_gemini_thread) # 최종 정리 슬롯 연결

        self.gemini_thread.start()

    def handle_gemini_response(self, xml_result: str, summary_result: str):
        """ Gemini 응답 처리 슬롯 """
        print("--- Handling Gemini Response ---")
        if hasattr(self, 'xml_input_tab'):
            self.xml_input_tab.setPlainText(xml_result)
            print(f"XML Output Length: {len(xml_result)}")
        if hasattr(self, 'summary_tab'): # 새로 추가한 Summary 탭
            self.summary_tab.setPlainText(summary_result)
            print(f"Summary Output Length: {len(summary_result)}")
            # Summary 탭으로 자동 전환 (선택적)
            self.build_tabs.setCurrentWidget(self.summary_tab)

        self.status_bar.showMessage("Gemini 응답 처리 완료.")
        if hasattr(self, 'send_to_gemini_btn'):
            self.send_to_gemini_btn.setEnabled(True) # 버튼 다시 활성화

    def handle_gemini_error(self, error_msg: str):
        """ Gemini 오류 처리 슬롯 """
        print(f"--- Handling Gemini Error: {error_msg} ---")
        QMessageBox.critical(self, "Gemini API 오류", f"오류 발생:\n{error_msg}")
        self.status_bar.showMessage("Gemini API 호출 오류.")
        if hasattr(self, 'send_to_gemini_btn'):
            self.send_to_gemini_btn.setEnabled(True) # 버튼 다시 활성화

    def cleanup_gemini_thread(self):
        """Gemini 스레드 및 워커 객체 정리"""
        print("--- Cleaning up Gemini thread and worker ---")
        self.gemini_thread = None
        self.gemini_worker = None

    # --- Gemini 파라미터 관리 메서드 ---
    def load_gemini_settings_to_ui(self):
        """Loads Gemini parameters from config.yml to the status bar widgets."""
        if not self._initialized: return # 초기화 중에는 실행 방지
        settings = self.config_service.get_settings()
        # 블록 시그널로 무한 루프 방지
        self.gemini_temp_edit.blockSignals(True)
        self.gemini_thinking_checkbox.blockSignals(True)
        self.gemini_budget_edit.blockSignals(True)
        self.gemini_search_checkbox.blockSignals(True)

        self.gemini_temp_edit.setText(str(settings.gemini_temperature))
        self.gemini_thinking_checkbox.setChecked(settings.gemini_enable_thinking)
        self.gemini_budget_edit.setText(str(settings.gemini_thinking_budget))
        self.gemini_search_checkbox.setChecked(settings.gemini_enable_search)

        self.gemini_temp_edit.blockSignals(False)
        self.gemini_thinking_checkbox.blockSignals(False)
        self.gemini_budget_edit.blockSignals(False)
        self.gemini_search_checkbox.blockSignals(False)

        # Gemini 선택 시에만 파라미터 위젯 보이도록 설정
        is_gemini_selected = (self.llm_combo.currentText() == "Gemini")
        if hasattr(self, 'gemini_param_widget'):
            self.gemini_param_widget.setVisible(is_gemini_selected)

    def save_gemini_settings(self):
        """Saves Gemini parameters from status bar widgets to config.yml."""
        if not self._initialized or self._is_saving_gemini_settings: return # 초기화 중 또는 저장 중에는 실행 방지

        self._is_saving_gemini_settings = True # 저장 시작 플래그
        try:
            # UI 값 읽기 및 유효성 검사
            try:
                temp_str = self.gemini_temp_edit.text().strip()
                temperature = float(temp_str) if temp_str else 0.0 # 빈 문자열이면 기본값 0.0
                if not (0.0 <= temperature <= 2.0):
                    raise ValueError("Temperature must be between 0.0 and 2.0")
            except ValueError as e:
                print(f"Invalid temperature value: {e}")
                # 유효하지 않으면 이전 값으로 복원 (선택적)
                # self.load_gemini_settings_to_ui()
                self._is_saving_gemini_settings = False
                return

            enable_thinking = self.gemini_thinking_checkbox.isChecked()

            try:
                budget_str = self.gemini_budget_edit.text().strip()
                thinking_budget = int(budget_str) if budget_str else 0 # 빈 문자열이면 기본값 0
                if thinking_budget < 0:
                    raise ValueError("Thinking budget must be non-negative")
            except ValueError as e:
                print(f"Invalid thinking budget value: {e}")
                # self.load_gemini_settings_to_ui()
                self._is_saving_gemini_settings = False
                return

            enable_search = self.gemini_search_checkbox.isChecked()

            # 업데이트할 데이터
            update_data = {
                "gemini_temperature": temperature,
                "gemini_enable_thinking": enable_thinking,
                "gemini_thinking_budget": thinking_budget,
                "gemini_enable_search": enable_search,
            }

            # ConfigService를 통해 업데이트 및 저장
            self.config_service.update_settings(**update_data)
            print(f"Gemini settings saved: {update_data}")
            # self.status_bar.showMessage("Gemini settings saved.", 2000) # 짧은 메시지 표시 (선택적)

        except Exception as e:
            print(f"Error saving Gemini settings: {e}")
            QMessageBox.warning(self, "오류", f"Gemini 설정 저장 중 오류 발생: {e}")
        finally:
            self._is_saving_gemini_settings = False # 저장 완료 플래그 해제


    # --- Event Handlers ---

    def on_copy_shortcut(self):
        """Handles Ctrl+C shortcut, copies if prompt output tab is active."""
        current_widget = self.build_tabs.currentWidget()
        if isinstance(current_widget, CustomTextEdit): # 현재 위젯이 텍스트 편집기인지 확인
            if current_widget.textCursor().hasSelection():
                current_widget.copy()
            elif current_widget == self.prompt_output_tab or \
                 (hasattr(self, 'final_prompt_tab') and current_widget == self.final_prompt_tab):
                self.prompt_controller.copy_to_clipboard() # PromptController의 복사 메서드 사용


    def on_tree_view_context_menu(self, position):
        """Handles context menu requests on the file tree view."""
        index = self.tree_view.indexAt(position)
        if not index.isValid(): return

        file_path = self.checkable_proxy.get_file_path_from_index(index)
        if not file_path: return

        menu = QMenu()
        rename_action = menu.addAction("이름 변경")
        delete_action = menu.addAction("삭제")
        action = menu.exec_(self.tree_view.viewport().mapToGlobal(position))

        if action == rename_action:
            self.file_tree_controller.rename_item(file_path)
        elif action == delete_action:
            self.file_tree_controller.delete_item(file_path)

    def on_tree_view_item_clicked(self, index: QModelIndex):
        """Handles item clicks in the tree view to toggle check state."""
        if not index.isValid() or index.column() != 0:
            return

        # CheckableProxyModel의 setData를 호출하여 체크 상태 토글
        current_state = self.checkable_proxy.data(index, Qt.CheckStateRole)
        new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
        # setData 호출 시 재귀 방지 플래그(_is_setting_data)가 있으므로 직접 호출 가능
        self.checkable_proxy.setData(index, new_state, Qt.CheckStateRole)

    # def on_selection_changed_handler(self, selected: QItemSelection, deselected: QItemSelection):
    #     """Handles selection changes in the file tree view to toggle check state."""
    #     # This handler is likely no longer needed as clicking toggles the check state directly.
    #     pass
