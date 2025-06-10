"""File system service organism - manages all file operations"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from watchdog.events import FileSystemEvent

from src.gateway import EventBus, Event, ServiceLocator
from ..atoms.file_scanner import FileScanner
from ..atoms.file_watcher import FileWatcher
from ..molecules.file_tree_builder import FileTreeBuilder, FileTreeNode
from ..molecules.gitignore_filter import GitignoreFilter

logger = logging.getLogger(__name__)


# File system events
class FileSystemChangedEvent(Event):
    """Event emitted when file system changes"""
    def __init__(self, event_type: str, path: str):
        self.event_type = event_type
        self.path = path


class ProjectFolderChangedEvent(Event):
    """Event emitted when project folder changes"""
    def __init__(self, old_path: Optional[str], new_path: str):
        self.old_path = old_path
        self.new_path = new_path


class FileSystemService:
    """High-level file system service"""
    
    def __init__(self):
        self.scanner = FileScanner()
        self.watcher = FileWatcher()
        self.tree_builder = FileTreeBuilder()
        self.gitignore_filter = GitignoreFilter()
        
        self.project_folder: Optional[Path] = None
        self.file_cache: List[Path] = []
        self.tree_cache: Optional[FileTreeNode] = None
        
        # Load gitignore patterns from config
        self._load_gitignore_patterns()
    
    def _load_gitignore_patterns(self):
        """Load gitignore patterns from configuration"""
        try:
            config_service = ServiceLocator.get("config")
            if config_service and config_service.gitignore_manager:
                patterns = config_service.gitignore_manager.get_all_patterns()
                self.gitignore_filter.load_patterns(patterns)
                logger.info(f"Loaded {len(patterns)} gitignore patterns")
        except Exception as e:
            logger.warning(f"Could not load gitignore patterns: {e}")
    
    def set_project_folder(self, folder_path: str) -> bool:
        """Set the project folder"""
        new_path = Path(folder_path)
        
        if not new_path.exists() or not new_path.is_dir():
            logger.error(f"Invalid project folder: {folder_path}")
            return False
        
        old_path = str(self.project_folder) if self.project_folder else None
        self.project_folder = new_path
        
        # Stop existing watcher
        if self.watcher.is_watching():
            self.watcher.stop()
        
        # Clear cache
        self.file_cache.clear()
        self.tree_cache = None
        
        # Emit event
        EventBus.emit(ProjectFolderChangedEvent(old_path=old_path, new_path=str(new_path)))
        
        # Start watching the new folder
        self._start_watching()
        
        # Scan the new folder
        self.refresh_file_system()
        
        logger.info(f"Project folder set to: {new_path}")
        return True
    
    def get_project_folder(self) -> Optional[str]:
        """Get current project folder"""
        return str(self.project_folder) if self.project_folder else None
    
    def refresh_file_system(self):
        """Refresh file system cache"""
        if not self.project_folder:
            logger.warning("No project folder set")
            return
        
        # Scan directory
        self.file_cache = self.scanner.scan_directory(
            self.project_folder,
            recursive=True,
            include_hidden=False
        )
        
        # Apply gitignore filter
        self.file_cache = self.gitignore_filter.filter_files(
            self.file_cache,
            self.project_folder
        )
        
        # Rebuild tree
        self.tree_cache = self.tree_builder.build_tree(
            self.project_folder,
            self.file_cache
        )
        
        logger.info(f"File system refreshed: {len(self.file_cache)} files found")
    
    def get_file_tree(self) -> Optional[Dict[str, Any]]:
        """Get file tree structure"""
        if not self.tree_cache:
            self.refresh_file_system()
        
        if self.tree_cache:
            return self.tree_cache.to_dict()
        return None
    
    def check_file(self, file_path: str, checked: bool):
        """Check or uncheck a file"""
        self.tree_builder.check_file(file_path, checked)
        
        # Update tree cache if it exists
        if self.tree_cache:
            node = self.tree_builder.path_to_node.get(file_path)
            if node:
                node.checked = checked
    
    def check_all_files(self, checked: bool):
        """Check or uncheck all files"""
        self.tree_builder.check_all(checked)
        
        # Update tree cache if it exists
        if self.tree_cache:
            for node in self.tree_builder.path_to_node.values():
                if not node.is_dir:
                    node.checked = checked
    
    def get_checked_files(self) -> List[str]:
        """Get list of checked files"""
        return self.tree_builder.get_checked_files()
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Read file content"""
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def generate_directory_tree(self, include_files: bool = True, max_depth: Optional[int] = None) -> str:
        """Generate directory tree text"""
        if not self.tree_cache:
            self.refresh_file_system()
        
        if self.tree_cache:
            return self.tree_builder.generate_tree_text(self.tree_cache)
        return ""
    
    def _start_watching(self):
        """Start watching the project folder"""
        if not self.project_folder:
            return
        
        def on_change(event: FileSystemEvent):
            """Handle file system change"""
            logger.debug(f"File system event: {event.event_type} - {event.src_path}")
            
            # Emit event
            EventBus.emit(FileSystemChangedEvent(
                event_type=event.event_type,
                path=event.src_path
            ))
            
            # Schedule refresh (debounced in real implementation)
            self.refresh_file_system()
        
        try:
            self.watcher.start(
                self.project_folder,
                on_change,
                ignore_patterns={'.git', '__pycache__', '*.pyc'}
            )
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
    
    def stop_watching(self):
        """Stop file system watcher"""
        self.watcher.stop()
    
    def apply_gitignore_filter(self, file_paths: List[str]) -> List[str]:
        """Apply gitignore filtering to file paths"""
        paths = [Path(p) for p in file_paths]
        filtered = self.gitignore_filter.filter_files(paths, self.project_folder)
        return [str(p) for p in filtered]
