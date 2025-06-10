"""Shared logger atom - provides consistent logging across features"""
import logging
import sys
from typing import Optional


class Logger:
    """Centralized logger configuration"""
    
    _initialized = False
    
    @classmethod
    def setup(
        cls,
        level: int = logging.INFO,
        format_string: Optional[str] = None,
        log_file: Optional[str] = None
    ) -> None:
        """Setup root logger configuration"""
        if cls._initialized:
            return
        
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(format_string)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(console_formatter)
            root_logger.addHandler(file_handler)
        
        cls._initialized = True
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance for a specific module"""
        return logging.getLogger(name)