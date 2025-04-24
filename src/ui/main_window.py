import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QTabWidget, QAction,
    QStatusBar, QPushButton, QLabel, QCheckBox,
    QAbstractItemView, QMenuBar, QSplitter, QStyleFactory, QApplication, QMenu, QTreeWidget, QTreeWidgetItem, QComboBox, QFileDialog, QInputDialog, QMessageBox, QFrame
)
from PyQt5.QtGui import QKeySequence, QIcon, QCursor, QMouseEvent, QFont, QDesktopServices
from PyQt5.QtCore import Qt, QSize, QStandardPaths, QModelIndex, QItemSelection, QUrl # QItemSelection, QUrl 추가

# 변경된 경로에서 import
from core.pydantic_models.app_state import AppState # 상태 타입 힌트용
from core.services.config_service import ConfigService
from core.services.state_service import StateService
from core.services.template_service import TemplateService
from core.services.prompt_service import PromptService
from core.services.xml_service import XmlService
from core.services.filesystem_service import FilesystemService

from ui.models.file_system_models import FilteredFileSystemModel, CheckableProxyModel
# 컨트롤러 import
from ui.controllers.main_controller import MainController
from ui.controllers.resource_controller import ResourceController
from ui.controllers.prompt_controller import PromptController
from ui.controllers.xml_controller import XmlController
from ui.controllers.file_tree_controller import FileTreeController
from ui.controllers.system_prompt_controller import apply_default_system_prompt, select_default_system_prompt

# UI 및 시그널 설정 함수 import
from .main_window_setup_ui import create_menu_bar, create_widgets, create_layout, create_status_bar
from .main_window_setup_signals import connect_signals

from ui.widgets.custom_text_edit import CustomTextEdit
from ui.widgets.custom_tab_bar import CustomTabBar # CustomTabBar 임포트
from utils.helpers import get_resource_path


