
import os
import fnmatch
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QModelIndex
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QTreeView
from typing import Callable, Optional, Set, List, Dict, Any # List, Dict, Any 추가
from core.services.filesystem_service import FilesystemService
import logging

logger = logging.getLogger(__name__)

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
        self.fs_service = fs_service
        self.tree_view = tree_view
        self.checked_files_dict: Dict[str, bool] = {} # {file_path: bool} - Stores the check state
        self._ignore_patterns: Set[str] = set()
        self._is_setting_data = False # 재귀적 setData 호출 방지 플래그

    def set_ignore_patterns(self, patterns: Set[str]):
        """Sets the ignore patterns used for filtering."""
        if self._ignore_patterns != patterns:
            self._ignore_patterns = patterns
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Determines if a row should be shown based on ignore patterns."""
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        if not source_index.isValid():
            return False

        file_path = self.sourceModel().filePath(source_index)
        project_root = self.project_folder_getter()

        if not project_root or not file_path.startswith(project_root):
            return True

        if file_path == project_root:
            return True

        is_dir = self.sourceModel().isDir(source_index)
        if self.fs_service.should_ignore(file_path, project_root, self._ignore_patterns, is_dir):
            if file_path in self.checked_files_dict:
                # 필터링되어 숨겨지는 항목은 체크 상태 딕셔너리에서도 제거
                logger.debug(f"Removing filtered item from checked_files_dict: {file_path}")
                del self.checked_files_dict[file_path]
            return False

        return True

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Returns data for the item, including check state and file size."""
        if not index.isValid():
            return None

        if index.column() == 0:
            if role == Qt.ItemDataRole.CheckStateRole:
                file_path = self.get_file_path_from_index(index)
                # checked_files_dict에 경로가 존재하고 값이 True이면 Checked, 아니면 Unchecked 반환
                # (값이 False인 경우는 없지만 명확성을 위해 True 확인)
                is_checked = self.checked_files_dict.get(file_path, False)
                return Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked
            elif role == Qt.ItemDataRole.DisplayRole:
                base_name = super().data(index, role)
                src_index = self.mapToSource(index)
                if src_index.isValid() and not self.fs_model.isDir(src_index):
                    file_path = self.fs_model.filePath(src_index)
                    try:
                        size = os.path.getsize(file_path)
                        return f"{base_name} ({size:,} bytes)"
                    except OSError:
                        return f"{base_name} (size error)"
                return base_name

        return super().data(index, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Returns item flags, adding ItemIsUserCheckable."""
        flags = super().flags(index)
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable
        return flags

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """Sets data for the item, handling check state changes, including multi-select and folder recursion."""
        # 재귀 호출 방지 플래그 체크
        if self._is_setting_data:
            logger.debug(f"setData blocked by flag for index: {self.get_file_path_from_index(index)}")
            return False
        # 체크 상태 역할 및 0번 컬럼인지 확인
        if index.column() != 0 or role != Qt.ItemDataRole.CheckStateRole:
            return super().setData(index, value, role)

        file_path = self.get_file_path_from_index(index)
        if not file_path:
            logger.warning(f"setData failed: Could not get file path for index {index.row()},{index.column()}")
            return False

        logger.debug(f"▶ setData called: path={file_path}, role={role}, value={value}")
        self._is_setting_data = True # 플래그 설정
        try:
            # PyQt6에서는 value가 CheckState enum 값일 수 있음
            if isinstance(value, Qt.CheckState):
                new_check_state = value
            elif isinstance(value, int): # Fallback for integer
                new_check_state = Qt.CheckState(value)
            else:
                logger.warning(f"setData: Unexpected value type for CheckStateRole: {type(value)}")
                self._is_setting_data = False
                return False

            is_checked = (new_check_state == Qt.CheckState.Checked)
            current_state_in_dict = file_path in self.checked_files_dict

            # 상태가 실제로 변경되는 경우에만 처리
            if is_checked == current_state_in_dict:
                logger.debug(f"setData: No state change needed for {file_path}. Current: {current_state_in_dict}, New: {is_checked}")
                self._is_setting_data = False
                return True # 상태 변경 없어도 성공으로 처리

            logger.debug(f"setData processing state change for: {file_path}, New state: {is_checked}")

            # 상태 딕셔너리 업데이트
            if is_checked:
                self.checked_files_dict[file_path] = True
            elif file_path in self.checked_files_dict:
                # 체크 해제 시 딕셔너리에서 제거
                del self.checked_files_dict[file_path]
                # logger.info(f"  Item unchecked and removed from checked_files_dict: {file_path}") # 제거 로그 레벨 INFO -> DEBUG로 변경
                logger.debug(f"  Item unchecked and removed from checked_files_dict: {file_path}")

            # 변경된 인덱스 목록 초기화
            indices_to_signal = {index} # 자기 자신 포함

            # 폴더인 경우 하위 항목 처리
            src_index = self.mapToSource(index)
            if src_index.isValid() and self.fs_model.isDir(src_index):
                logger.debug(f"  {file_path} is a directory. Updating children...")
                self.ensure_loaded(src_index) # 하위 항목 로드 보장
                # update_children_state 호출하여 하위 항목 상태 업데이트 및 변경된 인덱스 받기
                changed_children_indices = self.update_children_state(src_index, is_checked)
                indices_to_signal.update(changed_children_indices) # 변경된 하위 인덱스 추가
                logger.debug(f"  Finished updating children for {file_path}. Total signals needed: {len(indices_to_signal)}")

                # 폴더가 체크되었을 때 확장 (선택적)
                if is_checked:
                    logger.debug(f"  Expanding checked folder: {file_path}")
                    self.expand_index_recursively(index)

            # dataChanged 시그널 발생 (변경된 모든 인덱스에 대해)
            logger.debug(f"Emitting dataChanged for {len(indices_to_signal)} indices.")
            for idx_to_signal in indices_to_signal:
                if idx_to_signal.isValid():
                    logger.debug(f"    Emitting for: {self.get_file_path_from_index(idx_to_signal)}")
                    # dataChanged 시그널 발생시켜 UI 업데이트
                    self.dataChanged.emit(idx_to_signal, idx_to_signal, [Qt.ItemDataRole.CheckStateRole])

            logger.debug(f"setData returning True for path: {file_path}")
            return True # 성공적으로 처리됨

        except Exception as e:
            logger.exception(f"Error in setData for path {file_path}: {e}")
            return False # 오류 발생 시 실패 반환
        finally:
            logger.debug("setData finished. Releasing flag.")
            self._is_setting_data = False # 플래그 해제

    def ensure_loaded(self, parent_src_index: QModelIndex):
        """Ensures all children under the parent source index are loaded."""
        if parent_src_index.isValid() and hasattr(self.fs_model, '_fetch_all_recursively'):
            self.fs_model._fetch_all_recursively(parent_src_index)

    def update_children_state(self, parent_src_index: QModelIndex, checked: bool) -> Set[QModelIndex]:
        """
        Recursively updates check state for all visible children based on the 'checked' parameter.
        Updates the internal dictionary and returns a set of *proxy* indices whose state was changed.
        """
        changed_indices = set()
        row_count = self.fs_model.rowCount(parent_src_index)
        parent_path = self.fs_model.filePath(parent_src_index)
        # logger.debug(f"    update_children_state for {parent_path}, checked={checked}, children={row_count}")

        for row in range(row_count):
            child_src_index = self.fs_model.index(row, 0, parent_src_index)
            if not child_src_index.isValid(): continue

            child_proxy_index = self.mapFromSource(child_src_index)
            # 필터링되어 보이지 않는 항목은 건너뜀
            if not child_proxy_index.isValid():
                # logger.debug(f"      Skipping filtered child: {self.fs_model.filePath(child_src_index)}")
                continue

            file_path = self.fs_model.filePath(child_src_index)
            current_state_in_dict = file_path in self.checked_files_dict
            needs_update = (checked != current_state_in_dict)

            if needs_update:
                if checked:
                    self.checked_files_dict[file_path] = True
                elif file_path in self.checked_files_dict:
                    # 체크 해제 시 딕셔너리에서 제거
                    del self.checked_files_dict[file_path]
                    # logger.info(f"      Child unchecked and removed from checked_files_dict: {file_path}") # 제거 로그 레벨 INFO -> DEBUG로 변경
                    logger.debug(f"      Child unchecked and removed from checked_files_dict: {file_path}")
                changed_indices.add(child_proxy_index) # 변경된 프록시 인덱스 추가
                # logger.debug(f"      Child state changed: {file_path}, Added proxy index.")

            # 하위 폴더 재귀 호출 (폴더인 경우에만)
            if self.fs_model.isDir(child_src_index):
                self.ensure_loaded(child_src_index) # 하위 항목 로드 보장
                grandchildren_indices = self.update_children_state(child_src_index, checked)
                changed_indices.update(grandchildren_indices) # 재귀적으로 변경된 인덱스 추가

        # logger.debug(f"    Finished update_children_state for {parent_path}. Returning {len(changed_indices)} changed indices.")
        return changed_indices


    def expand_index_recursively(self, proxy_index: QModelIndex):
        """Recursively expands the given index and its children in the tree view."""
        if not proxy_index.isValid(): return

        self.tree_view.expand(proxy_index)
        child_count = self.rowCount(proxy_index)
        for row in range(child_count):
            child_proxy_idx = self.index(row, 0, proxy_index)
            if child_proxy_idx.isValid():
                 child_src_idx = self.mapToSource(child_proxy_idx)
                 if self.fs_model.isDir(child_src_idx):
                      self.expand_index_recursively(child_proxy_idx)


    def get_file_path_from_index(self, proxy_index: QModelIndex) -> Optional[str]:
        """Gets the file path from a proxy index."""
        src_index = self.mapToSource(proxy_index)
        if src_index.isValid():
            # 절대 경로 반환
            return self.fs_model.filePath(src_index)
        return None

    def get_all_checked_paths(self) -> List[str]:
        """Returns a list of all paths currently marked as checked."""
        # checked_files_dict의 키 목록을 반환 (값은 항상 True)
        # logger.info(f"get_all_checked_paths called. Returning {len(self.checked_files_dict)} paths.") # 로그 레벨 INFO -> DEBUG로 변경
        logger.debug(f"get_all_checked_paths called. Returning {len(self.checked_files_dict)} paths.")
        return list(self.checked_files_dict.keys())


    def get_checked_files(self) -> List[str]:
        """Returns a list of checked paths that correspond to actual files."""
        # checked_files_dict의 키 중에서 실제 파일인 것만 반환
        checked_files = [path for path in self.checked_files_dict if os.path.isfile(path)]
        # logger.info(f"get_checked_files called. Returning {len(checked_files)} file paths.") # 로그 레벨 INFO -> DEBUG로 변경
        logger.debug(f"get_checked_files called. Returning {len(checked_files)} file paths.")
        return checked_files
