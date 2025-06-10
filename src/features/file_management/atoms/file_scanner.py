"""File scanner atom - scans directories for files"""
import os
import logging
from pathlib import Path
from typing import List, Set, Optional, Dict, Any

logger = logging.getLogger(__name__)


class FileScanner:
    """Scans directories and returns file information"""
    
    def __init__(self):
        self.excluded_dirs = {
            '.git', '__pycache__', 'node_modules', 
            '.venv', 'venv', '.env', 'env',
            '.idea', '.vscode', 'dist', 'build',
            '*.egg-info', '.pytest_cache', '.mypy_cache'
        }
    
    def scan_directory(
        self, 
        directory: Path, 
        recursive: bool = True,
        include_hidden: bool = False,
        exclude_patterns: Optional[Set[str]] = None
    ) -> List[Path]:
        """Scan directory for files"""
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Directory does not exist or is not a directory: {directory}")
            return []
        
        files = []
        exclude_patterns = exclude_patterns or set()
        
        try:
            if recursive:
                for root, dirs, filenames in os.walk(directory):
                    root_path = Path(root)
                    
                    # Filter out excluded directories
                    dirs[:] = [
                        d for d in dirs 
                        if d not in self.excluded_dirs
                        and (include_hidden or not d.startswith('.'))
                    ]
                    
                    # Add files
                    for filename in filenames:
                        if not include_hidden and filename.startswith('.'):
                            continue
                        
                        file_path = root_path / filename
                        if not self._should_exclude(file_path, exclude_patterns):
                            files.append(file_path)
            else:
                # Non-recursive scan
                for item in directory.iterdir():
                    if item.is_file():
                        if not include_hidden and item.name.startswith('.'):
                            continue
                        if not self._should_exclude(item, exclude_patterns):
                            files.append(item)
        
        except PermissionError as e:
            logger.error(f"Permission denied accessing directory: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
        
        return sorted(files)
    
    def _should_exclude(self, file_path: Path, patterns: Set[str]) -> bool:
        """Check if file should be excluded based on patterns"""
        path_str = str(file_path)
        for pattern in patterns:
            if pattern in path_str:
                return True
        return False
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed information about a file"""
        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'is_binary': self._is_binary(file_path),
                'extension': file_path.suffix
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {
                'path': str(file_path),
                'name': file_path.name,
                'error': str(e)
            }
    
    def _is_binary(self, file_path: Path) -> bool:
        """Check if file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except:
            return True