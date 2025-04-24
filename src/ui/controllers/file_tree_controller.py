import os
import shutil
from typing import Optional, List, Set
from PyQt5.QtCore import Qt, QModelIndex, QItemSelection
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox

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
            self.mw.reset_state() # MainWindow 상태 초기화
            self.mw.current_project_folder = folder
            folder_name = os.path.basename(folder)
            self.mw.project_folder_label.setText(f"현재 프로젝트 폴더: {folder}")

            self.load_gitignore_settings() # gitignore 로드 및 필터 설정

            if hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
                idx = self.mw.dir_model.setRootPathFiltered(folder)
                root_proxy_index = self.mw.checkable_proxy.mapFromSource(idx)
                self.mw.tree_view.setRootIndex(root_proxy_index)
                self.mw.status_bar.showMessage(f"Project Folder: {folder}")

                if root_proxy_index.isValid():
                    self.mw.checkable_proxy.setData(root_proxy_index, Qt.Checked, Qt.CheckStateRole)

            self.mw.update_window_title(folder_name)

    def load_gitignore_settings(self):
        """Loads .gitignore patterns and updates the UI and filter model."""
        self.gitignore_path = None
        patterns: Set[str] = set()
        lines_for_ui: List[str] = []

        settings = self.config_service.get_settings()
        patterns.update(settings.default_ignore_list)
        lines_for_ui.extend(sorted(list(settings.default_ignore_list))) # 기본값 먼저 표시

        if self.mw.current_project_folder:
            possible_path = os.path.join(self.mw.current_project_folder, ".gitignore")
            if os.path.isfile(possible_path):
                self.gitignore_path = possible_path
                try:
                    # FilesystemService를 사용하여 .gitignore 로드 (선택적)
                    # gitignore_patterns = self.fs_service.load_gitignore_patterns(self.mw.current_project_folder)
                    # patterns.update(gitignore_patterns) # 서비스가 반환한 패턴 사용

                    # 또는 직접 로드
                    with open(self.gitignore_path, 'r', encoding='utf-8') as f:
                        lines = f.read().splitlines()
                    gitignore_lines = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]
                    patterns.update(gitignore_lines)
                    lines_for_ui = gitignore_lines # .gitignore 있으면 UI 내용 교체

                except Exception as e:
                    QMessageBox.warning(self.mw, "Error", f".gitignore 로드 중 오류: {str(e)}")

        # config.yml의 excluded_dirs 추가
        patterns.update(settings.excluded_dirs)

        # UI 업데이트
        self.mw.gitignore_edit.setText("\n".join(lines_for_ui))

        # 필터 모델에 패턴 설정
        if hasattr(self.mw, 'checkable_proxy'):
             self.mw.checkable_proxy.set_ignore_patterns(patterns)

    def save_gitignore_settings(self):
        """Saves the content of the gitignore editor to the .gitignore file."""
        if not self.mw.current_project_folder:
            QMessageBox.warning(self.mw, "Error", "프로젝트 폴더가 설정되지 않았습니다.")
            return

        lines = self.mw.gitignore_edit.toPlainText().splitlines()
        lines_to_save = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]
        target_path = os.path.join(self.mw.current_project_folder, ".gitignore")

        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines_to_save) + "\n")
            QMessageBox.information(self.mw, "Info", f".gitignore가 저장되었습니다: {target_path}")
            self.load_gitignore_settings() # 저장 후 다시 로드
        except Exception as e:
            QMessageBox.warning(self.mw, "Error", f".gitignore 저장 중 오류: {str(e)}")

    def reset_gitignore_and_filter(self):
        """Resets gitignore settings and filter to defaults."""
        default_settings = self.config_service.get_settings()
        default_patterns = set(default_settings.default_ignore_list).union(default_settings.excluded_dirs)
        self.mw.gitignore_edit.setText("\n".join(sorted(list(default_patterns))))
        if hasattr(self.mw, 'checkable_proxy'):
             self.mw.checkable_proxy.set_ignore_patterns(default_patterns)

    def reset_file_tree(self):
        """Resets the file tree view to the home directory."""
        home_path = os.path.expanduser("~")
        if hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
            idx = self.mw.dir_model.setRootPathFiltered(home_path)
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))
            self.mw.checkable_proxy.checked_files_dict.clear() # 체크 상태 초기화
            self.mw.tree_view.collapseAll()

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
                # TODO: FilesystemService에 rename 기능 추가 고려
                os.rename(file_path, new_path)
                self.mw.status_bar.showMessage(f"'{old_name}' -> '{new_name_stripped}' 이름 변경 완료")
                # 체크 상태 업데이트
                if hasattr(self.mw, 'checkable_proxy'):
                    if file_path in self.mw.checkable_proxy.checked_files_dict:
                        is_checked = self.mw.checkable_proxy.checked_files_dict.pop(file_path)
                        self.mw.checkable_proxy.checked_files_dict[new_path] = is_checked
                self.refresh_tree()
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
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # TODO: FilesystemService에 delete 기능 추가 고려
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                self.mw.status_bar.showMessage(f"'{item_name}' 삭제 완료")
                # 체크 상태 업데이트
                if hasattr(self.mw, 'checkable_proxy'):
                    # 삭제된 경로 및 하위 경로의 체크 상태 제거
                    paths_to_remove = [p for p in self.mw.checkable_proxy.checked_files_dict if p == file_path or p.startswith(file_path + os.sep)]
                    for p in paths_to_remove:
                        if p in self.mw.checkable_proxy.checked_files_dict:
                            del self.mw.checkable_proxy.checked_files_dict[p]
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"삭제 중 오류 발생: {str(e)}")

    def refresh_tree(self):
        """Refreshes the file explorer tree view."""
        if self.mw.current_project_folder and hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
            # TODO: 확장 상태 저장/복원 로직 추가
            idx = self.mw.dir_model.setRootPathFiltered(self.mw.current_project_folder)
            # 필터 갱신은 setRootPathFiltered 또는 set_ignore_patterns 호출 시 처리됨
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))
            self.mw.status_bar.showMessage("파일 트리 새로고침 완료.")

    def handle_selection_change(self, selected: QItemSelection, deselected: QItemSelection):
        """Handles selection changes in the file tree view to toggle check state."""
        indexes = selected.indexes()
        if not indexes: return

        proxy_index = indexes[0]
        if proxy_index.column() != 0: return

        # ProxyModel의 setData 호출하여 체크 상태 토글
        if hasattr(self.mw, 'checkable_proxy'):
            current_state = self.mw.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
            new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
            self.mw.checkable_proxy.setData(proxy_index, new_state, Qt.CheckStateRole)

    def on_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: List[int]):
        """Handles updates when data in the CheckableProxyModel changes."""
        # 체크 상태 변경 시 관련 UI 업데이트 (예: 선택된 파일 정보 업데이트)
        if Qt.CheckStateRole in roles and hasattr(self.mw, 'checkable_proxy'):
            # 선택된 파일 목록 및 크기 정보 업데이트 (선택적)
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
            # 상태바 등에 정보 표시 (선택적)
            # self.mw.status_bar.showMessage(f"{len(checked_files)} files selected, Total size: {total_size:,} bytes")
            pass # 현재는 특별한 동작 없음
