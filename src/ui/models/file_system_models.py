import os
import fnmatch
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QModelIndex, QFileInfo, QAbstractItemModel, pyqtSignal # Added QAbstractItemModel, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon, QColor, QBrush # Added QStandardItemModel, QStandardItem, QIcon, QColor, QBrush
from PyQt6.QtWidgets import QTreeView, QApplication, QStyle # Added QApplication, QStyle
from typing import Callable, Optional, Set, List, Dict, Any # List, Dict, Any 추가
from core.services.filesystem_service import FilesystemService
from core.services.directory_cache_service import CacheNode # Added
import logging

logger = logging.getLogger(__name__)

# --- Constants ---
NODE_ROLE = Qt.ItemDataRole.UserRole + 1 # Role to store CacheNode reference
PATH_ROLE = Qt.ItemDataRole.UserRole + 2 # Role to store absolute path

# --- Cached File System Model (using QStandardItemModel) ---
class CachedFileSystemModel(QStandardItemModel):
    """
    A model based on QStandardItemModel that displays the cached directory structure.
    It gets populated/updated by the DirectoryCacheService.
    """
    # Signal emitted when the model needs to be repopulated
    request_repopulation = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(['Name']) # Single column for name/icon
        self._icon_provider = QApplication.style() # Use application style for default icons
        self._folder_icon = self._icon_provider.standardIcon(QStyle.StandardPixmap.SP_DirIcon) # QStyle.SP_DirIcon -> QStyle.StandardPixmap.SP_DirIcon
        self._file_icon = self._icon_provider.standardIcon(QStyle.StandardPixmap.SP_FileIcon) # QStyle.SP_FileIcon -> QStyle.StandardPixmap.SP_FileIcon

    def populate_from_cache(self, root_node: Optional[CacheNode]):
        """
        Clears the model and populates it from the CacheNode structure.
        The root folder itself is not shown; its children are the top-level items.
        """
        self.clear()
        self.setHorizontalHeaderLabels(['Name']) # Reset header after clear
        if root_node and not root_node.ignored: # Only populate if root exists and is not ignored
            # Don't create a visible item for the root folder itself.
            # Instead, populate its children directly under the invisible root.
            self._populate_children(self.invisibleRootItem(), root_node)
        logger.info("CachedFileSystemModel populated from cache.")

    def _populate_children(self, parent_item: QStandardItem, parent_node: CacheNode):
        """Recursively populates children items."""
        # Sort children by name (directories first, then files)
        sorted_children = sorted(parent_node.children.values(), key=lambda node: (not node.is_dir, node.name.lower()))

        for child_node in sorted_children:
            if not child_node.ignored: # Skip ignored items
                child_item = self._create_item_from_node(child_node)
                parent_item.appendRow(child_item)
                if child_node.is_dir:
                    self._populate_children(child_item, child_node)

    def _create_item_from_node(self, node: CacheNode) -> QStandardItem:
        """Creates a QStandardItem from a CacheNode."""
        item = QStandardItem(node.name)
        item.setEditable(False)
        item.setData(node, NODE_ROLE) # Store the node object
        item.setData(node.path, PATH_ROLE) # Store the path
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

    def update_model_from_cache_change(self, cache_root: Optional[CacheNode]):
        """Handles cache updates from the service."""
        # For simplicity, repopulate the entire model on any cache change.
        # More granular updates (insertRows, removeRows, dataChanged) are possible
        # but significantly more complex to implement correctly based on cache diffs.
        logger.info("Received cache update signal. Repopulating model.")
        self.populate_from_cache(cache_root)


