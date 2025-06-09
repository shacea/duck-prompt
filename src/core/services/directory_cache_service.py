import os
import time
import logging
from typing import Optional, Dict, Any, Set, List, Callable
from pathlib import Path
import threading
from collections import deque

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, DirModifiedEvent, FileModifiedEvent

from .filesystem_service import FilesystemService

logger = logging.getLogger(__name__)

# --- Data Structure for Cache ---
class CacheNode:
    """Represents a node in the directory cache."""
    def __init__(self, name: str, path: str, is_dir: bool, ignored: bool, children: Optional[Dict[str, 'CacheNode']] = None):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.ignored = ignored
        self.children: Dict[str, 'CacheNode'] = children if children is not None else {} # {name: CacheNode}

    def to_dict(self) -> Dict[str, Any]:
        """Converts the node to a dictionary (for potential serialization)."""
        return {
            "name": self.name,
            "path": self.path,
            "is_dir": self.is_dir,
            "ignored": self.ignored,
            "children": {name: child.to_dict() for name, child in self.children.items()}
        }

# --- Background Scanner Worker ---
class ScannerWorker(QObject):
    """Worker object to perform directory scanning in a background thread."""
    finished = pyqtSignal(object) # Emits the root CacheNode when done
    progress = pyqtSignal(str)    # Emits status updates
    error = pyqtSignal(str)       # Emits error messages

    def __init__(self, root_path: str, fs_service: FilesystemService, ignore_patterns: Set[str]):
        super().__init__()
        self.root_path = root_path
        self.fs_service = fs_service
        self.ignore_patterns = ignore_patterns
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        """Scans the directory structure starting from root_path."""
        logger.info(f"ScannerWorker started for path: {self.root_path}")
        try:
            root_node = self._scan_directory(self.root_path)
            if self._is_cancelled:
                logger.info("ScannerWorker cancelled.")
                self.error.emit("Scan cancelled.")
            else:
                logger.info(f"ScannerWorker finished successfully for {self.root_path}.")
                self.finished.emit(root_node)
        except Exception as e:
            logger.exception(f"Error during directory scan for {self.root_path}")
            self.error.emit(f"Scan error: {e}")

    def _scan_directory(self, dir_path: str) -> Optional[CacheNode]:
        """Recursively scans a directory and builds CacheNode structure."""
        if self._is_cancelled: return None

        try:
            path_obj = Path(dir_path)
            if not path_obj.exists() or not path_obj.is_dir():
                logger.warning(f"Directory not found or not a directory: {dir_path}")
                return None

            is_root_ignored = self.fs_service.should_ignore(dir_path, self.root_path, self.ignore_patterns, True)
            root_node = CacheNode(name=path_obj.name, path=dir_path, is_dir=True, ignored=is_root_ignored)

            # Use deque for breadth-first or depth-first scanning (here using deque like a stack for DFS)
            scan_queue = deque([(root_node, dir_path)])
            processed_dirs = 0

            while scan_queue:
                if self._is_cancelled: return None
                parent_node, current_dir = scan_queue.pop()

                # Skip scanning children if parent is ignored (optimization)
                if parent_node.ignored:
                    # logger.debug(f"Skipping ignored directory children: {current_dir}")
                    continue

                try:
                    # Use os.scandir for better performance
                    with os.scandir(current_dir) as it:
                        for entry in it:
                            if self._is_cancelled: return None
                            entry_path = entry.path
                            entry_name = entry.name
                            try:
                                is_dir = entry.is_dir()
                                # Check if ignored *before* adding to cache/queue
                                is_ignored = self.fs_service.should_ignore(entry_path, self.root_path, self.ignore_patterns, is_dir)

                                child_node = CacheNode(name=entry_name, path=entry_path, is_dir=is_dir, ignored=is_ignored)
                                parent_node.children[entry_name] = child_node

                                # If it's a directory and not ignored, add to queue for further scanning
                                if is_dir and not is_ignored:
                                    scan_queue.append((child_node, entry_path))

                            except OSError as stat_err:
                                logger.warning(f"Could not stat file {entry_path}: {stat_err}. Skipping.")
                                # Add as ignored node to prevent re-scanning attempts
                                error_node = CacheNode(name=entry_name, path=entry_path, is_dir=False, ignored=True) # Assume file if stat fails
                                parent_node.children[entry_name] = error_node
                            except Exception as inner_e:
                                logger.error(f"Error processing entry {entry_path}: {inner_e}")


                    processed_dirs += 1
                    if processed_dirs % 100 == 0: # Update progress periodically
                        self.progress.emit(f"Scanned {processed_dirs} directories...")

                except OSError as scandir_err:
                    logger.error(f"Could not scan directory {current_dir}: {scandir_err}")
                    # Mark parent as ignored if scanning fails? Or just log? Logged for now.
                except Exception as outer_e:
                     logger.error(f"Unexpected error scanning directory {current_dir}: {outer_e}")

            self.progress.emit(f"Scan complete. Processed {processed_dirs} directories.")
            return root_node

        except Exception as e:
            logger.exception(f"Fatal error during scan setup for {dir_path}")
            self.error.emit(f"Scan setup error: {e}")
            return None


