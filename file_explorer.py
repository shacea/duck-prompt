import os
import fnmatch
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
    .gitignore 패턴에 따라 파일/폴더 숨김 처리.
    """

    def __init__(self, fs_model: FilteredFileSystemModel, project_folder_getter, tree_view: QTreeView, parent=None):
        super().__init__(parent)
        self.fs_model = fs_model
        self.project_folder_getter = project_folder_getter
        self.tree_view = tree_view
        self.checked_files_dict = {}

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        .gitignore 패턴에 따라 파일/폴더를 숨길지 결정합니다.
        """
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

        file_name = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')

        patterns = self.fs_model.config.excluded_dirs

        for pattern in patterns:
            # 패턴이 '/'로 끝나면 디렉토리 패턴
            is_dir_pattern = pattern.endswith('/')
            cleaned_pattern = pattern.rstrip('/')

            # 디렉토리 패턴인데 현재 항목이 파일이면 건너뜀
            if is_dir_pattern and not self.sourceModel().isDir(source_index):
                continue

            # 1. 파일 이름 매칭 (e.g., *.log, __pycache__)
            if fnmatch.fnmatch(file_name, cleaned_pattern):
                # 디렉토리 패턴이면 디렉토리만 매칭
                if is_dir_pattern and self.sourceModel().isDir(source_index):
                    return False
                # 파일 패턴이면 파일/디렉토리 모두 매칭 (gitignore 기본 동작)
                elif not is_dir_pattern:
                    return False

            # 2. 상대 경로 매칭 (e.g., build/, docs/temp.txt)
            # 디렉토리 패턴일 경우, 경로 끝에 '/' 추가하여 매칭
            match_path = relative_path + '/' if self.sourceModel().isDir(source_index) else relative_path
            if fnmatch.fnmatch(match_path, pattern):
                 return False
            # 패턴에 /가 포함되어 있고, 디렉토리 패턴이 아닐 때도 경로 매칭 시도
            # (e.g. 'some/dir/file.txt' 패턴)
            if '/' in pattern and not is_dir_pattern:
                 if fnmatch.fnmatch(relative_path, pattern):
                     return False


        return True # 어떤 패턴과도 매치되지 않으면 표시

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
        parent_index 하위 모든 폴더/파일 체크 상태를 갱신 (필터링된 항목 제외)
        """
        row_count = self.fs_model.rowCount(parent_index)
        for row in range(row_count):
            child_index = self.fs_model.index(row, 0, parent_index)
            child_proxy_index = self.mapFromSource(child_index)

            # 프록시 인덱스가 유효한지 (필터링되지 않았는지) 확인
            if not child_proxy_index.isValid():
                continue

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
        # 필터링되어 보이지 않는 파일은 체크된 파일 목록에서 제외해야 할 수 있음
        # 현재 로직은 단순히 dict 기반이므로, 실제 보이는 파일만 가져오려면 추가 로직 필요
        # 하지만 현재 요구사항은 체크된 모든 파일이므로 그대로 둠
        return [path for path, checked in self.checked_files_dict.items() if checked and os.path.isfile(path)]
