"""Gitignore manager molecule - manages gitignore patterns"""
import logging
from typing import List, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class GitignoreManager:
    """Manages gitignore patterns from database and .gitignore file"""
    
    def __init__(self):
        self._db_patterns: Set[str] = set()
        self._file_patterns: Set[str] = set()
    
    def load_from_database(self, patterns: List[str]) -> None:
        """Load patterns from database"""
        self._db_patterns = set(patterns)
        logger.info(f"Loaded {len(patterns)} patterns from database")
    
    def load_from_file(self, gitignore_path: Path) -> None:
        """Load patterns from .gitignore file"""
        if not gitignore_path.exists():
            logger.warning(f".gitignore file not found at {gitignore_path}")
            return
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                patterns = [
                    line.strip() 
                    for line in f 
                    if line.strip() and not line.startswith('#')
                ]
            self._file_patterns = set(patterns)
            logger.info(f"Loaded {len(patterns)} patterns from .gitignore file")
        except Exception as e:
            logger.error(f"Failed to load .gitignore file: {e}")
    
    def get_all_patterns(self) -> List[str]:
        """Get all unique patterns from both sources"""
        all_patterns = self._db_patterns.union(self._file_patterns)
        return sorted(list(all_patterns))
    
    def get_database_patterns(self) -> List[str]:
        """Get patterns from database only"""
        return sorted(list(self._db_patterns))
    
    def get_file_patterns(self) -> List[str]:
        """Get patterns from .gitignore file only"""
        return sorted(list(self._file_patterns))
    
    def update_database_patterns(self, patterns: List[str]) -> None:
        """Update database patterns"""
        self._db_patterns = set(patterns)
        logger.info(f"Updated database patterns: {len(patterns)} patterns")
    
    def should_ignore(self, file_path: str) -> bool:
        """Check if a file should be ignored based on patterns"""
        # This is a simplified implementation
        # In a real implementation, you'd use proper gitignore pattern matching
        for pattern in self.get_all_patterns():
            if pattern in file_path:
                return True
        return False