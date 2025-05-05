import os
import shutil
from typing import Optional, List, Set
from PyQt6.QtCore import Qt, QModelIndex, QItemSelection, QTimer # QTimer 추가
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox # PyQt5 -> PyQt6
import logging # 로깅 추가

# 서비스 및 모델 import
from core.services.filesystem_service import FilesystemService
from core.services.config_service import ConfigService
from core.services.directory_cache_service import DirectoryCacheService, CacheNode # Added

# MainWindow는 타입 힌트용으로만 사용
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow
    from ui.models.cached_file_system_model import CachedFileSystemModel # Added

logger = logging.getLogger(__name__) # 로거 설정

class FileTreeController:
    """
    Handles logic related to the file tree view, including interactions,
    filesystem operations, and gitignore handling.
    Uses DirectoryCacheService for data and updates.
    """
    def __init__(self, main_window: 'MainWindow', fs_service: FilesystemService, config_service: ConfigService, cache_service: DirectoryCacheService):
        self.mw = main_window
        self.fs_service = fs_service
        self.config_service = config_service
        self.cache_service = cache_service # Added
        self.gitignore_path: Optional[str] = None # .gitignore 파일 경로 저장
        self._is_refreshing = False # Prevent recursive refresh calls

        # Connect cache service signals
        self.cache_service.scan_progress.connect(self._update_scan_progress)
        self.cache_service.scan_error.connect(self._handle_scan_error)
        # cache_updated signal is connected in main_window to update the model

    def _update_scan_progress(self, message: str):
        """Updates the status bar with scan progress."""
        self.mw.status_bar.showMessage(f"Scanning: {message}")

    def _handle_scan_error(self, error_msg: str):
        """Handles scan errors reported by the cache service."""
        QMessageBox.warning(self.mw, "Scan Error", f"Error scanning project folder:\n{error_msg}")
        self.mw.status_bar.showMessage(f"Scan failed: {error_msg}")
        # Reset tree view if scan fails?
        self.reset_file_tree()

    def select_project_folder(self):
        """Opens a dialog to select the project folder and triggers a background scan."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 프로젝트 폴더 선택이 필요 없습니다.")
            return

        start_dir = self.mw.current_project_folder if self.mw.current_project_folder else os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self.mw, "프로젝트 폴더 선택", start_dir)

        if folder:
            logger.info(f"Project folder selected: {folder}")
            # Stop previous scan/monitoring if any
            self.cache_service.stop_scan()
            self.cache_service.stop_monitoring()

            # Reset UI state related to the old project
            self.mw.reset_state() # Resets internal state, clears tree model via signal

            # Update UI labels and internal state
            self.mw.current_project_folder = folder
            folder_name = os.path.basename(folder)
            self.mw.project_folder_label.setText(f"현재 프로젝트 폴더: {folder}")
            self.mw.update_window_title(folder_name)

            # Load gitignore patterns for the new folder
            ignore_patterns = self.load_gitignore_settings()

            # Start background scan via DirectoryCacheService
            self.mw.status_bar.showMessage(f"Starting scan for {folder}...")
            self.cache_service.start_scan(folder, ignore_patterns)

            # Tree view will be populated when the scan finishes and cache_updated signal is emitted
            # No need to set root index here directly

            # Trigger state change signal
            self.mw.state_changed_signal.emit()

    def load_gitignore_settings(self) -> Set[str]:
        """Loads .gitignore patterns and updates the filter model and cache service."""
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
                    logger.info(f"Loaded {len(gitignore_lines)} patterns from {self.gitignore_path}")
                except Exception as e:
                    QMessageBox.warning(self.mw, "Error", f".gitignore 로드 중 오류: {str(e)}")
                    logger.error(f"Error loading .gitignore: {e}", exc_info=True)

        # config.yml의 excluded_dirs 추가
        patterns.update(settings.excluded_dirs)
        logger.info(f"Total ignore patterns (including defaults and excluded_dirs): {len(patterns)}")

        # Update ignore patterns in the cache service (for watchdog)
        self.cache_service.update_ignore_patterns(patterns)

        # Update patterns in the proxy model (for UI filtering)
        if hasattr(self.mw, 'checkable_proxy'):
             self.mw.checkable_proxy.set_ignore_patterns(patterns)
             # Filter invalidation happens inside set_ignore_patterns
             # No need to call refresh_tree here, cache update will handle UI refresh

        return patterns # Return patterns for initial scan

    def save_gitignore_settings(self):
        """Saves the content of the gitignore editor to the .gitignore file. (Moved to SettingsDialog)"""
        QMessageBox.information(self.mw, "정보", ".gitignore 저장은 환경 설정 메뉴에서 수행해주세요.")

    def reset_gitignore_and_filter(self):
        """Resets gitignore filter to defaults based on config.yml."""
        logger.info("Resetting gitignore filter to defaults.")
        default_settings = self.config_service.get_settings()
        default_patterns = set(default_settings.default_ignore_list).union(default_settings.excluded_dirs)

        # Update cache service and proxy model
        self.cache_service.update_ignore_patterns(default_patterns)
        if hasattr(self.mw, 'checkable_proxy'):
             self.mw.checkable_proxy.set_ignore_patterns(default_patterns)
             # Trigger a refresh/rescan if patterns changed significantly?
             # For now, rely on cache_updated signal if filtering changes visibility
             # Consider adding a manual refresh button if needed.
             # self.refresh_tree() # Avoid manual refresh, let model update handle it

    def reset_file_tree(self):
        """Resets the file tree view by clearing the model."""
        logger.info("Resetting file tree view.")
        if hasattr(self.mw, 'cached_model'):
            self.mw.cached_model.clear() # Clear the QStandardItemModel
            logger.info("Cached file system model cleared.")
        # Check state dictionary is cleared in MainWindow's reset_state


    def generate_directory_tree_structure(self):
        """Generates the directory tree structure based on checked items from the cache."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 디렉토리 트리 기능이 필요 없습니다.")
            return False

        if not self.mw.current_project_folder:
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

        logger.info(f"Generating directory tree for {len(all_checked_paths)} checked items.")
        try:
            # Use FilesystemService, which doesn't rely on the cache directly
            # It operates on the list of checked paths provided.
            tree_string = self.fs_service.get_directory_tree(all_checked_paths, self.mw.current_project_folder)
        except Exception as e:
             QMessageBox.critical(self.mw, "오류", f"디렉토리 트리 생성 중 오류 발생: {e}")
             logger.error(f"Error generating directory tree: {e}", exc_info=True)
             return False

        if hasattr(self.mw, "dir_structure_tab"):
            self.mw.dir_structure_tab.setText(tree_string)
            self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
        self.mw.status_bar.showMessage("File tree generated!")
        self.mw.tree_generated = True # MainWindow 상태 업데이트
        logger.info("Directory tree generation successful.")
        return True

    def rename_item(self, file_path):
        """Renames a file or directory. Watchdog should handle the update."""
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

            logger.info(f"Renaming item: '{file_path}' -> '{new_path}'")
            try:
                os.rename(file_path, new_path)
                self.mw.status_bar.showMessage(f"'{old_name}' -> '{new_name_stripped}' 이름 변경 완료. 파일 시스템 감시자가 업데이트합니다.")
                # Update check state dictionary if the renamed item was checked
                if hasattr(self.mw, 'checkable_proxy'):
                    if file_path in self.mw.checkable_proxy.checked_files_dict:
                        is_checked = self.mw.checkable_proxy.checked_files_dict.pop(file_path)
                        self.mw.checkable_proxy.checked_files_dict[new_path] = is_checked
                        logger.debug(f"Updated checked_files_dict for renamed item: {new_path}")
                # No need to manually refresh tree, watchdog + cache service should handle it.
                # self.refresh_tree() # REMOVED
                self.mw.state_changed_signal.emit() # 파일 구조 변경 시 상태 변경
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"이름 변경 중 오류 발생: {str(e)}")
                logger.error(f"Error renaming item: {e}", exc_info=True)
        elif ok:
             QMessageBox.warning(self.mw, "Error", "새 이름은 비워둘 수 없습니다.")

    def delete_item(self, file_path):
        """Deletes a file or directory. Watchdog should handle the update."""
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
            logger.info(f"Deleting item: {file_path}")
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                self.mw.status_bar.showMessage(f"'{item_name}' 삭제 완료. 파일 시스템 감시자가 업데이트합니다.")
                # Remove the deleted item and any children from the check state dictionary
                if hasattr(self.mw, 'checkable_proxy'):
                    paths_to_remove = [p for p in self.mw.checkable_proxy.checked_files_dict if p == file_path or p.startswith(file_path + os.sep)]
                    removed_count = 0
                    for p in paths_to_remove:
                        if p in self.mw.checkable_proxy.checked_files_dict:
                            del self.mw.checkable_proxy.checked_files_dict[p]
                            removed_count += 1
                    logger.debug(f"Removed {removed_count} items from checked_files_dict after deletion.")
                # No need to manually refresh tree, watchdog + cache service should handle it.
                # self.refresh_tree() # REMOVED
                self.mw.state_changed_signal.emit() # 파일 구조 변경 시 상태 변경
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"삭제 중 오류 발생: {str(e)}")
                logger.error(f"Error deleting item: {e}", exc_info=True)

    def refresh_tree(self):
        """Manually triggers a rescan of the project folder."""
        if self._is_refreshing:
            logger.debug("Refresh already in progress, skipping.")
            return
        if not self.mw.current_project_folder:
            logger.warning("Cannot refresh tree: Project folder not set.")
            return

        logger.info("Manually refreshing file tree by triggering rescan...")
        self._is_refreshing = True
        self.mw.status_bar.showMessage(f"Refreshing project folder: {self.mw.current_project_folder}...")
        # Get current ignore patterns
        ignore_patterns = self.load_gitignore_settings()
        # Start scan via cache service
        self.cache_service.start_scan(self.mw.current_project_folder, ignore_patterns)
        # Use a timer to reset the flag after a short delay, preventing rapid clicks
        QTimer.singleShot(2000, self._reset_refresh_flag) # Reset flag after 2 seconds

    def _reset_refresh_flag(self):
        self._is_refreshing = False
        logger.debug("Refresh flag reset.")


    def on_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: List[int]):
        """Handles updates when data in the CheckableProxyModel changes (e.g., check state)."""
        # This method might still be useful for reacting to check state changes,
        # but file size calculation is removed.
        if Qt.ItemDataRole.CheckStateRole in roles and hasattr(self.mw, 'checkable_proxy'): # Qt.CheckStateRole -> Qt.ItemDataRole.CheckStateRole
            # Get checked files (optimized version without os.path.getsize)
            checked_files = self.mw.checkable_proxy.get_checked_files() # This now uses cache/model info
            self.mw.selected_files_data = []
            # Store paths only, size is not relevant here anymore
            for fpath in checked_files:
                self.mw.selected_files_data.append((fpath, 0)) # Store path with dummy size 0

            self.mw.status_bar.showMessage(f"{len(checked_files)} files selected.") # Update status bar without size
            # Token calculation is triggered by button clicks
            # State change signal is emitted directly from the proxy model connection
            # logger.debug("Check state changed, state_changed_signal emitted.") # Signal emitted via connect_signals

