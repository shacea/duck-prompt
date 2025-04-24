import os
import sys
# import tiktoken # No longer directly used here, moved to TokenCalculationService
from typing import Union, Optional
# import threading # No longer needed for preloading here
from pathlib import Path # pathlib 사용

# --- 경로 관련 ---
def get_project_root() -> Path:
    """Gets the project root directory reliably."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller 번들 환경
        return Path(sys._MEIPASS)
    else:
        # 개발 환경 (main.py 또는 src/app.py에서 실행 가정)

        src_dir = Path(__file__).parent.parent.resolve()
        # 프로젝트 루트는 src 폴더의 부모
        return src_dir.parent

def get_resource_path(relative_path: str) -> str:
    """
    Gets the absolute path to a resource file/directory.
    Assumes the 'resources' directory is at the project root.
    """
    project_root = get_project_root()
    resource_path = project_root / "resources" / relative_path
    return str(resource_path)

# --- 텍스트 계산 관련 ---
def calculate_char_count(text: str) -> int:
    """Calculates the number of characters in the text."""
    return len(text)

# calculate_token_count is now handled by TokenCalculationService
# def calculate_token_count(text: str) -> Optional[int]:
#     """
#     Calculates the number of tokens using the preloaded tiktoken encoding.
#     Returns None if encoding is not available or an error occurs.
#     """
#     # ... (old implementation removed) ...

# init_utils and preload_encoding are removed as tiktoken loading is now
# handled within TokenCalculationService when needed.
# def preload_encoding():
#     """Preloads the tiktoken encoding in a separate thread."""
#     # ... (old implementation removed) ...

# def init_utils():
#     """Initializes utility functions, including preloading encoding."""
#     # ... (old implementation removed) ...

# def get_encoding() -> Optional[tiktoken.Encoding]:
#     """Returns the preloaded tiktoken encoding, loading if necessary."""
#     # ... (old implementation removed) ...
