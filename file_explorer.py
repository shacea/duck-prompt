
import os
from PyQt5.QtCore import QSortFilterProxyModel, Qt
from PyQt5.QtWidgets import QFileSystemModel

class FilteredFileSystemModel(QFileSystemModel):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config

    def setRootPathFiltered(self, path):
        idx = self.setRootPath(path)
        return idx

    def is_file_allowed(self, file_path, project_folder):
        if project_folder:
            rel_path = os.path.relpath(file_path, project_folder)
        else:
            rel_path = file_path

        dirs_in_path = rel_path.split(os.sep)[:-1]
        for d in dirs_in_path:
            if d in self.config.excluded_dirs:
                return False
        ext = os.path.splitext(file_path)[1].lower()
        if len(self.config.allowed_extensions) > 0:
            if ext not in self.config.allowed_extensions:
                return False
        return True

class CheckableProxyModel(QSortFilterProxyModel):
    def __init__(self, fs_model, project_folder_getter, parent=None):
        super().__init__(parent)
        self.fs_model = fs_model
        self.project_folder_getter = project_folder_getter
        self.checked_files_dict = {}

    def data(self, index, role=Qt.DisplayRole):
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

                src_index = self.mapToSource(index)
                if self.fs_model.isDir(src_index):
                    self.check_all_children(src_index, is_checked)

                self.dataChanged.emit(index, index, [Qt.CheckStateRole])
                return True
        return super().setData(index, value, role)

    def ensure_loaded(self, parent_index):
        while self.fs_model.canFetchMore(parent_index):
            self.fs_model.fetchMore(parent_index)
        row_count = self.fs_model.rowCount(parent_index)
        for row in range(row_count):
            child_index = self.fs_model.index(row, 0, parent_index)
            if self.fs_model.isDir(child_index):
                self.ensure_loaded(child_index)

    def check_all_children(self, parent_index, is_checked):
        self.ensure_loaded(parent_index)
        row_count = self.fs_model.rowCount(parent_index)
        for row in range(row_count):
            child_index = self.fs_model.index(row, 0, parent_index)
            if child_index.isValid():
                fpath = self.fs_model.filePath(child_index)
                self.checked_files_dict[fpath] = is_checked
                if self.fs_model.isDir(child_index):
                    self.check_all_children(child_index, is_checked)
        self.layoutChanged.emit()

    def get_file_path_from_index(self, proxy_index):
        src_index = self.mapToSource(proxy_index)
        file_path = self.fs_model.filePath(src_index)
        return file_path

    def get_checked_files(self):
        project_folder = self.project_folder_getter()
        files = []
        for fpath, checked in self.checked_files_dict.items():
            if checked:
                if os.path.isfile(fpath) and self.fs_model.is_file_allowed(fpath, project_folder):
                    files.append(fpath)
        return files

    def get_all_checked_paths(self):
        checked_paths = []
        for fpath, checked in self.checked_files_dict.items():
            if checked:
                checked_paths.append(fpath)
        return checked_paths
