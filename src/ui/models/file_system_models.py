import os
import fnmatch
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QModelIndex, QFileInfo, QAbstractItemModel, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon, QColor, QBrush
from PyQt6.QtWidgets import QTreeView, QApplication, QStyle
from typing import Callable, Optional, Set, List, Dict, Any
from src.features.file_management.molecules.file_tree_builder import FileTreeNode
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# --- Constants ---
NODE_ROLE = Qt.ItemDataRole.UserRole + 1 # Role to store FileTreeNode reference
PATH_ROLE = Qt.ItemDataRole.UserRole + 2 # Role to store absolute path

def dict_to_file_tree_node(node_dict: Dict[str, Any]) -> FileTreeNode:
    """Recursively converts a dictionary back into a FileTreeNode object structure."""
    path = Path(node_dict['path'])
    node = FileTreeNode(path, node_dict['is_dir'])
    node.checked = node_dict.get('checked', False)
    
    for child_dict in node_dict.get('children', []):
        child_node = dict_to_file_tree_node(child_dict)
        node.add_child(child_node)
        
    return node

# --- Cached File System Model (using QStandardItemModel) ---
class CachedFileSystemModel(QStandardItemModel):
    """
    A model based on QStandardItemModel that displays the cached directory structure.
    It gets populated/updated by the FileSystemService.
    """
    # Signal emitted when the model needs to be repopulated
    request_repopulation = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(['Name']) # Single column for name/icon
        self._icon_provider = QApplication.style() # Use application style for default icons
        self._folder_icon = self._icon_provider.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        self._file_icon = self._icon_provider.standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    def populate_from_cache(self, root_node: Optional[FileTreeNode]):
        """
        Clears the model and populates it from the FileTreeNode structure.
        The root folder itself is not shown; its children are the top-level items.
        """
        self.clear()
        self.setHorizontalHeaderLabels(['Name']) # Reset header after clear
        if root_node:
            self._populate_children(self.invisibleRootItem(), root_node)
        logger.info("CachedFileSystemModel populated from cache.")

    def _populate_children(self, parent_item: QStandardItem, parent_node: FileTreeNode):
        """Recursively populates children items."""
        # Sort children by name (directories first, then files)
        sorted_children = sorted(parent_node.children, key=lambda node: (not node.is_dir, node.name.lower()))

        for child_node in sorted_children:
            child_item = self._create_item_from_node(child_node)
            parent_item.appendRow(child_item)
            if child_node.is_dir:
                self._populate_children(child_item, child_node)

    def _create_item_from_node(self, node: FileTreeNode) -> QStandardItem:
        """Creates a QStandardItem from a FileTreeNode."""
        item = QStandardItem(node.name)
        item.setEditable(False)
        item.setData(node, NODE_ROLE) # Store the node object
        item.setData(str(node.path), PATH_ROLE) # Store the path string
        item.setIcon(self._folder_icon if node.is_dir else self._file_icon)
        # Set checkable flag (proxy model will handle actual check state)
        item.setCheckable(True)
        item.setCheckState(Qt.CheckState.Unchecked) # Default to unchecked
        return item

    def find_item_by_path(self, path: str) -> Optional[QStandardItem]:
        """Finds a QStandardItem in the model by its absolute path."""
        if not path: return None
        # Iterate through all items to find the one with the matching path
        # This can be slow for very large models. Consider optimizing if needed.
        root = self.invisibleRootItem()
        queue = [root.child(i, 0) for i in range(root.rowCount())]
        while queue:
            item = queue.pop(0)
            if not item: continue
            item_path = item.data(PATH_ROLE)
            if item_path == path:
                return item
            # Add children to the queue
            for i in range(item.rowCount()):
                 child = item.child(i, 0)
                 if child: queue.append(child)
        return None

    def update_model_from_cache_change(self, cache_root: Optional[FileTreeNode]):
        """Handles cache updates from the service."""
        # For simplicity, repopulate the entire model on any cache change.
        logger.info("Received cache update signal. Repopulating model.")
        self.populate_from_cache(cache_root)


