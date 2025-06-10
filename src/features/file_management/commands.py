"""File management feature commands"""
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
from src.gateway.bus._base import Command


class SetProjectFolder(Command):
    """Command to set the project folder"""
    folder_path: str


class GetProjectFolder(Command):
    """Command to get current project folder"""
    pass


class ScanDirectory(Command):
    """Command to scan a directory for files"""
    directory_path: str
    recursive: bool = True
    include_hidden: bool = False


class GetFileTree(Command):
    """Command to get the file tree structure"""
    root_path: Optional[str] = None
    include_hidden: bool = False


class CheckFile(Command):
    """Command to check/select a file"""
    file_path: str
    checked: bool


class CheckAllFiles(Command):
    """Command to check all files"""
    checked: bool


class GetCheckedFiles(Command):
    """Command to get all checked files"""
    pass


class GetFileContent(Command):
    """Command to read file content"""
    file_path: str


class RefreshFileSystem(Command):
    """Command to refresh file system cache"""
    pass


class ApplyGitignoreFilter(Command):
    """Command to apply gitignore filtering"""
    file_paths: List[str]


class StartFileWatcher(Command):
    """Command to start file system watcher"""
    watch_path: str


class StopFileWatcher(Command):
    """Command to stop file system watcher"""
    pass


class GetDirectoryTree(Command):
    """Command to generate directory tree text"""
    root_path: str
    include_files: bool = True
    max_depth: Optional[int] = None
    checked_only: bool = False # Flag to generate tree for checked items only


class GetFilteredFiles(Command):
    """Command to get files with filtering applied"""
    root_path: str
    patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
