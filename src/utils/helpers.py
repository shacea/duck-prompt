import os
import sys
import tiktoken
from typing import Union, Optional
import threading
from pathlib import Path # pathlib 사용

# --- Tiktoken 인코딩 관련 ---
ENC: Optional[tiktoken.Encoding] = None
enc_lock = threading.Lock() # 스레드 안전성을 위한 잠금

def preload_encoding():
    """Preloads the tiktoken encoding in a separate thread."""
    global ENC
    try:
        with enc_lock:
            if ENC is None: # 중복 로딩 방지
                print("Preloading tiktoken encoding...")
                ENC = tiktoken.get_encoding("o200k_base")
                print("Tiktoken encoding loaded.")
    except Exception as e:
        print(f"Error preloading tiktoken encoding: {e}")
        # ENC가 None으로 유지됨

def init_utils():
    """Initializes utility functions, including preloading encoding."""
    # 백그라운드 스레드에서 인코딩 로딩 시작
    thread = threading.Thread(target=preload_encoding, daemon=True)
    thread.start()
    # 메인 스레드는 계속 진행 (필요시 thread.join()으로 대기)

def get_encoding() -> Optional[tiktoken.Encoding]:
    """Returns the preloaded tiktoken encoding, loading if necessary."""
    global ENC
    if ENC is None:
        # 아직 로드되지 않았으면 동기적으로 로드 시도 (UI 블로킹 가능성)
        print("Tiktoken encoding not preloaded, loading synchronously...")
        preload_encoding() # 잠금 포함된 함수 호출
    return ENC

# --- 경로 관련 ---
def get_project_root() -> Path:
    """Gets the project root directory reliably."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller 번들 환경
        return Path(sys._MEIPASS)
    else:
        # 개발 환경 (main.py 또는 src/app.py에서 실행 가정)
        # helpers.py 위치 기준: src/utils/helpers.py
        # src 폴더 찾기: helpers.py -> utils -> src
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

def calculate_token_count(text: str) -> Optional[int]:
    """
    Calculates the number of tokens using the preloaded tiktoken encoding.
    Returns None if encoding is not available or an error occurs.
    """
    enc = get_encoding()
    if enc is None:
        print("Token calculation failed: Encoding not available.")
        return None
    try:
        return len(enc.encode(text))
    except Exception as e:
        print(f"Error calculating tokens: {str(e)}")
        return None

# 사용 예시:
# init_utils() # 앱 시작 시 호출
# icon_path = get_resource_path("rubber_duck.ico")
# char_count = calculate_char_count("some text")
# token_count = calculate_token_count("some text")