# --- Checkable Proxy Model (Adapted for CachedFileSystemModel) ---
class CheckableProxyModel(QSortFilterProxyModel):
    """
    Proxy model that provides checkable items.
    Handles recursive checking for folders and multi-selection checking.
    Works with CachedFileSystemModel.
    """
    # Signal to inform the controller about a check state change
    file_check_state_changed = pyqtSignal(str, bool)

    def __init__(self, project_folder_getter: Callable[[], Optional[str]], fs_service: Optional[Any], tree_view: QTreeView, parent=None):
        super().__init__(parent)
        self.project_folder_getter = project_folder_getter
        self.fs_service = fs_service
        self.tree_view = tree_view
        self.checked_files_dict: Dict[str, bool] = {} # {file_path: bool} - Stores the check state
        self._is_setting_data = False

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Determines if a row should be shown. In the new FAH architecture,
        the file list is pre-filtered by the FileSystemService, so this
        proxy model no longer needs to perform filtering. It just accepts all rows.
        """
        return True

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Returns data for the item, including check state based on checked_files_dict.
        """
        if not index.isValid():
            return None

        if index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            file_path = self.mapToSource(index).data(PATH_ROLE)
            if file_path:
                is_checked = self.checked_files_dict.get(file_path, False)
                return Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked
            return Qt.CheckState.Unchecked

        return super().data(index, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Returns item flags, ensuring checkable status comes from source."""
        flags = super().flags(index)
        if index.column() == 0:
            source_index = self.mapToSource(index)
            source_flags = self.sourceModel().flags(source_index)
            if source_flags & Qt.ItemFlag.ItemIsUserCheckable:
                flags |= Qt.ItemFlag.ItemIsUserCheckable
            flags |= Qt.ItemFlag.ItemIsEnabled
        return flags


    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """
        Sets data for the item, handling check state changes for the proxy model's dictionary.
        Propagates changes to children based on the source model structure.
        """
        if self._is_setting_data:
            return False
        if index.column() != 0 or role != Qt.ItemDataRole.CheckStateRole:
            return super().setData(index, value, role)

        source_index = self.mapToSource(index)
        source_item = self.sourceModel().itemFromIndex(source_index)
        if not source_item: return False

        file_path = source_item.data(PATH_ROLE)
        node: Optional[FileTreeNode] = source_item.data(NODE_ROLE)
        if not file_path or not node:
            logger.warning(f"setData failed: Could not get path/node for index {index.row()},{index.column()}")
            return False

        self._is_setting_data = True
        try:
            if isinstance(value, Qt.CheckState):
                new_check_state = value
            elif isinstance(value, int):
                new_check_state = Qt.CheckState(value)
            else:
                logger.warning(f"setData: Unexpected value type for CheckStateRole: {type(value)}")
                self._is_setting_data = False
                return False

            is_checked = (new_check_state == Qt.CheckState.Checked)
            
            # Emit signal to notify controller BEFORE changing internal state
            # This allows the controller to be the source of truth for the change
            self.file_check_state_changed.emit(file_path, is_checked)
            
            # The actual update of the dictionary and UI will happen
            # once the controller processes the command and updates the service state.
            # For a more responsive UI, we can preemptively update the UI here,
            # but for consistency, we'll let the backend drive the state.
            # Let's do a hybrid: update locally and let backend confirm.
            
            self._update_recursive_check_state(source_item, is_checked)
            
            # We must emit dataChanged for all affected indices.
            # A simple way is to reset the whole model view, but that's inefficient.
            # Let's emit for the top-level item. The recursive update will handle children.
            self.dataChanged.emit(index, index, [role])

            return True

        except Exception as e:
            logger.exception(f"Error in setData for path {file_path}: {e}")
            return False
        finally:
            self._is_setting_data = False

    def _update_recursive_check_state(self, parent_source_item: QStandardItem, checked: bool):
        """Recursively updates the internal check state dictionary and emits dataChanged."""
        parent_path = parent_source_item.data(PATH_ROLE)
        if not parent_path: return

        if checked:
            self.checked_files_dict[parent_path] = True
        elif parent_path in self.checked_files_dict:
            del self.checked_files_dict[parent_path]
        
        parent_source_index = self.sourceModel().indexFromItem(parent_source_item)
        parent_proxy_index = self.mapFromSource(parent_source_index)
        if parent_proxy_index.isValid():
            self.dataChanged.emit(parent_proxy_index, parent_proxy_index, [Qt.ItemDataRole.CheckStateRole])
        
        # Recurse for children
        for row in range(parent_source_item.rowCount()):
            child_source_item = parent_source_item.child(row, 0)
            if child_source_item:
                self._update_recursive_check_state(child_source_item, checked)

    def expand_index_recursively(self, proxy_index: QModelIndex):
        """Recursively expands the given index and its children in the tree view."""
        if not proxy_index.isValid(): return
        self.tree_view.expand(proxy_index)
        child_count = self.rowCount(proxy_index)
        for row in range(child_count):
            child_proxy_idx = self.index(row, 0, proxy_index)
            if child_proxy_idx.isValid():
                 source_idx = self.mapToSource(child_proxy_idx)
                 source_item = self.sourceModel().itemFromIndex(source_idx)
                 if source_item:
                     node: Optional[FileTreeNode] = source_item.data(NODE_ROLE)
                     if node and node.is_dir:
                          self.expand_index_recursively(child_proxy_idx)


    def get_file_path_from_index(self, proxy_index: QModelIndex) -> Optional[str]:
        """Gets the file path from a proxy index by looking at the source model."""
        if not proxy_index.isValid(): return None
        source_index = self.mapToSource(proxy_index)
        if source_index.isValid():
            return self.sourceModel().data(source_index, PATH_ROLE)
        return None

    def get_all_checked_paths(self) -> List[str]:
        """Returns a list of all paths currently marked as checked in the dictionary."""
        return [path for path, checked in self.checked_files_dict.items() if checked]

    def get_checked_files(self) -> List[str]:
        """
        Returns a list of checked paths that correspond to actual files.
        """
        checked_files = []
        source_model = self.sourceModel()
        if not isinstance(source_model, CachedFileSystemModel):
             logger.warning("get_checked_files: Source model not CachedFileSystemModel.")
             return []

        for path, is_checked in self.checked_files_dict.items():
            if not is_checked: continue

            item = source_model.find_item_by_path(path)
            if item:
                node: Optional[FileTreeNode] = item.data(NODE_ROLE)
                if node and not node.is_dir:
                    checked_files.append(path)
        
        return checked_files

    def update_check_states_from_dict(self):
        """Forces UI update based on the current checked_files_dict."""
        logger.debug("Updating visual check states from dictionary.")
        self.beginResetModel()
        self.endResetModel()
        logger.debug("Finished updating visual check states.")

    def set_check_state_for_path(self, path: str, checked: bool):
        """Externally set the check state for a path and its children."""
        source_item = self.sourceModel().find_item_by_path(path)
        if source_item:
            self._is_setting_data = True
            self._update_recursive_check_state(source_item, checked)
            self._is_setting_data = False