class MainWindow(QMainWindow):
    def __init__(self, mode="Code Enhancer Prompt Builder"):
        super().__init__()
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

        # --- 서비스 인스턴스 생성 ---
        # 서비스 인스턴스는 MainWindow 내에서 생성 및 관리
        self.config_service = ConfigService()
        self.state_service = StateService()
        self.template_service = TemplateService()
        self.prompt_service = PromptService()
        self.xml_service = XmlService()
        self.fs_service = FilesystemService(self.config_service)

        # --- UI 구성 요소 생성 (외부 함수 호출) ---
        create_menu_bar(self)
        create_widgets(self)
        create_layout(self)
        create_status_bar(self)

        # --- 컨트롤러 생성 및 연결 ---
        # 각 컨트롤러에 MainWindow와 필요한 서비스 주입
        self.main_controller = MainController(self)
        self.resource_controller = ResourceController(self, self.template_service, self.state_service)
        self.prompt_controller = PromptController(self, self.prompt_service)
        self.xml_controller = XmlController(self, self.xml_service)
        self.file_tree_controller = FileTreeController(self, self.fs_service, self.config_service)

        # --- 시그널 연결 (외부 함수 호출) ---
        connect_signals(self)

        # --- 초기화 작업 ---
        self.resource_controller.load_templates_list() # 리소스 목록 로드
        self._apply_initial_settings() # 기본 설정 적용 (기본 프롬프트 등)

        # 상태바 메시지 및 창 크기 설정
        self.status_bar.showMessage("Ready")
        initial_width = 1200
        initial_height = 800
        self.resize(initial_width, initial_height)

        # 초기 스플리터 크기 설정 (왼쪽:오른쪽 비율 조정)
        # 예: 왼쪽을 오른쪽보다 약 1.8배 크게 (전체 너비 기준 비율 계산)
        # left_width = int(initial_width * (1.8 / (1.8 + 1))) # 약 642
        # right_width = initial_width - left_width # 약 558
        # 더 명확하게: 왼쪽 540, 오른쪽 660 (1200 기준) -> 비율 약 1:1.22
        # 왼쪽 700, 오른쪽 500 -> 비율 1.4:1
        # 왼쪽 600, 오른쪽 600 -> 비율 1:1
        # 왼쪽 770, 오른쪽 430 -> 비율 약 1.8:1
        left_width = int(initial_width * 1.8 / 2.8) # 약 771
        right_width = initial_width - left_width # 약 429
        self.center_splitter.setSizes([left_width, right_width])

        self.build_tabs.setCurrentIndex(1) # 사용자 탭을 기본으로 표시

        # 초기/리셋 시 파일 탐색기 비우기
        self.file_tree_controller.reset_file_tree()


    # UI 생성 및 시그널 연결 함수는 외부 파일로 이동됨
    # _create_menu_bar, _create_widgets, _create_layout, _create_status_bar, _connect_signals

    def _apply_initial_settings(self):
        """Applies initial settings like default system prompt."""
        apply_default_system_prompt(self)

        if self.mode == "Meta Prompt Builder":
            meta_prompt_path_relative = os.path.join("prompts", "system", "META_Prompt.md")
            try:
                meta_prompt_path = get_resource_path(meta_prompt_path_relative)
                if os.path.exists(meta_prompt_path):
                    with open(meta_prompt_path, "r", encoding="utf-8") as f:
                        self.system_tab.setText(f.read())
            except Exception as e:
                print(f"Error loading default META prompt: {e}")

        self.file_tree_controller.load_gitignore_settings() # FileTreeController
        self.resource_controller.update_buttons_label() # ResourceController

    def _restart_with_mode(self, new_mode: str):
        """Restarts the application with the specified mode."""
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


    # --- Public Methods (Controller에서 호출) ---

    def reset_state(self):
        """Resets internal state variables of the MainWindow."""
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


    def update_window_title(self, folder_name: Optional[str] = None):
        """Updates the window title based on the project folder."""
        if folder_name:
            self.setWindowTitle(f"{folder_name} - {self.base_title}")
        else:
            self.setWindowTitle(self.base_title)

    def get_current_state(self) -> AppState:
        """Gathers the current UI state and returns it as an AppState model."""
        checked_paths = self.checkable_proxy.get_all_checked_paths() if hasattr(self, 'checkable_proxy') else []
        state_data = {
            "mode": self.mode,
            "project_folder": self.current_project_folder,
            "system_prompt": self.system_tab.toPlainText(),
            "user_prompt": self.user_tab.toPlainText(),
            "checked_files": checked_paths
        }
        try:
            app_state = AppState(**state_data)
            return app_state
        except Exception as e:
             print(f"Error creating AppState model: {e}")
             return AppState(mode=self.mode)

    def set_current_state(self, state: AppState):
        """Sets the UI state based on the provided AppState model."""
        if self.mode != state.mode:
            print(f"Mode mismatch during state load. Current: {self.mode}, Loaded: {state.mode}. Restarting...")
            self._restart_with_mode(state.mode)
            return # 재시작 후 새 인스턴스에서 상태 로드됨

        self.reset_state() # UI 및 내부 상태 초기화 (트리 포함)

        folder_name = None
        if state.project_folder and os.path.isdir(state.project_folder):
            self.current_project_folder = state.project_folder
            folder_name = os.path.basename(state.project_folder)
            self.project_folder_label.setText(f"현재 프로젝트 폴더: {state.project_folder}")
            if hasattr(self, 'dir_model') and hasattr(self, 'checkable_proxy'):
                idx = self.mw.dir_model.setRootPathFiltered(state.project_folder)
                root_proxy_index = self.mw.checkable_proxy.mapFromSource(idx)
                self.mw.tree_view.setRootIndex(root_proxy_index) # 유효한 인덱스 설정
                # 루트 폴더 자동 체크 (선택적)
                if root_proxy_index.isValid():
                    self.mw.checkable_proxy.setData(root_proxy_index, Qt.Checked, Qt.CheckStateRole)

            self.status_bar.showMessage(f"Project Folder: {state.project_folder}")
        else:
             # 프로젝트 폴더가 유효하지 않으면 라벨 업데이트 및 트리 리셋 (reset_state에서 이미 처리됨)
             self.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
             # self.file_tree_controller.reset_file_tree() # reset_state에서 호출됨

        self.system_tab.setText(state.system_prompt)
        self.user_tab.setText(state.user_prompt)

        # 체크 상태 복원 (프로젝트 폴더가 유효할 때만 의미 있음)
        if self.current_project_folder and hasattr(self, 'checkable_proxy'):
            # self.uncheck_all_files() # reset_state에서 이미 처리됨
            for fpath in state.checked_files:
                 # 경로가 현재 프로젝트 폴더 하위에 있는지 확인 (선택적이지만 안전)
                 if fpath.startswith(self.current_project_folder):
                     src_index = self.dir_model.index(fpath)
                     if src_index.isValid():
                         proxy_index = self.checkable_proxy.mapFromSource(src_index)
                         if proxy_index.isValid():
                             # setData를 호출하여 체크 상태 설정 및 하위 항목 처리 유발
                             self.checkable_proxy.setData(proxy_index, Qt.Checked, Qt.CheckStateRole)

        self.file_tree_controller.load_gitignore_settings() # FileTreeController
        self.update_window_title(folder_name)
        self.resource_controller.update_buttons_label() # ResourceController
        self.status_bar.showMessage("State loaded successfully!")


    def uncheck_all_files(self):
        """Unchecks all items in the file tree view."""
        if not hasattr(self, 'checkable_proxy'): return
        self.checkable_proxy.checked_files_dict.clear()
        root_proxy_index = self.tree_view.rootIndex()
        if root_proxy_index.isValid():
            self._recursive_uncheck(root_proxy_index)


    def _recursive_uncheck(self, proxy_index: QModelIndex):
        """Helper method to recursively uncheck items via setData."""
        if not proxy_index.isValid(): return
        current_state = self.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
        if current_state == Qt.Checked:
            # setData 호출 시 하위 항목 처리 및 시그널 발생
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
            # 새 탭 추가 시 토큰 계산 연결
            new_tab.textChanged.connect(self.main_controller.update_active_tab_counts)

        elif ok:
             QMessageBox.warning(self, "경고", "탭 이름은 비워둘 수 없습니다.")


    # --- Event Handlers ---

    def on_copy_shortcut(self):
        """Handles Ctrl+C shortcut, copies if prompt output tab is active."""
        current_widget = self.build_tabs.currentWidget()
        if isinstance(current_widget, CustomTextEdit): # 현재 위젯이 텍스트 편집기인지 확인
            # 선택된 텍스트가 있으면 그것을 복사
            if current_widget.textCursor().hasSelection():
                current_widget.copy()
            # 선택된 텍스트가 없고, 특정 탭(프롬프트 출력 등)이면 전체 내용 복사
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


    def on_selection_changed_handler(self, selected: QItemSelection, deselected: QItemSelection):
        """Handles selection changes in the file tree view to toggle check state."""
        self.file_tree_controller.handle_selection_change(selected, deselected)
