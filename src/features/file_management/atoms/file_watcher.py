"""File watcher atom - monitors file system changes"""
import logging
from pathlib import Path
from typing import Optional, Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class FileWatcherHandler(FileSystemEventHandler):
    """Handles file system events"""
    
    def __init__(self, callback: Callable[[FileSystemEvent], None], ignore_patterns: Optional[Set[str]] = None):
        self.callback = callback
        self.ignore_patterns = ignore_patterns or {'.git', '__pycache__', '.pyc'}
    
    def _should_ignore(self, event: FileSystemEvent) -> bool:
        """Check if event should be ignored"""
        path_str = str(event.src_path)
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
        return False
    
    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event"""
        if not self._should_ignore(event):
            try:
                self.callback(event)
            except Exception as e:
                logger.error(f"Error in file watcher callback: {e}")


class FileWatcher:
    """Watches for file system changes"""
    
    def __init__(self):
        self.observer: Optional[Observer] = None
        self.watch_path: Optional[Path] = None
        self.handler: Optional[FileWatcherHandler] = None
    
    def start(self, path: Path, callback: Callable[[FileSystemEvent], None], ignore_patterns: Optional[Set[str]] = None):
        """Start watching a directory"""
        if self.observer and self.observer.is_alive():
            self.stop()
        
        self.watch_path = path
        self.handler = FileWatcherHandler(callback, ignore_patterns)
        self.observer = Observer()
        
        try:
            self.observer.schedule(self.handler, str(path), recursive=True)
            self.observer.start()
            logger.info(f"Started file watcher for: {path}")
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            self.observer = None
            raise
    
    def stop(self):
        """Stop watching"""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=2)
            logger.info(f"Stopped file watcher for: {self.watch_path}")
        
        self.observer = None
        self.watch_path = None
        self.handler = None
    
    def is_watching(self) -> bool:
        """Check if watcher is active"""
        return bool(self.observer and self.observer.is_alive())