# --- Watchdog Event Handler ---
class CacheUpdateHandler(QObject, FileSystemEventHandler):
    """Handles filesystem events and signals the DirectoryCacheService."""
    # Signals to notify the main service about specific changes
    needs_rescan = pyqtSignal(str) # path
    item_created = pyqtSignal(str, bool) # path, is_dir
    item_deleted = pyqtSignal(str) # path
    item_moved = pyqtSignal(str, str) # src_path, dest_path
    item_modified = pyqtSignal(str) # path (for files)

    def __init__(self, cache_service: 'DirectoryCacheService'):
        QObject.__init__(self)
        FileSystemEventHandler.__init__(self)
        self.cache_service = cache_service
        self._ignore_patterns = set()
        self._root_path = None

    def update_config(self, root_path: str, ignore_patterns: Set[str]):
        self._root_path = root_path
        self._ignore_patterns = ignore_patterns

    def _should_process(self, event: FileSystemEvent) -> bool:
        """Checks if an event should be processed (not ignored)."""
        if not self._root_path: return False
        # Ignore directory modifications themselves, only care about contents
        # However, modifying a directory might indicate permission changes etc., needing rescan?
        # Let's ignore DirModifiedEvent for now to reduce noise. FileModifiedEvent is important.
        if isinstance(event, DirModifiedEvent):
             # logger.debug(f"Ignoring DirModifiedEvent: {event.src_path}")
             return False
        # Ignore modifications to ignored files/dirs
        path = event.src_path
        is_dir = event.is_directory
        if self.cache_service.fs_service.should_ignore(path, self._root_path, self._ignore_patterns, is_dir):
            # logger.debug(f"Ignoring event for ignored path: {path}")
            return False
        return True

    def on_created(self, event: FileSystemEvent):
        if self._should_process(event):
            logger.info(f"Watchdog: Detected creation: {event.src_path} (is_dir={event.is_directory})")
            self.item_created.emit(event.src_path, event.is_directory)

    def on_deleted(self, event: FileSystemEvent):
        # Check ignore based on path *before* deletion
        if not self._root_path: return False
        is_dir = event.is_directory # Note: is_directory might be unreliable after deletion
        # We might need to check if the path *was* ignored if we cached ignore status
        # For simplicity, assume if the path itself matches an ignore pattern, we ignore the delete event
        if self.cache_service.fs_service.should_ignore(event.src_path, self._root_path, self._ignore_patterns, is_dir):
             # logger.debug(f"Ignoring delete event for ignored path: {event.src_path}")
             return
        logger.info(f"Watchdog: Detected deletion: {event.src_path}")
        self.item_deleted.emit(event.src_path)

    def on_modified(self, event: FileSystemEvent):
        # Only process file modifications for now
        if isinstance(event, FileModifiedEvent) and self._should_process(event):
            logger.info(f"Watchdog: Detected modification: {event.src_path}")
            self.item_modified.emit(event.src_path)

    def on_moved(self, event: FileSystemEvent):
        # Check if either source or destination is ignored
        if not self._root_path: return False
        src_ignored = self.cache_service.fs_service.should_ignore(event.src_path, self._root_path, self._ignore_patterns, event.is_directory)
        dest_ignored = self.cache_service.fs_service.should_ignore(event.dest_path, self._root_path, self._ignore_patterns, event.is_directory)
        if src_ignored and dest_ignored:
            # logger.debug(f"Ignoring move event for ignored paths: {event.src_path} -> {event.dest_path}")
            return
        logger.info(f"Watchdog: Detected move: {event.src_path} -> {event.dest_path}")
        self.item_moved.emit(event.src_path, event.dest_path)