# --- Checkable Proxy Model (Adapted for CachedFileSystemModel) ---
class CheckableProxyModel(QSortFilterProxyModel):
    """
    Proxy model that provides checkable items and filters based on ignore patterns.
    Handles recursive checking for folders and multi-selection checking.
    Works with CachedFileSystemModel (QStandardItemModel based).
    """
    # Signal to indicate check state dictionary has changed
    check_state_changed = pyqtSignal()

    def __init__(self, project_folder_getter: Callable[[], Optional[str]], fs_service: FilesystemService, tree_view: QTreeView, parent=None):
        super().__init__(parent)
        # Source model is now CachedFileSystemModel (set via setSourceModel)
        self.project_folder_getter = project_folder_getter
        self.fs_service = fs_service # Still needed for should_ignore fallback? Maybe not.
        self.tree_view = tree_view
        self.checked_files_dict: Dict[str, bool] = {} # {file_path: bool} - Stores the check state
        self._ignore_patterns: Set[str] = set()
        self._is_setting_data = False # 재귀적 setData 호출 방지 플래그

    def set_ignore_patterns(self, patterns: Set[str]):
        """Sets the ignore patterns used for filtering."""
        if self._ignore_patterns != patterns:
            self._ignore_patterns = patterns
            logger.info(f"Ignore patterns updated. Invalidating filter.")
            self.invalidateFilter() # Trigger refiltering

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Determines if a row should be shown. Reads 'ignored' status from CacheNode.
        """
        source_model = self.sourceModel()
        if not isinstance(source_model, QStandardItemModel): # Check if source model is set and correct type
             logger.warning("filterAcceptsRow: Source model not set or not QStandardItemModel.")
             return False

        source_index = source_model.index(source_row, 0, source_parent)
        if not source_index.isValid():
            return False

        item = source_model.itemFromIndex(source_index)
        if not item: return False # Should not happen

        node: Optional[CacheNode] = item.data(NODE_ROLE)

        # If node data is missing or node is marked as ignored in the cache, filter it out
        if node is None or node.ignored:
            # If it's filtered out, ensure it's removed from the check state dict
            path = item.data(PATH_ROLE)
            if path and path in self.checked_files_dict:
                logger.debug(f"Removing filtered/ignored item from checked_files_dict: {path}")
                del self.checked_files_dict[path]
                self.check_state_changed.emit() # Notify change
            return False

        # If node exists and is not ignored, accept the row
        return True

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Returns data for the item, including check state based on checked_files_dict.
        """
        if not index.isValid():
            return None

        # Handle check state for column 0
        if index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            file_path = self.mapToSource(index).data(PATH_ROLE) # Get path from source item
            if file_path:
                is_checked = self.checked_files_dict.get(file_path, False)
                return Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked
            return Qt.CheckState.Unchecked # Default if path not found

        # For other roles, delegate to the source model (QStandardItemModel)
        return super().data(index, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Returns item flags, ensuring checkable status comes from source."""
        # Start with flags from the proxy model itself
        flags = super().flags(index)
        if index.column() == 0:
            # Get flags from the source model item (QStandardItem)
            source_index = self.mapToSource(index)
            source_flags = self.sourceModel().flags(source_index)
            # Ensure checkable flag is included if set in source
            if source_flags & Qt.ItemFlag.ItemIsUserCheckable: # Qt.ItemIsUserCheckable -> Qt.ItemFlag.ItemIsUserCheckable
                flags |= Qt.ItemFlag.ItemIsUserCheckable # Qt.ItemIsUserCheckable -> Qt.ItemFlag.ItemIsUserCheckable
            # Ensure item is enabled
            flags |= Qt.ItemFlag.ItemIsEnabled # Qt.ItemIsEnabled -> Qt.ItemFlag.ItemIsEnabled
        return flags


    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """
        Sets data for the item, handling check state changes for the proxy model's dictionary.
        Propagates changes to children based on the source model structure.
        """
        if self._is_setting_data:
            # logger.debug(f"setData blocked by flag for index: {self.get_file_path_from_index(index)}")
            return False
        if index.column() != 0 or role != Qt.ItemDataRole.CheckStateRole:
            return super().setData(index, value, role)

        source_index = self.mapToSource(index)
        source_item = self.sourceModel().itemFromIndex(source_index)
        if not source_item: return False

        file_path = source_item.data(PATH_ROLE)
        node: Optional[CacheNode] = source_item.data(NODE_ROLE)
        if not file_path or not node:
            logger.warning(f"setData failed: Could not get path/node for index {index.row()},{index.column()}")
            return False

        # logger.debug(f"▶ setData called: path={file_path}, role={role}, value={value}")
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
            current_state_in_dict = self.checked_files_dict.get(file_path, False)

            if is_checked == current_state_in_dict:
                # logger.debug(f"setData: No state change needed for {file_path}.")
                self._is_setting_data = False
                return True

            # logger.debug(f"setData processing state change for: {file_path}, New state: {is_checked}")

            # Update the dictionary
            if is_checked:
                self.checked_files_dict[file_path] = True
            elif file_path in self.checked_files_dict:
                del self.checked_files_dict[file_path]
                # logger.debug(f"  Item unchecked and removed from checked_files_dict: {file_path}")

            # Emit dataChanged for the current index to update its visual state
            self.dataChanged.emit(index, index, [role])
            indices_to_signal = {index} # Track indices needing UI update

            # If it's a directory, update children recursively
            if node.is_dir:
                # logger.debug(f"  {file_path} is a directory. Updating children...")
                changed_children_proxy_indices = self._update_children_state_recursive(source_item, is_checked)
                indices_to_signal.update(changed_children_proxy_indices)
                # logger.debug(f"  Finished updating children for {file_path}. Total signals needed: {len(indices_to_signal)}")

                # Expand checked folders (optional)
                if is_checked:
                    # logger.debug(f"  Expanding checked folder: {file_path}")
                    self.expand_index_recursively(index)

            # Emit dataChanged for all affected children (already done inside _update_children_state_recursive)
            # logger.debug(f"Emitting dataChanged for {len(indices_to_signal)} indices.")
            # for idx_to_signal in indices_to_signal:
            #     if idx_to_signal.isValid():
            #         # logger.debug(f"    Emitting for: {self.get_file_path_from_index(idx_to_signal)}")
            #         self.dataChanged.emit(idx_to_signal, idx_to_signal, [Qt.ItemDataRole.CheckStateRole])

            self.check_state_changed.emit() # Signal that the dictionary was modified
            # logger.debug(f"setData returning True for path: {file_path}")
            return True

        except Exception as e:
            logger.exception(f"Error in setData for path {file_path}: {e}")
            return False
        finally:
            # logger.debug("setData finished. Releasing flag.")
            self._is_setting_data = False

    def _update_children_state_recursive(self, parent_source_item: QStandardItem, checked: bool) -> Set[QModelIndex]:
        """
        Recursively updates the check state dictionary for children of a source item.
        Returns a set of *proxy* indices whose state was visually changed.
        """
        changed_proxy_indices = set()
        source_model = self.sourceModel()

        for row in range(parent_source_item.rowCount()):
            child_source_item = parent_source_item.child(row, 0)
            if not child_source_item: continue

            child_node: Optional[CacheNode] = child_source_item.data(NODE_ROLE)
            child_path = child_source_item.data(PATH_ROLE)

            if not child_node or not child_path: continue
            # Skip ignored items as they are not visible anyway
            if child_node.ignored: continue

            current_state_in_dict = self.checked_files_dict.get(child_path, False)
            needs_update = (checked != current_state_in_dict)

            if needs_update:
                if checked:
                    self.checked_files_dict[child_path] = True
                elif child_path in self.checked_files_dict:
                    del self.checked_files_dict[child_path]
                    # logger.debug(f"      Child unchecked and removed from dict: {child_path}")

                # Find the corresponding proxy index for signaling
                child_source_index = source_model.indexFromItem(child_source_item)
                child_proxy_index = self.mapFromSource(child_source_index)
                if child_proxy_index.isValid():
                    changed_proxy_indices.add(child_proxy_index)
                    # Emit dataChanged immediately for this child
                    self.dataChanged.emit(child_proxy_index, child_proxy_index, [Qt.ItemDataRole.CheckStateRole])
                    # logger.debug(f"      Child state changed & signaled: {child_path}")

            # Recurse if it's a directory
            if child_node.is_dir:
                grandchildren_indices = self._update_children_state_recursive(child_source_item, checked)
                changed_proxy_indices.update(grandchildren_indices)

        return changed_proxy_indices

    def expand_index_recursively(self, proxy_index: QModelIndex):
        """Recursively expands the given index and its children in the tree view."""
        if not proxy_index.isValid(): return
        self.tree_view.expand(proxy_index)
        # Iterate through children in the proxy model
        child_count = self.rowCount(proxy_index)
        for row in range(child_count):
            child_proxy_idx = self.index(row, 0, proxy_index)
            if child_proxy_idx.isValid():
                 # Check if the child corresponds to a directory in the source model
                 source_idx = self.mapToSource(child_proxy_idx)
                 source_item = self.sourceModel().itemFromIndex(source_idx)
                 if source_item:
                     node: Optional[CacheNode] = source_item.data(NODE_ROLE)
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
        # logger.debug(f"get_all_checked_paths called. Returning {len(self.checked_files_dict)} paths.")
        return list(self.checked_files_dict.keys())


    def get_checked_files(self) -> List[str]:
        """
        Returns a list of checked paths that correspond to actual files.
        Reads 'is_dir' status from the internal dictionary.
        """
        checked_files = []
        source_model = self.sourceModel()
        if not isinstance(source_model, QStandardItemModel):
             logger.warning("get_checked_files: Source model not available.")
             return []

        # Iterate through the dictionary keys (paths)
        for path, is_checked in self.checked_files_dict.items():
            if not is_checked: continue # Should not happen if only True is stored, but check anyway

            # Find the item in the model to check its type
            # This is inefficient. Store type in checked_files_dict?
            # Or iterate through model items? Let's try finding item.
            item = source_model.find_item_by_path(path) # Use helper method
            if item:
                node: Optional[CacheNode] = item.data(NODE_ROLE)
                if node and not node.is_dir:
                    checked_files.append(path)
            else:
                # Fallback: If item not found in model (shouldn't happen often), use os.path
                # This is slow, especially on network drives.
                logger.warning(f"Item not found in model for checked path: {path}. Falling back to os.path.isfile().")
                try:
                    if os.path.isfile(path):
                        checked_files.append(path)
                except OSError as e:
                    logger.warning(f"Error checking if path is file in get_checked_files (fallback): {path}, Error: {e}")


        # logger.debug(f"get_checked_files called. Returning {len(checked_files)} file paths.")
        return checked_files

    def update_check_states_from_dict(self):
        """Forces UI update based on the current checked_files_dict."""
        logger.debug("Updating visual check states from dictionary.")
        self.beginResetModel() # More drastic update signal
        # Or iterate and emit dataChanged for all items?
        # for path in self.checked_files_dict.keys():
        #     item = self.sourceModel().find_item_by_path(path)
        #     if item:
        #         source_index = self.sourceModel().indexFromItem(item)
        #         proxy_index = self.mapFromSource(source_index)
        #         if proxy_index.isValid():
        #             self.dataChanged.emit(proxy_index, proxy_index, [Qt.ItemDataRole.CheckStateRole])
        self.endResetModel()
        logger.debug("Finished updating visual check states.")
