"""Shared file utilities atom"""
import os
from pathlib import Path
from typing import List, Optional, Set


class FileUtils:
    """Common file operation utilities"""
    
    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """Ensure a directory exists, create if it doesn't"""
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def read_lines(file_path: Path, encoding: str = 'utf-8') -> List[str]:
        """Read all lines from a file"""
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding=encoding) as f:
            return f.readlines()
    
    @staticmethod
    def write_lines(file_path: Path, lines: List[str], encoding: str = 'utf-8') -> None:
        """Write lines to a file"""
        with open(file_path, 'w', encoding=encoding) as f:
            f.writelines(lines)
    
    @staticmethod
    def find_files(
        root_path: Path,
        pattern: str = "*",
        recursive: bool = True,
        exclude_dirs: Optional[Set[str]] = None
    ) -> List[Path]:
        """Find files matching a pattern"""
        if exclude_dirs is None:
            exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
        
        files = []
        
        if recursive:
            for path in root_path.rglob(pattern):
                # Skip excluded directories
                if any(excluded in path.parts for excluded in exclude_dirs):
                    continue
                if path.is_file():
                    files.append(path)
        else:
            for path in root_path.glob(pattern):
                if path.is_file():
                    files.append(path)
        
        return sorted(files)
    
    @staticmethod
    def get_relative_path(file_path: Path, base_path: Path) -> str:
        """Get relative path from base path"""
        try:
            return str(file_path.relative_to(base_path))
        except ValueError:
            return str(file_path)
    
    @staticmethod
    def is_binary_file(file_path: Path) -> bool:
        """Check if a file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check for null bytes
                return b'\x00' in chunk
        except Exception:
            return True