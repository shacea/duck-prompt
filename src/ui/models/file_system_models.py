import os
import fnmatch
from PyQt5.QtCore import QSortFilterProxyModel, Qt, QModelIndex
from PyQt5.QtWidgets import QFileSystemModel, QTreeView
from typing import Callable, Optional, Set
from core.services.filesystem_service import FilesystemService

class FilteredFileSystemModel(QFileSystemModel):
    """
    Custom file system model that fetches all children recursively upon setting root path.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def setRootPathFiltered(self, path: str) -> QModelIndex:
        """Sets the root path and immediately fetches all children."""
        root_index = super().setRootPath(path)
        if root_index.isValid():
            self._fetch_all_recursively(root_index)
        return root_index

    def _fetch_all_recursively(self, parent_index: QModelIndex) -> None:
        """Recursively fetches all items under the parent index."""
        if not parent_index.isValid():
            return

        # Fetch immediate children first
        while self.canFetchMore(parent_index):
            self.fetchMore(parent_index)

        # Recursively fetch for child directories
        row_count = self.rowCount(parent_index)
        for row in range(row_count):
            child_index = self.index(row, 0, parent_index)
            if child_index.isValid() and self.isDir(child_index):
                self._fetch_all_recursively(child_index)


class CheckableProxyModel(QSortFilterProxyModel):
    """
    Proxy model that provides checkable items and filters based on ignore patterns.
    Handles recursive checking for folders and multi-selection checking.
    """
    def __init__(self, fs_model: FilteredFileSystemModel, project_folder_getter: Callable[[], Optional[str]], fs_service: FilesystemService, tree_view: QTreeView, parent=None):
        super().__init__(parent)
        self.fs_model = fs_model
        self.project_folder_getter = project_folder_getter
        self.fs_service = fs_service # FilesystemService 저장
        self.tree_view = tree_view
        self.checked_files_dict = {} # {file_path: bool} - Stores the check state
        self._ignore_patterns: Set[str] = set() # .gitignore 패턴 저장

    def set_ignore_patterns(self, patterns: Set[str]):
        """Sets the ignore patterns used for filtering."""
        if self._ignore_patterns != patterns:
            self._ignore_patterns = patterns
            # 패턴 변경 시 필터 무효화
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Determines if a row should be shown based on ignore patterns."""
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        if not source_index.isValid():
            return False

        file_path = self.sourceModel().filePath(source_index)
        project_root = self.project_folder_getter()

        # 프로젝트 루트가 설정되지 않았거나, 현재 파일이 프로젝트 루트 밖에 있으면 필터링 안 함
        if not project_root or not file_path.startswith(project_root):
            return True # 프로젝트 루트 외부는 항상 표시 (루트 포함)

        # 프로젝트 루트 자체는 숨기지 않음
        if file_path == project_root:
            return True

        # FilesystemService의 should_ignore 사용
        is_dir = self.sourceModel().isDir(source_index)
        if self.fs_service.should_ignore(file_path, project_root, self._ignore_patterns, is_dir):
            # 무시 대상이면, 체크 상태도 해제 (선택적)
            if file_path in self.checked_files_dict:
                del self.checked_files_dict[file_path]
            return False # 무시해야 하면 숨김

        return True # 필터링되지 않으면 표시

    def data(self, index, role=Qt.DisplayRole):
        """Returns data for the item, including check state."""
        if index.column() == 0 and role == Qt.CheckStateRole:
            file_path = self.get_file_path_from_index(index)
            # 체크 상태 반환 (dict에 없으면 Unchecked)
            return Qt.Checked if self.checked_files_dict.get(file_path, False) else Qt.Unchecked
        # 파일 이름 표시 (기본값)
        return super().data(index, role)

    def flags(self, index):
        """Returns item flags, adding ItemIsUserCheckable."""
        flags = super().flags(index)
        if index.column() == 0:
            # Ensure the item is enabled to be checkable
            flags |= Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        return flags

    def setData(self, index: QModelIndex, value: any, role: int = Qt.EditRole) -> bool:
        """Sets data for the item, handling check state changes, including multi-select and folder recursion."""
        if index.column() == 0 and role == Qt.CheckStateRole:
            selection_model = self.tree_view.selectionModel()
            selected_indexes = [idx for idx in selection_model.selectedIndexes() if idx.column() == 0]
            is_multi_select = len(selected_indexes) > 1
            clicked_is_selected = index in selected_indexes

            target_indexes = []
            if is_multi_select and clicked_is_selected:
                # If multi-select and the clicked item is part of the selection, target all selected items
                target_indexes = selected_indexes
                print(f"Multi-select check triggered for {len(target_indexes)} items.")
            else:
                # Otherwise, target only the clicked item
                target_indexes = [index]
                # print(f"Single item check triggered for: {self.get_file_path_from_index(index)}")


            new_check_state = value # The desired state (Qt.Checked or Qt.Unchecked)
            is_checked = (new_check_state == Qt.Checked)

            # Use a set to avoid processing the same path multiple times if selected via different indices
            processed_paths = set()
            items_to_update_signal = [] # Collect indices for batch signal emission

            for target_index in target_indexes:
                if not target_index.isValid(): continue

                file_path = self.get_file_path_from_index(target_index)
                if file_path and file_path not in processed_paths:
                    processed_paths.add(file_path)

                    # Update internal dict
                    current_state_in_dict = self.checked_files_dict.get(file_path, False)
                    needs_update = (is_checked != current_state_in_dict)

                    if needs_update:
                        # print(f"Updating check state for {file_path} to {is_checked}")
                        if is_checked:
                            self.checked_files_dict[file_path] = True
                        elif file_path in self.checked_files_dict:
                            del self.checked_files_dict[file_path]

                        # Add to list for signal emission
                        items_to_update_signal.append(target_index)

                        # Handle children if it's a directory
                        src_index = self.mapToSource(target_index)
                        if src_index.isValid() and self.fs_model.isDir(src_index):
                            # print(f"Processing children for directory: {file_path}")
                            self.ensure_loaded(src_index)
                            # Pass the new state and collect child indices needing signal update
                            child_indices_to_update = self.check_all_children(src_index, is_checked)
                            items_to_update_signal.extend(child_indices_to_update)
                            # Expand only when checking, not unchecking (optional)
                            if is_checked:
                                self.expand_index_recursively(target_index)
                    # else:
                        # print(f"Skipping update for {file_path}, state already {is_checked}")


            # Emit dataChanged for all affected items at once
            if items_to_update_signal:
                # We need to emit for ranges, but Qt expects topLeft and bottomRight.
                # For simplicity, emit for each item individually.
                # For performance with huge selections, optimizing this might be needed.
                # print(f"Emitting dataChanged for {len(items_to_update_signal)} items.")
                for idx_to_signal in items_to_update_signal:
                     if idx_to_signal.isValid(): # Check validity again before emitting
                        self.dataChanged.emit(idx_to_signal, idx_to_signal, [Qt.CheckStateRole])

            return True # Indicate success

        return super().setData(index, value, role)


    def ensure_loaded(self, parent_src_index: QModelIndex):
        """Ensures all children under the parent source index are loaded."""
        # FilteredFileSystemModel의 _fetch_all_recursively 호출
        if parent_src_index.isValid() and hasattr(self.fs_model, '_fetch_all_recursively'):
            # print(f"Ensuring loaded for: {self.fs_model.filePath(parent_src_index)}")
            self.fs_model._fetch_all_recursively(parent_src_index)

    def check_all_children(self, parent_src_index: QModelIndex, checked: bool) -> list[QModelIndex]:
        """
        Recursively updates check state for all visible children based on the 'checked' parameter.
        Returns a list of proxy indices whose state was changed and need a signal update.
        """
        indices_changed = []
        row_count = self.fs_model.rowCount(parent_src_index)
        # print(f"Checking children of {self.fs_model.filePath(parent_src_index)} ({row_count} children), target state: {checked}")

        for row in range(row_count):
            child_src_index = self.fs_model.index(row, 0, parent_src_index)
            if not child_src_index.isValid(): continue

            child_proxy_index = self.mapFromSource(child_src_index)

            # Only process visible children (those not filtered out)
            if not child_proxy_index.isValid():
                # print(f"  Skipping filtered child: {self.fs_model.filePath(child_src_index)}")
                continue

            file_path = self.fs_model.filePath(child_src_index)
            current_state_in_dict = self.checked_files_dict.get(file_path, False)
            needs_update = (checked != current_state_in_dict)

            if needs_update:
                # print(f"  Updating child: {file_path} to {checked}")
                # Update check state in the dictionary
                if checked:
                    self.checked_files_dict[file_path] = True
                elif file_path in self.checked_files_dict:
                    del self.checked_files_dict[file_path]

                # Add this child's proxy index to the list for signal emission
                indices_changed.append(child_proxy_index)

                # Recursively process grandchildren if this child is a directory
                if self.fs_model.isDir(child_src_index):
                    # Ensure grandchildren are loaded before recursion
                    self.ensure_loaded(child_src_index)
                    grandchildren_indices = self.check_all_children(child_src_index, checked)
                    indices_changed.extend(grandchildren_indices)
            # else:
                # print(f"  Skipping child update (already correct state): {file_path}")


        return indices_changed


    def expand_index_recursively(self, proxy_index: QModelIndex):
        """Recursively expands the given index and its children in the tree view."""
        if not proxy_index.isValid(): return

        self.tree_view.expand(proxy_index)
        child_count = self.rowCount(proxy_index) # 프록시 모델의 rowCount 사용
        for row in range(child_count):
            child_proxy_idx = self.index(row, 0, proxy_index) # 프록시 모델의 index 사용
            if child_proxy_idx.isValid():
                 # 하위 항목이 폴더인지 확인 (소스 모델 기준)
                 child_src_idx = self.mapToSource(child_proxy_idx)
                 if self.fs_model.isDir(child_src_idx):
                      self.expand_index_recursively(child_proxy_idx)


    def get_file_path_from_index(self, proxy_index) -> Optional[str]:
        """Gets the file path from a proxy index."""
        src_index = self.mapToSource(proxy_index)
        if src_index.isValid():
            return self.fs_model.filePath(src_index)
        return None

    def get_all_checked_paths(self) -> list[str]:
        """Returns a list of all paths currently marked as checked."""
        # 필터링 상태와 관계없이 dict에 저장된 모든 체크된 경로 반환
        return list(self.checked_files_dict.keys()) # 체크된 것만 저장하므로 value 검사 불필요

    def get_checked_files(self) -> list[str]:
        """Returns a list of checked paths that correspond to actual files."""
        # 필터링 상태와 관계없이 dict 기반 + 파일 여부 확인
        return [path for path, checked in self.checked_files_dict.items() if checked and os.path.isfile(path)]
