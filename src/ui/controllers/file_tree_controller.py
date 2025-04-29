
import os
import shutil
from typing import Optional, List, Set
from PyQt6.QtCore import Qt, QModelIndex, QItemSelection # PyQt5 -> PyQt6
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox # PyQt5 -> PyQt6

# 서비스 및 모델 import
from core.services.filesystem_service import FilesystemService
from core.services.config_service import ConfigService

# MainWindow는 타입 힌트용으로만 사용
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow

class FileTreeController:
    """
    Handles logic related to the file tree view, including interactions,
    filesystem operations, and gitignore handling.
    """
    def __init__(self, main_window: 'MainWindow', fs_service: FilesystemService, config_service: ConfigService):
        self.mw = main_window
        self.fs_service = fs_service
        self.config_service = config_service
        self.gitignore_path: Optional[str] = None # .gitignore 파일 경로 저장

    def select_project_folder(self):
        """Opens a dialog to select the project folder and updates the UI."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 프로젝트 폴더 선택이 필요 없습니다.")
            return

        start_dir = self.mw.current_project_folder if self.mw.current_project_folder else os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self.mw, "프로젝트 폴더 선택", start_dir)

        if folder:
            # 폴더 선택 시 상태 초기화 (UI 및 내부 변수)
            self.mw.reset_state() # MainWindow 상태 초기화 (트리 리셋 포함)
            self.mw.current_project_folder = folder
            folder_name = os.path.basename(folder)
            self.mw.project_folder_label.setText(f"현재 프로젝트 폴더: {folder}")

            self.load_gitignore_settings() # gitignore 로드 및 필터 설정

            # 모델에 루트 경로 설정 및 트리뷰 업데이트
            if hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
                idx = self.mw.dir_model.setRootPathFiltered(folder)
                root_proxy_index = self.mw.checkable_proxy.mapFromSource(idx)
                self.mw.tree_view.setRootIndex(root_proxy_index) # 유효한 루트 인덱스 설정
                self.mw.status_bar.showMessage(f"Project Folder: {folder}")

                # 루트 폴더 자동 체크 (선택적)
                if root_proxy_index.isValid():
                    # Check the root folder by default
                    self.mw.checkable_proxy.setData(root_proxy_index, Qt.CheckState.Checked, Qt.ItemDataRole.CheckStateRole) # Qt.Checked -> Qt.CheckState.Checked, Qt.CheckStateRole -> Qt.ItemDataRole.CheckStateRole

            self.mw.update_window_title(folder_name)
            # 프로젝트 폴더 변경 시 상태 변경 시그널 발생
            self.mw.state_changed_signal.emit()

    def load_gitignore_settings(self):
        """Loads .gitignore patterns and updates the filter model."""
        self.gitignore_path = None
        patterns: Set[str] = set()

        settings = self.config_service.get_settings()
        patterns.update(settings.default_ignore_list)

        if self.mw.current_project_folder:
            possible_path = os.path.join(self.mw.current_project_folder, ".gitignore")
            if os.path.isfile(possible_path):
                self.gitignore_path = possible_path
                try:
                    with open(self.gitignore_path, 'r', encoding='utf-8') as f:
                        lines = f.read().splitlines()
                    gitignore_lines = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]
                    patterns.update(gitignore_lines)
                except Exception as e:
                    QMessageBox.warning(self.mw, "Error", f".gitignore 로드 중 오류: {str(e)}")

        # config.yml의 excluded_dirs 추가
        patterns.update(settings.excluded_dirs)

        # 필터 모델에 패턴 설정
        if hasattr(self.mw, 'checkable_proxy'):
             self.mw.checkable_proxy.set_ignore_patterns(patterns)
             # 필터가 변경되었으므로 트리 뷰를 새로 고쳐야 할 수 있음
             self.refresh_tree() # 필터 적용 후 트리 새로고침

    def save_gitignore_settings(self):
        """Saves the content of the gitignore editor to the .gitignore file. (Moved to SettingsDialog)"""
        QMessageBox.information(self.mw, "정보", ".gitignore 저장은 환경 설정 메뉴에서 수행해주세요.")

    def reset_gitignore_and_filter(self):
        """Resets gitignore filter to defaults based on config.yml."""
        default_settings = self.config_service.get_settings()
        default_patterns = set(default_settings.default_ignore_list).union(default_settings.excluded_dirs)
        if hasattr(self.mw, 'checkable_proxy'):
             self.mw.checkable_proxy.set_ignore_patterns(default_patterns)
             self.refresh_tree() # 필터 리셋 후 트리 새로고침

    def reset_file_tree(self):
        """Resets the file tree view to an empty state."""
        if hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
            idx = self.mw.dir_model.setRootPath("")
            self.mw.tree_view.setRootIndex(QModelIndex())
            self.mw.checkable_proxy.checked_files_dict.clear()
            self.mw.tree_view.collapseAll()
            print("File tree reset to empty state.")


    def generate_directory_tree_structure(self):
        """Generates the directory tree structure based on checked items."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 디렉토리 트리 기능이 필요 없습니다.")
            return False

        if not self.mw.current_project_folder or not os.path.isdir(self.mw.current_project_folder):
            QMessageBox.warning(self.mw, "경고", "프로젝트 폴더를 먼저 선택해주세요.")
            return False

        all_checked_paths = self.mw.checkable_proxy.get_all_checked_paths() if hasattr(self.mw, 'checkable_proxy') else []
        if not all_checked_paths:
            message = "선택된 파일이나 폴더가 없습니다."
            if hasattr(self.mw, "dir_structure_tab"):
                self.mw.dir_structure_tab.setText(message)
                self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
            self.mw.status_bar.showMessage("파일 트리를 생성할 항목이 없습니다!")
            return False

        try:
            tree_string = self.fs_service.get_directory_tree(all_checked_paths, self.mw.current_project_folder)
        except Exception as e:
             QMessageBox.critical(self.mw, "오류", f"디렉토리 트리 생성 중 오류 발생: {e}")
             return False

        if hasattr(self.mw, "dir_structure_tab"):
            self.mw.dir_structure_tab.setText(tree_string)
            self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
        self.mw.status_bar.showMessage("File tree generated!")
        self.mw.tree_generated = True # MainWindow 상태 업데이트
        return True

    def rename_item(self, file_path):
        """Renames a file or directory."""
        if self.mw.mode == "Meta Prompt Builder": return
        if not os.path.exists(file_path):
            QMessageBox.warning(self.mw, "Error", "파일 또는 디렉토리가 존재하지 않습니다.")
            return

        base_dir = os.path.dirname(file_path)
        old_name = os.path.basename(file_path)
        new_name, ok = QInputDialog.getText(self.mw, "이름 변경", f"'{old_name}'의 새 이름을 입력하세요:", text=old_name)

        if ok and new_name and new_name.strip():
            new_name_stripped = new_name.strip()
            if new_name_stripped == old_name: return
            new_path = os.path.join(base_dir, new_name_stripped)
            if os.path.exists(new_path):
                 QMessageBox.warning(self.mw, "Error", f"'{new_name_stripped}' 이름이 이미 존재합니다.")
                 return

            try:
                os.rename(file_path, new_path)
                self.mw.status_bar.showMessage(f"'{old_name}' -> '{new_name_stripped}' 이름 변경 완료")
                if hasattr(self.mw, 'checkable_proxy'):
                    if file_path in self.mw.checkable_proxy.checked_files_dict:
                        is_checked = self.mw.checkable_proxy.checked_files_dict.pop(file_path)
                        self.mw.checkable_proxy.checked_files_dict[new_path] = is_checked
                self.refresh_tree()
                self.mw.state_changed_signal.emit() # 파일 구조 변경 시 상태 변경
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"이름 변경 중 오류 발생: {str(e)}")
        elif ok:
             QMessageBox.warning(self.mw, "Error", "새 이름은 비워둘 수 없습니다.")

    def delete_item(self, file_path):
        """Deletes a file or directory."""
        if self.mw.mode == "Meta Prompt Builder": return
        if not os.path.exists(file_path):
            QMessageBox.warning(self.mw, "Error", "파일 또는 디렉토리가 존재하지 않습니다.")
            return

        item_name = os.path.basename(file_path)
        item_type = "폴더" if os.path.isdir(file_path) else "파일"
        reply = QMessageBox.question(self.mw, "삭제 확인",
                                     f"정말로 '{item_name}' {item_type}을(를) 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) # QMessageBox.Yes/No -> QMessageBox.StandardButton.Yes/No

        if reply == QMessageBox.StandardButton.Yes: # QMessageBox.Yes -> QMessageBox.StandardButton.Yes
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                self.mw.status_bar.showMessage(f"'{item_name}' 삭제 완료")
                if hasattr(self.mw, 'checkable_proxy'):
                    paths_to_remove = [p for p in self.mw.checkable_proxy.checked_files_dict if p == file_path or p.startswith(file_path + os.sep)]
                    for p in paths_to_remove:
                        if p in self.mw.checkable_proxy.checked_files_dict:
                            del self.mw.checkable_proxy.checked_files_dict[p]
                self.refresh_tree()
                self.mw.state_changed_signal.emit() # 파일 구조 변경 시 상태 변경
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"삭제 중 오류 발생: {str(e)}")

    def refresh_tree(self):
        """Refreshes the file explorer tree view."""
        if self.mw.current_project_folder and hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
            self.mw.checkable_proxy.invalidateFilter()
            idx = self.mw.dir_model.setRootPathFiltered(self.mw.current_project_folder)
            root_proxy_index = self.mw.checkable_proxy.mapFromSource(idx)
            self.mw.tree_view.setRootIndex(root_proxy_index)
            self._reapply_check_states(root_proxy_index)
            self.mw.status_bar.showMessage("파일 트리 새로고침 완료.")


    def _reapply_check_states(self, parent_proxy_index: QModelIndex):
         """Recursively reapply check states based on the dictionary after a refresh."""
         if not parent_proxy_index.isValid(): return

         parent_path = self.mw.checkable_proxy.get_file_path_from_index(parent_proxy_index)
         if parent_path:
             is_checked = self.mw.checkable_proxy.checked_files_dict.get(parent_path, False)
             current_state = self.mw.checkable_proxy.data(parent_proxy_index, Qt.ItemDataRole.CheckStateRole) # Qt.CheckStateRole -> Qt.ItemDataRole.CheckStateRole
             target_state = Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked # Qt.Checked/Unchecked -> Qt.CheckState.Checked/Unchecked
             if current_state != target_state:
                 self.mw.checkable_proxy.setData(parent_proxy_index, target_state, Qt.ItemDataRole.CheckStateRole) # Qt.CheckStateRole -> Qt.ItemDataRole.CheckStateRole

         row_count = self.mw.checkable_proxy.rowCount(parent_proxy_index)
         for row in range(row_count):
             child_proxy_index = self.mw.checkable_proxy.index(row, 0, parent_proxy_index)
             if child_proxy_index.isValid():
                 self._reapply_check_states(child_proxy_index)


    def on_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: List[int]):
        """Handles updates when data in the CheckableProxyModel changes (e.g., check state)."""
        if Qt.ItemDataRole.CheckStateRole in roles and hasattr(self.mw, 'checkable_proxy'): # Qt.CheckStateRole -> Qt.ItemDataRole.CheckStateRole
            checked_files = self.mw.checkable_proxy.get_checked_files()
            self.mw.selected_files_data = []
            total_size = 0
            for fpath in checked_files:
                try:
                    size = os.path.getsize(fpath)
                    self.mw.selected_files_data.append((fpath, size))
                    total_size += size
                except Exception:
                    pass # 오류 무시
            self.mw.status_bar.showMessage(f"{len(checked_files)} files selected, Total size: {total_size:,} bytes")
            # 토큰 계산은 버튼 클릭 시에만 수행되도록 변경됨
            # self.mw.main_controller.update_char_count_for_active_tab() # Trigger update based on active tab
            # 파일 체크 상태 변경 시 상태 변경 시그널 발생 (자동 저장용) -> 시그널 연결 파일에서 처리

