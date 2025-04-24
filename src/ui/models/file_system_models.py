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
        self._is_setting_data = False # 재귀적 setData 호출 방지 플래그

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
        """Returns data for the item, including check state and file size."""
        if not index.isValid():
            return None

        if index.column() == 0:
            if role == Qt.CheckStateRole:
                file_path = self.get_file_path_from_index(index)
                # 체크 상태 반환 (dict에 없으면 Unchecked)
                return Qt.Checked if self.checked_files_dict.get(file_path, False) else Qt.Unchecked
            elif role == Qt.DisplayRole:
                # 기본 파일/폴더 이름 가져오기
                base_name = super().data(index, role)
                # 소스 모델 인덱스 가져오기
                src_index = self.mapToSource(index)
                if src_index.isValid() and not self.fs_model.isDir(src_index):
                    # 파일인 경우 크기 가져오기 시도
                    file_path = self.fs_model.filePath(src_index)
                    try:
                        size = os.path.getsize(file_path)
                        # 이름 뒤에 크기 추가 (예: "myfile.txt (1,234 bytes)")
                        return f"{base_name} ({size:,} bytes)"
                    except OSError:
                        # 크기를 가져올 수 없는 경우 (예: 권한 문제)
                        return f"{base_name} (size error)"
                # 폴더거나 기본 역할이 아니면 기본 이름 반환
                return base_name

        # 다른 컬럼이나 역할은 기본 동작 따름
        return super().data(index, role)

    def flags(self, index):
        """Returns item flags, adding ItemIsUserCheckable."""
        flags = super().flags(index)
        if index.column() == 0:
            # Ensure the item is enabled to be checkable and selectable
            flags |= Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
        return flags

    def setData(self, index: QModelIndex, value: any, role: int = Qt.EditRole) -> bool:
        """Sets data for the item, handling check state changes, including multi-select and folder recursion."""
        if self._is_setting_data: # 재귀 호출 방지
            # print(f"setData blocked by flag for index: {self.get_file_path_from_index(index)}")
            return False
        if index.column() != 0 or role != Qt.CheckStateRole:
            return super().setData(index, value, role)

        # print(f"setData called for index: {self.get_file_path_from_index(index)}, value: {value}")
        self._is_setting_data = True # 플래그 설정
        try:
            selection_model = self.tree_view.selectionModel()
            # QItemSelectionModel.selectedIndexes() returns a list of QModelIndex
            selected_indexes = [idx for idx in selection_model.selectedIndexes() if idx.column() == 0]
            is_multi_select = len(selected_indexes) > 1
            clicked_is_selected = index in selected_indexes

            target_indexes_to_process = []
            # If multiple items are selected AND the clicked item is one of them, process all selected items.
            if is_multi_select and clicked_is_selected:
                target_indexes_to_process = selected_indexes
                # print(f"Multi-select detected. Processing {len(target_indexes_to_process)} items.")
            # Otherwise, just process the clicked item.
            else:
                target_indexes_to_process = [index]
                # print(f"Single-select or non-selected click. Processing 1 item.")

            new_check_state = value # The desired state (Qt.Checked or Qt.Unchecked)
            is_checked = (new_check_state == Qt.Checked)

            processed_paths = set() # Avoid processing the same path multiple times in one go
            items_to_update_signal = [] # Collect indices for batch signal emission

            for target_index in target_indexes_to_process:
                if not target_index.isValid(): continue

                file_path = self.get_file_path_from_index(target_index)
                if not file_path or file_path in processed_paths:
                    continue # Skip if path invalid or already processed

                processed_paths.add(file_path)
                # print(f"Processing target: {file_path}, desired state: {is_checked}")

                # Update the state for the current target index itself
                current_state_in_dict = self.checked_files_dict.get(file_path, False)
                needs_update = (is_checked != current_state_in_dict)

                if needs_update:
                    if is_checked:
                        self.checked_files_dict[file_path] = True
                    elif file_path in self.checked_files_dict:
                        del self.checked_files_dict[file_path]
                    items_to_update_signal.append(target_index)
                    # print(f"  State changed for {file_path}. Added to signal list.")

                # If it's a directory, recursively update children AND expand if checking
                src_index = self.mapToSource(target_index)
                if src_index.isValid() and self.fs_model.isDir(src_index):
                    # print(f"  {file_path} is a directory. Checking children...")
                    self.ensure_loaded(src_index) # Ensure children are loaded in the source model
                    child_indices_to_update = self.check_all_children(src_index, is_checked)
                    items_to_update_signal.extend(child_indices_to_update)
                    # print(f"  Finished checking children for {file_path}. Total signals needed: {len(items_to_update_signal)}")

                    # Expand the folder recursively if it was just checked
                    if is_checked and needs_update: # Only expand if state actually changed to checked
                        # print(f"  Recursively expanding folder: {file_path}")
                        self.expand_index_recursively(target_index) # Use recursive expand


            # Emit dataChanged signals only once after all processing is done
            if items_to_update_signal:
                # Use a set to ensure unique indices before emitting signals
                unique_indices_to_signal = {idx for idx in items_to_update_signal if idx.isValid()}
                # print(f"Emitting dataChanged for {len(unique_indices_to_signal)} unique indices.")
                for idx_to_signal in unique_indices_to_signal:
                    # print(f"  Emitting for: {self.get_file_path_from_index(idx_to_signal)}")
                    self.dataChanged.emit(idx_to_signal, idx_to_signal, [Qt.CheckStateRole])

            return True # Indicate success

        finally:
            # print("setData finished. Releasing flag.")
            self._is_setting_data = False # 플래그 해제


    def ensure_loaded(self, parent_src_index: QModelIndex):
        """Ensures all children under the parent source index are loaded."""
        if parent_src_index.isValid() and hasattr(self.fs_model, '_fetch_all_recursively'):
            # print(f"Ensuring children are loaded for source index: {self.fs_model.filePath(parent_src_index)}")
            self.fs_model._fetch_all_recursively(parent_src_index)

    def check_all_children(self, parent_src_index: QModelIndex, checked: bool) -> list[QModelIndex]:
        """
        Recursively updates check state for all visible children based on the 'checked' parameter.
        Updates the internal dictionary and returns a list of *proxy* indices whose state was changed.
        """
        indices_changed = []
        row_count = self.fs_model.rowCount(parent_src_index)
        # print(f"  check_all_children for {self.fs_model.filePath(parent_src_index)}, checked={checked}, children={row_count}")

        for row in range(row_count):
            child_src_index = self.fs_model.index(row, 0, parent_src_index)
            if not child_src_index.isValid(): continue

            # Map to proxy index *before* checking visibility or processing
            child_proxy_index = self.mapFromSource(child_src_index)

            # IMPORTANT: Only process children that are *visible* in the proxy model
            # This check implicitly handles the .gitignore filtering
            if not child_proxy_index.isValid():
                # print(f"    Skipping child (not visible in proxy): {self.fs_model.filePath(child_src_index)}")
                continue

            file_path = self.fs_model.filePath(child_src_index)
            # print(f"    Processing child: {file_path}")
            current_state_in_dict = self.checked_files_dict.get(file_path, False)
            needs_update = (checked != current_state_in_dict)

            if needs_update:
                if checked:
                    self.checked_files_dict[file_path] = True
                elif file_path in self.checked_files_dict:
                    del self.checked_files_dict[file_path]
                # Add the *proxy* index to the list of changed items
                indices_changed.append(child_proxy_index)
                # print(f"      State changed for {file_path}. Added proxy index to list.")

            # If it's a directory, recurse further
            if self.fs_model.isDir(child_src_index):
                self.ensure_loaded(child_src_index) # Ensure grandchildren are loaded
                grandchildren_indices = self.check_all_children(child_src_index, checked)
                indices_changed.extend(grandchildren_indices)

        # print(f"  Finished check_all_children for {self.fs_model.filePath(parent_src_index)}. Returning {len(indices_changed)} changed indices.")
        return indices_changed


    def expand_index_recursively(self, proxy_index: QModelIndex):
        """Recursively expands the given index and its children in the tree view."""
        if not proxy_index.isValid(): return

        self.tree_view.expand(proxy_index)
        child_count = self.rowCount(proxy_index)
        for row in range(child_count):
            child_proxy_idx = self.index(row, 0, proxy_index)
            if child_proxy_idx.isValid():
                 child_src_idx = self.mapToSource(child_proxy_idx)
                 # Only recurse into directories that are visible in the proxy
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
        # Return only keys where value is True, just in case False entries exist temporarily
        return [path for path, checked in self.checked_files_dict.items() if checked]


    def get_checked_files(self) -> list[str]:
        """Returns a list of checked paths that correspond to actual files."""
        return [path for path, checked in self.checked_files_dict.items() if checked and os.path.isfile(path)]

            