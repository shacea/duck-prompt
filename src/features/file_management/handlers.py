"""File management feature command handlers"""
import logging
from src.gateway.bus.file_management_command_bus import FileManagementCommandBus
from src.gateway import EventBus, ServiceLocator
from .commands import (
    SetProjectFolder, GetProjectFolder, ScanDirectory, GetFileTree,
    CheckFile, CheckAllFiles, GetCheckedFiles, GetFileContent,
    RefreshFileSystem, ApplyGitignoreFilter, StartFileWatcher,
    StopFileWatcher, GetDirectoryTree, GetFilteredFiles
)
from .organisms.file_system_service import FileSystemService

logger = logging.getLogger(__name__)


# Initialize file system service and register with ServiceLocator
file_system_service = FileSystemService()
ServiceLocator.provide("file_system", file_system_service)


@FileManagementCommandBus.register(SetProjectFolder)
async def handle_set_project_folder(cmd: SetProjectFolder):
    """Set the project folder"""
    service = ServiceLocator.get("file_system")
    success = service.set_project_folder(cmd.folder_path)
    tree = service.get_file_tree()
    return {"success": success, "path": cmd.folder_path, "tree": tree}


@FileManagementCommandBus.register(GetProjectFolder)
async def handle_get_project_folder(cmd: GetProjectFolder):
    """Get current project folder"""
    service = ServiceLocator.get("file_system")
    path = service.get_project_folder()
    return {"path": path}


@FileManagementCommandBus.register(ScanDirectory)
async def handle_scan_directory(cmd: ScanDirectory):
    """Scan a directory for files"""
    service = ServiceLocator.get("file_system")
    from pathlib import Path
    
    files = service.scanner.scan_directory(
        Path(cmd.directory_path),
        recursive=cmd.recursive,
        include_hidden=cmd.include_hidden
    )
    
    # Apply gitignore filter
    filtered_files = service.gitignore_filter.filter_files(files)
    
    return {
        "directory": cmd.directory_path,
        "files": [str(f) for f in filtered_files],
        "count": len(filtered_files)
    }


@FileManagementCommandBus.register(GetFileTree)
async def handle_get_file_tree(cmd: GetFileTree):
    """Get the file tree structure"""
    service = ServiceLocator.get("file_system")
    
    if cmd.root_path:
        # Set project folder if provided
        service.set_project_folder(cmd.root_path)
    
    tree = service.get_file_tree()
    return {"tree": tree}


@FileManagementCommandBus.register(CheckFile)
async def handle_check_file(cmd: CheckFile):
    """Check or uncheck a file"""
    service = ServiceLocator.get("file_system")
    service.check_file(cmd.file_path, cmd.checked)
    return {"file": cmd.file_path, "checked": cmd.checked}


@FileManagementCommandBus.register(CheckAllFiles)
async def handle_check_all_files(cmd: CheckAllFiles):
    """Check or uncheck all files"""
    service = ServiceLocator.get("file_system")
    service.check_all_files(cmd.checked)
    
    checked_count = len(service.get_checked_files())
    return {"checked": cmd.checked, "count": checked_count}


@FileManagementCommandBus.register(GetCheckedFiles)
async def handle_get_checked_files(cmd: GetCheckedFiles):
    """Get all checked files"""
    service = ServiceLocator.get("file_system")
    files = service.get_checked_files()
    return {"files": files, "count": len(files)}


@FileManagementCommandBus.register(GetFileContent)
async def handle_get_file_content(cmd: GetFileContent):
    """Read file content"""
    service = ServiceLocator.get("file_system")
    content = service.get_file_content(cmd.file_path)
    
    return {
        "file": cmd.file_path,
        "content": content,
        "exists": content is not None
    }


@FileManagementCommandBus.register(RefreshFileSystem)
async def handle_refresh_file_system(cmd: RefreshFileSystem):
    """Refresh file system cache"""
    service = ServiceLocator.get("file_system")
    service.refresh_file_system()
    
    return {
        "status": "refreshed",
        "file_count": len(service.file_cache)
    }


@FileManagementCommandBus.register(ApplyGitignoreFilter)
async def handle_apply_gitignore_filter(cmd: ApplyGitignoreFilter):
    """Apply gitignore filtering to files"""
    service = ServiceLocator.get("file_system")
    filtered = service.apply_gitignore_filter(cmd.file_paths)
    
    return {
        "original_count": len(cmd.file_paths),
        "filtered_count": len(filtered),
        "filtered_files": filtered
    }


@FileManagementCommandBus.register(StartFileWatcher)
async def handle_start_file_watcher(cmd: StartFileWatcher):
    """Start file system watcher"""
    service = ServiceLocator.get("file_system")
    
    # Set project folder and start watching
    success = service.set_project_folder(cmd.watch_path)
    
    return {
        "started": success and service.watcher.is_watching(),
        "path": cmd.watch_path
    }


@FileManagementCommandBus.register(StopFileWatcher)
async def handle_stop_file_watcher(cmd: StopFileWatcher):
    """Stop file system watcher"""
    service = ServiceLocator.get("file_system")
    service.stop_watching()
    
    return {"stopped": True}


@FileManagementCommandBus.register(GetDirectoryTree)
async def handle_get_directory_tree(cmd: GetDirectoryTree):
    """Generate directory tree text"""
    service = ServiceLocator.get("file_system")
    
    if str(service.project_folder) != cmd.root_path:
        service.set_project_folder(cmd.root_path)

    if cmd.checked_only:
        tree_text = service.generate_checked_directory_tree()
    else:
        tree_text = service.generate_directory_tree(
            include_files=cmd.include_files,
            max_depth=cmd.max_depth
        )
    
    return {"tree": tree_text}


@FileManagementCommandBus.register(GetFilteredFiles)
async def handle_get_filtered_files(cmd: GetFilteredFiles):
    """Get files with filtering applied"""
    service = ServiceLocator.get("file_system")
    from pathlib import Path
    
    # Scan directory
    files = service.scanner.scan_directory(
        Path(cmd.root_path),
        recursive=True,
        exclude_patterns=set(cmd.exclude_patterns or [])
    )
    
    # Apply patterns if provided
    if cmd.patterns:
        import fnmatch
        filtered = []
        for file_path in files:
            for pattern in cmd.patterns:
                if fnmatch.fnmatch(str(file_path), pattern):
                    filtered.append(file_path)
                    break
        files = filtered
    
    return {
        "root": cmd.root_path,
        "files": [str(f) for f in files],
        "count": len(files)
    }
