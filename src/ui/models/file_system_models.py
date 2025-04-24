import os
import fnmatch
from PyQt5.QtCore import QSortFilterProxyModel, Qt, QModelIndex
from PyQt5.QtWidgets import QFileSystemModel, QTreeView
from typing import Callable, Optional, Set

# TODO: FilesystemService를 주입받아 필터링 로직 위임 고려

class FilteredFileSystemModel(QFileSystemModel):
    """
    Custom file system model that fetches all children recursively upon setting root path.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.config = config # 제거됨. 설정은 외부(Controller/Service)에서 관리

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
                # Check if we can fetch more for the child directory
                if self.canFetchMore(child_index):
                     self._fetch_all_recursively(child_index)


class CheckableProxyModel(QSortFilterProxyModel):
    """
    Proxy model that provides checkable items and filters based on ignore patterns.
    """
    def __init__(self, fs_model: FilteredFileSystemModel, project_folder_getter: Callable[[], Optional[str]], tree_view: QTreeView, parent=None):
        super().__init__(parent)
        self.fs_model = fs_model
        self.project_folder_getter = project_folder_getter
        self.tree_view = tree_view
        self.checked_files_dict = {} # {file_path: bool}
        self._ignore_patterns: Set[str] = set() # .gitignore 패턴 저장

    def set_ignore_patterns(self, patterns: Set[str]):
        """Sets the ignore patterns used for filtering."""
        self._ignore_patterns = patterns
        # 패턴 변경 시 필터 무효화 필요
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
            return True # 프로젝트 루트 외부는 항상 표시

        # 프로젝트 루트 자체는 숨기지 않음
        if file_path == project_root:
            return True

        # FilesystemService의 should_ignore 사용하도록 리팩토링 필요
        # 임시: 직접 필터링 로직 수행
        is_dir = self.sourceModel().isDir(source_index)
        if self._should_ignore_local(file_path, project_root, self._ignore_patterns, is_dir):
            return False # 무시해야 하면 숨김

        return True # 필터링되지 않으면 표시

    def _should_ignore_local(self, file_path: str, project_root: str, ignore_patterns: Set[str], is_dir: bool) -> bool:
        """Internal implementation of ignore logic (to be replaced by FilesystemService)."""
        file_name = os.path.basename(file_path)
        try:
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
        except ValueError:
            return False # 상대 경로 계산 불가 시 무시 안 함

        for pattern in ignore_patterns:
            is_dir_pattern = pattern.endswith('/')
            cleaned_pattern = pattern.rstrip('/')

            if is_dir_pattern and not is_dir: continue

            # 1. 파일 이름 매칭
            if fnmatch.fnmatch(file_name, cleaned_pattern):
                if is_dir_pattern and is_dir: return True
                elif not is_dir_pattern: return True

            # 2. 상대 경로 매칭
            match_path = relative_path + '/' if is_dir else relative_path
            if fnmatch.fnmatch(match_path, pattern): return True
            if '/' in pattern and not is_dir_pattern:
                 if fnmatch.fnmatch(relative_path, pattern): return True

        return False

    def data(self, index, role=Qt.DisplayRole):
        """Returns data for the item, including check state."""
        if index.column() == 0 and role == Qt.CheckStateRole:
            file_path = self.get_file_path_from_index(index)
            # 체크 상태 반환 (dict에 없으면 Unchecked)
            return Qt.Checked if self.checked_files_dict.get(file_path, False) else Qt.Unchecked
        return super().data(index, role)

    def flags(self, index):
        """Returns item flags, adding ItemIsUserCheckable."""
        flags = super().flags(index)
        if index.column() == 0:
            flags |= Qt.ItemIsUserCheckable
        return flags

    def setData(self, index, value, role=Qt.EditRole):
        """Sets data for the item, handling check state changes."""
        if index.column() == 0 and role == Qt.CheckStateRole:
            file_path = self.get_file_path_from_index(index)
            if file_path:
                is_checked = (value == Qt.Checked)
                # 체크 상태 업데이트 (내부 dict)
                self.checked_files_dict[file_path] = is_checked
                # 뷰 갱신을 위해 dataChanged 시그널 발생
                self.dataChanged.emit(index, index, [Qt.CheckStateRole])

                src_index = self.mapToSource(index)
                # 폴더인 경우 하위 항목 처리 및 트리 확장
                if src_index.isValid() and self.fs_model.isDir(src_index):
                    # 하위 항목 로드 보장 (setData 호출 전에 ensure_loaded 호출 필요할 수 있음)
                    self.ensure_loaded(src_index)
                    # 하위 항목 체크 상태 동기화 및 시그널 발생
                    self.check_all_children(src_index, is_checked)
                    # 트리 확장 (체크 시) / 축소 (체크 해제 시 - 선택적)
                    if is_checked:
                        self.expand_index_recursively(index)
                    # else:
                    #     self.tree_view.collapse(index) # 체크 해제 시 축소 (선택적)
                return True
        return super().setData(index, value, role)

    def ensure_loaded(self, parent_index: QModelIndex):
        """Ensures all children under the parent index are loaded."""
        # FilteredFileSystemModel의 _fetch_all_recursively 호출
        if parent_index.isValid() and hasattr(self.fs_model, '_fetch_all_recursively'):
            self.fs_model._fetch_all_recursively(parent_index)

    def check_all_children(self, parent_src_index: QModelIndex, checked: bool):
        """Recursively updates check state for all visible children."""
        row_count = self.fs_model.rowCount(parent_src_index)
        for row in range(row_count):
            child_src_index = self.fs_model.index(row, 0, parent_src_index)
            child_proxy_index = self.mapFromSource(child_src_index)

            # 프록시 인덱스가 유효한지 (필터링되지 않았는지) 확인
            if not child_proxy_index.isValid():
                continue

            file_path = self.fs_model.filePath(child_src_index)

            # 체크 상태 업데이트 (내부 dict)
            self.checked_files_dict[file_path] = checked

            # 뷰 갱신을 위해 dataChanged 시그널 발생
            self.dataChanged.emit(child_proxy_index, child_proxy_index, [Qt.CheckStateRole])

            # 하위 폴더 재귀 호출
            if self.fs_model.isDir(child_src_index):
                # ensure_loaded는 setData에서 이미 호출되었으므로 여기서 재귀 호출
                self.check_all_children(child_src_index, checked)


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
        return [path for path, checked in self.checked_files_dict.items() if checked]

    def get_checked_files(self) -> list[str]:
        """Returns a list of checked paths that correspond to actual files."""
        # 필터링 상태와 관계없이 dict 기반 + 파일 여부 확인
        return [path for path, checked in self.checked_files_dict.items() if checked and os.path.isfile(path)]
