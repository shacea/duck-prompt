
import os
from PyQt5.QtCore import QSortFilterProxyModel, Qt, QModelIndex
from PyQt5.QtWidgets import QFileSystemModel, QTreeView

class FilteredFileSystemModel(QFileSystemModel):
    """
    폴더 선택 시 전체 하위 폴더 및 파일을 재귀적으로 메모리에 로드하기 위한 모델.
    """

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config

    def setRootPathFiltered(self, path: str) -> QModelIndex:
        root_index = super().setRootPath(path)
        # 전체 하위 경로를 즉시 로드
        self._fetch_all_recursively(root_index)
        return root_index

    def _fetch_all_recursively(self, parent_index: QModelIndex) -> None:
        """
        parent_index 이하 모든 폴더/파일을 fetchMore()하여 로드
        """
        if not parent_index.isValid():
            return

        while self.canFetchMore(parent_index):
            self.fetchMore(parent_index)

        row_count = self.rowCount(parent_index)
        for row in range(row_count):
            child_index = self.index(row, 0, parent_index)
            if self.isDir(child_index):
                self._fetch_all_recursively(child_index)


class CheckableProxyModel(QSortFilterProxyModel):
    """
    폴더/파일 체크 가능한 ProxyModel.
    폴더 체크 시 하위 폴더/파일도 자동 체크 + 자동 확장.
    """

    def __init__(self, fs_model: FilteredFileSystemModel, project_folder_getter, tree_view: QTreeView, parent=None):
        super().__init__(parent)
        self.fs_model = fs_model
        self.project_folder_getter = project_folder_getter
        self.tree_view = tree_view
        self.checked_files_dict = {}

    def data(self, index, role=Qt.DisplayRole):
        # 체크 상태 표시
        if index.column() == 0 and role == Qt.CheckStateRole:
            file_path = self.get_file_path_from_index(index)
            return Qt.Checked if self.checked_files_dict.get(file_path, False) else Qt.Unchecked
        return super().data(index, role)

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 0:
            flags |= Qt.ItemIsUserCheckable
        return flags

    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 0 and role == Qt.CheckStateRole:
            file_path = self.get_file_path_from_index(index)
            if file_path:
                is_checked = (value == Qt.Checked)
                self.checked_files_dict[file_path] = is_checked
                self.dataChanged.emit(index, index, [Qt.CheckStateRole])

                src_index = self.mapToSource(index)
                # 폴더면 하위 항목도 체크 처리 및 트리 자동 확장
                if src_index.isValid() and self.fs_model.isDir(src_index):
                    self.ensure_loaded(src_index)
                    self.check_all_children(src_index, is_checked)
                    self.expand_index_recursively(index)
                return True
        return super().setData(index, value, role)

    def ensure_loaded(self, parent_index: QModelIndex):
        """
        parent_index 하위 폴더/파일을 모두 로드
        """
        if parent_index.isValid() and hasattr(self.fs_model, '_fetch_all_recursively'):
            self.fs_model._fetch_all_recursively(parent_index)

    def check_all_children(self, parent_index: QModelIndex, checked: bool):
        """
        parent_index 하위 모든 폴더/파일 체크 상태를 갱신
        """
        row_count = self.fs_model.rowCount(parent_index)
        for row in range(row_count):
            child_index = self.fs_model.index(row, 0, parent_index)
            child_proxy_index = self.mapFromSource(child_index)
            file_path = self.fs_model.filePath(child_index)

            # 체크 상태 업데이트
            self.checked_files_dict[file_path] = checked
            # ★ 중요: super().setData() 호출로 실제 체크 상태 갱신
            super().setData(child_proxy_index, Qt.Checked if checked else Qt.Unchecked, Qt.CheckStateRole)

            # 하위 폴더 재귀
            if self.fs_model.isDir(child_index):
                self.ensure_loaded(child_index)
                self.check_all_children(child_index, checked)

    def expand_index_recursively(self, proxy_index: QModelIndex):
        """
        주어진 인덱스와 모든 자식을 트리에서 확장
        """
        self.tree_view.expand(proxy_index)
        child_count = self.rowCount(proxy_index)
        for row in range(child_count):
            child_idx = self.index(row, 0, proxy_index)
            if child_idx.isValid():
                self.expand_index_recursively(child_idx)

    def get_file_path_from_index(self, proxy_index):
        src_index = self.mapToSource(proxy_index)
        return self.fs_model.filePath(src_index)

    def get_all_checked_paths(self):
        return [path for path, checked in self.checked_files_dict.items() if checked]

    def get_checked_files(self):
        return [path for path, checked in self.checked_files_dict.items() if checked and os.path.isfile(path)]