# --- Main Cache Service ---
class DirectoryCacheService(QObject):
    """
    Manages the directory cache, background scanning, and filesystem monitoring.
    """
    cache_updated = pyqtSignal(object) # Emits the root CacheNode
    scan_progress = pyqtSignal(str)
    scan_error = pyqtSignal(str)
    scan_finished = pyqtSignal() # Signal when scan completes successfully

    def __init__(self, fs_service: FilesystemService, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.fs_service = fs_service
        self.cache_root: Optional[CacheNode] = None
        self.current_root_path: Optional[str] = None
        self.current_ignore_patterns: Set[str] = set()
        self._cache_lock = threading.Lock() # Lock for accessing the cache

        self._scanner_thread: Optional[QThread] = None
        self._scanner_worker: Optional[ScannerWorker] = None

        self._observer: Optional[Observer] = None
        self._event_handler: Optional[CacheUpdateHandler] = None
        self._observer_thread: Optional[threading.Thread] = None

    def start_scan(self, root_path: str, ignore_patterns: Set[str]):
        """Starts a background scan for the given path."""
        logger.info(f"CacheService: Received request to scan: {root_path}")
        self.stop_scan() # Stop any previous scan
        self.stop_monitoring() # Stop monitoring during scan

        self.current_root_path = root_path
        self.current_ignore_patterns = ignore_patterns
        with self._cache_lock:
            self.cache_root = None # Clear cache before scan

        self._scanner_thread = QThread()
        self._scanner_worker = ScannerWorker(root_path, self.fs_service, ignore_patterns)
        self._scanner_worker.moveToThread(self._scanner_thread)

        # Connect signals
        self._scanner_thread.started.connect(self._scanner_worker.run)
        self._scanner_worker.finished.connect(self._handle_scan_finished)
        self._scanner_worker.progress.connect(self.scan_progress.emit)
        self._scanner_worker.error.connect(self._handle_scan_error)

        # Cleanup connections
        self._scanner_worker.finished.connect(self._scanner_thread.quit)
        self._scanner_worker.finished.connect(self._scanner_worker.deleteLater)
        self._scanner_thread.finished.connect(self._scanner_thread.deleteLater)
        self._scanner_worker.error.connect(self._scanner_thread.quit) # Quit thread on error too
        self._scanner_worker.error.connect(self._scanner_worker.deleteLater)
        self._scanner_thread.finished.connect(self._cleanup_scanner_thread) # Custom cleanup slot

        self._scanner_thread.start()
        self.scan_progress.emit(f"Starting scan for {root_path}...")

    def stop_scan(self):
        """Stops the currently running scan."""
        if self._scanner_worker:
            logger.info("CacheService: Stopping scanner worker...")
            self._scanner_worker.cancel()
        if self._scanner_thread and self._scanner_thread.isRunning():
            logger.info("CacheService: Quitting scanner thread...")
            self._scanner_thread.quit()
            if not self._scanner_thread.wait(1000): # Wait 1 sec
                 logger.warning("Scanner thread did not quit gracefully.")
            self._cleanup_scanner_thread() # Ensure cleanup

    def _cleanup_scanner_thread(self):
        logger.debug("Cleaning up scanner thread/worker objects.")
        self._scanner_thread = None
        self._scanner_worker = None

    def _handle_scan_finished(self, root_node: CacheNode):
        """Handles the successful completion of a scan."""
        logger.info("CacheService: Scan finished successfully.")
        with self._cache_lock:
            self.cache_root = root_node
        self.cache_updated.emit(self.cache_root) # Emit the new cache
        self.scan_finished.emit() # Signal completion
        # Start monitoring after successful scan
        self.start_monitoring(self.current_root_path, self.current_ignore_patterns)

    def _handle_scan_error(self, error_msg: str):
        """Handles errors during the scan."""
        logger.error(f"CacheService: Scan error: {error_msg}")
        with self._cache_lock:
            self.cache_root = None # Clear cache on error
        self.scan_error.emit(error_msg)
        self.cache_updated.emit(None) # Emit empty cache
        # Do not start monitoring if scan failed

    def get_cache(self) -> Optional[CacheNode]:
        """Returns the current cache root node (thread-safe)."""
        with self._cache_lock:
            return self.cache_root

    # --- Filesystem Monitoring ---

    def start_monitoring(self, root_path: Optional[str], ignore_patterns: Set[str]):
        """Starts filesystem monitoring using watchdog."""
        if not root_path:
            logger.warning("Cannot start monitoring: root_path is None.")
            return
        if self._observer and self._observer.is_alive():
            logger.info("Monitor already running. Stopping and restarting.")
            self.stop_monitoring()

        logger.info(f"Starting filesystem monitor for: {root_path}")
        self.current_root_path = root_path # Update path just in case
        self.current_ignore_patterns = ignore_patterns

        self._event_handler = CacheUpdateHandler(self)
        self._event_handler.update_config(root_path, ignore_patterns)
        # Connect handler signals to service methods
        self._event_handler.item_created.connect(self._handle_item_created)
        self._event_handler.item_deleted.connect(self._handle_item_deleted)
        self._event_handler.item_moved.connect(self._handle_item_moved)
        self._event_handler.item_modified.connect(self._handle_item_modified)
        # self._event_handler.needs_rescan.connect(self._handle_needs_rescan) # Optional

        self._observer = Observer()
        try:
            # Watch the root path recursively
            self._observer.schedule(self._event_handler, root_path, recursive=True)
            # Run observer in a separate daemon thread
            self._observer_thread = threading.Thread(target=self._observer.start, daemon=True)
            self._observer_thread.start()
            logger.info(f"Filesystem monitor started successfully for {root_path}.")
        except OSError as e:
             logger.error(f"Failed to start watchdog observer for {root_path}: {e}. Check path permissions or if it's a network drive limitation.")
             QMessageBox.warning(None, "Monitoring Error", f"폴더 감시 시작 실패:\n{root_path}\n\n오류: {e}\n\n네트워크 드라이브 또는 권한 문제일 수 있습니다. 파일 변경 사항이 자동으로 반영되지 않을 수 있습니다.")
             self._observer = None
             self._observer_thread = None
        except Exception as e:
            logger.exception(f"Unexpected error starting watchdog observer for {root_path}")
            self._observer = None
            self._observer_thread = None


    def stop_monitoring(self):
        """Stops the filesystem monitor."""
        if self._observer and self._observer.is_alive():
            logger.info("Stopping filesystem monitor...")
            try:
                self._observer.stop()
                self._observer.join(timeout=1.0) # Wait for thread to finish
                if self._observer.is_alive():
                     logger.warning("Watchdog observer thread did not join gracefully.")
                else:
                     logger.info("Filesystem monitor stopped.")
            except Exception as e:
                 logger.error(f"Error stopping watchdog observer: {e}")
        self._observer = None
        self._observer_thread = None
        self._event_handler = None # Disconnect signals implicitly

    def update_ignore_patterns(self, ignore_patterns: Set[str]):
        """Updates ignore patterns for the running monitor."""
        self.current_ignore_patterns = ignore_patterns
        if self._event_handler:
            self._event_handler.update_config(self.current_root_path, ignore_patterns)
            logger.info("Watchdog ignore patterns updated.")
            # Trigger a cache update signal? Maybe not necessary unless filtering changes visibility
            # self.cache_updated.emit(self.get_cache())

    # --- Cache Update Handlers (Called by Watchdog Handler Signals) ---

    def _find_node(self, path: str) -> Optional[CacheNode]:
        """Finds a node in the cache by its absolute path."""
        if not self.cache_root or not self.current_root_path: return None
        if path == self.current_root_path: return self.cache_root

        try:
            relative_path = Path(path).relative_to(self.current_root_path)
            parts = relative_path.parts
        except ValueError:
            logger.warning(f"Path '{path}' is not relative to root '{self.current_root_path}'")
            return None

        current_node = self.cache_root
        for part in parts:
            if part in current_node.children:
                current_node = current_node.children[part]
            else:
                return None # Node not found
        return current_node

    def _find_parent_node(self, path: str) -> Optional[CacheNode]:
        """Finds the parent node of a given path."""
        parent_path = os.path.dirname(path)
        return self._find_node(parent_path)

    def _handle_item_created(self, path: str, is_dir: bool):
        logger.debug(f"CacheService: Handling item created: {path}")
        with self._cache_lock:
            if not self.cache_root or not self.current_root_path: return
            parent_node = self._find_parent_node(path)
            if parent_node and not parent_node.ignored:
                name = os.path.basename(path)
                # Check ignore status for the new item
                is_ignored = self.fs_service.should_ignore(path, self.current_root_path, self.current_ignore_patterns, is_dir)
                new_node = CacheNode(name=name, path=path, is_dir=is_dir, ignored=is_ignored)
                parent_node.children[name] = new_node
                logger.info(f"Cache updated: Added node {name} to parent {parent_node.path}")
                # If the new item is a directory and not ignored, we might need to scan its contents
                if is_dir and not is_ignored:
                    # For simplicity, trigger a full rescan for directory creation for now
                    # A more refined approach would scan just the new directory
                    logger.warning(f"Directory created ({path}), triggering full rescan for simplicity.")
                    self._handle_needs_rescan(f"Directory created: {path}")
                    return # Rescan handles cache update signal

                # Emit cache update signal only if not rescanning
                self.cache_updated.emit(self.cache_root)
            elif parent_node and parent_node.ignored:
                 logger.debug(f"Ignoring creation under ignored parent: {path}")
            else:
                 logger.warning(f"Parent node not found for created item: {path}")


    def _handle_item_deleted(self, path: str):
        logger.debug(f"CacheService: Handling item deleted: {path}")
        with self._cache_lock:
            if not self.cache_root or not self.current_root_path: return
            parent_node = self._find_parent_node(path)
            if parent_node:
                name = os.path.basename(path)
                if name in parent_node.children:
                    del parent_node.children[name]
                    logger.info(f"Cache updated: Removed node {name} from parent {parent_node.path}")
                    self.cache_updated.emit(self.cache_root)
                else:
                    logger.warning(f"Node '{name}' not found in parent '{parent_node.path}' for deletion.")
            else:
                # Could be the root directory itself being deleted?
                if path == self.current_root_path:
                     logger.warning("Root project directory deleted! Clearing cache.")
                     self.cache_root = None
                     self.cache_updated.emit(None)
                     self.stop_monitoring() # Stop monitoring if root is gone
                else:
                     logger.warning(f"Parent node not found for deleted item: {path}")

    def _handle_item_moved(self, src_path: str, dest_path: str):
        logger.debug(f"CacheService: Handling item moved: {src_path} -> {dest_path}")
        with self._cache_lock:
            if not self.cache_root or not self.current_root_path: return

            # 1. Find and remove source node
            src_parent_node = self._find_parent_node(src_path)
            src_name = os.path.basename(src_path)
            moved_node: Optional[CacheNode] = None
            if src_parent_node and src_name in src_parent_node.children:
                moved_node = src_parent_node.children.pop(src_name)
                logger.info(f"Cache updated: Removed source node {src_name} from {src_parent_node.path}")
            else:
                logger.warning(f"Source node not found for move: {src_path}")
                # If source not found, maybe trigger rescan?
                self._handle_needs_rescan(f"Source node not found for move: {src_path}")
                return

            # 2. Find destination parent node
            dest_parent_node = self._find_parent_node(dest_path)
            dest_name = os.path.basename(dest_path)

            # 3. Add node to destination parent (if parent exists and isn't ignored)
            if dest_parent_node and moved_node:
                 # Update node's name and path
                 moved_node.name = dest_name
                 moved_node.path = dest_path
                 # Re-check ignore status at new location
                 moved_node.ignored = self.fs_service.should_ignore(dest_path, self.current_root_path, self.current_ignore_patterns, moved_node.is_dir)

                 # Add to new parent only if parent isn't ignored
                 if not dest_parent_node.ignored:
                     dest_parent_node.children[dest_name] = moved_node
                     logger.info(f"Cache updated: Added moved node {dest_name} to {dest_parent_node.path}")
                 else:
                      logger.debug(f"Move destination parent ignored, node not added: {dest_path}")

                 # If a directory was moved, its children's paths also need updating (complex)
                 # For simplicity, trigger a rescan when directories are moved.
                 if moved_node.is_dir:
                      logger.warning(f"Directory moved ({src_path} -> {dest_path}), triggering full rescan for simplicity.")
                      self._handle_needs_rescan(f"Directory moved: {dest_path}")
                      return # Rescan handles cache update signal

                 # Emit cache update signal only if not rescanning
                 self.cache_updated.emit(self.cache_root)

            elif not dest_parent_node:
                 logger.warning(f"Destination parent node not found for move: {dest_path}")
                 # Trigger rescan if destination parent is missing
                 self._handle_needs_rescan(f"Destination parent not found for move: {dest_path}")
            # else: moved_node is None (already handled)


    def _handle_item_modified(self, path: str):
        # Currently, the cache doesn't store modification time or content hash.
        # So, a modification event doesn't change the cache structure itself.
        # We could potentially add mtime to CacheNode and update it here.
        # For now, just log it. The model displaying the cache might want this signal.
        logger.debug(f"CacheService: Handling item modified: {path}")
        # Find the node - maybe update an mtime attribute if we add one
        # with self._cache_lock:
        #     node = self._find_node(path)
        #     if node:
        #         # node.mtime = os.path.getmtime(path) # Example if mtime is added
        #         # self.cache_updated.emit(self.cache_root) # Emit if node data changes
        #         pass
        pass # No action on cache for modification currently

    def _handle_needs_rescan(self, reason: str):
        """Handles events that require a full rescan for simplicity."""
        logger.warning(f"Triggering rescan due to: {reason}")
        if self.current_root_path:
            # Emit error signal to potentially inform UI before starting scan
            self.scan_error.emit(f"Rescanning due to: {reason}")
            # Restart the scan
            self.start_scan(self.current_root_path, self.current_ignore_patterns)
        else:
            logger.error("Cannot rescan: current_root_path is not set.")

    def __del__(self):
        """Ensure threads are stopped when the service is deleted."""
        self.stop_scan()
        self.stop_monitoring()
