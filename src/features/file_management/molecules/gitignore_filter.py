"""Gitignore filter molecule - filters files based on gitignore patterns"""
import logging
import fnmatch
from pathlib import Path
from typing import List, Set, Optional

logger = logging.getLogger(__name__)


class GitignoreFilter:
    """Filters files based on gitignore patterns"""
    
    def __init__(self):
        self.patterns: Set[str] = set()
        self.compiled_patterns: List[str] = []
    
    def load_patterns(self, patterns: List[str]):
        """Load gitignore patterns"""
        self.patterns = set()
        self.compiled_patterns = []
        
        for pattern in patterns:
            pattern = pattern.strip()
            if pattern and not pattern.startswith('#'):
                self.patterns.add(pattern)
                # Convert gitignore pattern to fnmatch pattern
                if pattern.endswith('/'):
                    # Directory pattern
                    self.compiled_patterns.append(pattern.rstrip('/'))
                else:
                    self.compiled_patterns.append(pattern)
        
        logger.info(f"Loaded {len(self.compiled_patterns)} gitignore patterns")
    
    def should_ignore(self, file_path: Path, root_path: Optional[Path] = None) -> bool:
        """Check if a file should be ignored"""
        if root_path:
            try:
                relative_path = file_path.relative_to(root_path)
                path_str = str(relative_path).replace('\\', '/')
            except ValueError:
                path_str = str(file_path).replace('\\', '/')
        else:
            path_str = str(file_path).replace('\\', '/')
        
        # Check each pattern
        for pattern in self.compiled_patterns:
            if self._match_pattern(path_str, pattern):
                return True
        
        return False
    
    def filter_files(self, file_paths: List[Path], root_path: Optional[Path] = None) -> List[Path]:
        """Filter a list of files based on gitignore patterns"""
        filtered = []
        
        for file_path in file_paths:
            if not self.should_ignore(file_path, root_path):
                filtered.append(file_path)
        
        logger.debug(f"Filtered {len(file_paths)} files to {len(filtered)} files")
        return filtered
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Match a path against a gitignore pattern"""
        # Handle negation patterns (starting with !)
        if pattern.startswith('!'):
            return False
        
        # Handle directory patterns
        if '/' in pattern:
            # Pattern with directory separator
            if pattern.startswith('/'):
                # Absolute pattern (from root)
                pattern = pattern[1:]
                return fnmatch.fnmatch(path, pattern)
            else:
                # Relative pattern - can match anywhere
                parts = path.split('/')
                pattern_parts = pattern.split('/')
                
                for i in range(len(parts) - len(pattern_parts) + 1):
                    if all(fnmatch.fnmatch(parts[i + j], pattern_parts[j]) 
                           for j in range(len(pattern_parts))):
                        return True
                return False
        else:
            # Simple pattern - match basename
            basename = path.split('/')[-1]
            return fnmatch.fnmatch(basename, pattern)
    
    def add_pattern(self, pattern: str):
        """Add a single pattern"""
        pattern = pattern.strip()
        if pattern and not pattern.startswith('#'):
            self.patterns.add(pattern)
            if pattern.endswith('/'):
                self.compiled_patterns.append(pattern.rstrip('/'))
            else:
                self.compiled_patterns.append(pattern)
    
    def remove_pattern(self, pattern: str):
        """Remove a pattern"""
        pattern = pattern.strip()
        self.patterns.discard(pattern)
        # Rebuild compiled patterns
        self.load_patterns(list(self.patterns))
    
    def get_patterns(self) -> List[str]:
        """Get current patterns"""
        return sorted(list(self.patterns))