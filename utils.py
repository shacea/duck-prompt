# utils.py
import os
import sys
import tiktoken
from typing import Union
import threading

ENC = None  # 전역 변수로 인코딩 객체를 저장할 예정

def preload_encoding():
    global ENC
    ENC = tiktoken.get_encoding("o200k_base")

# 프로그램 실행시 init_utils 함수를 호출해서 백그라운드로 인코딩 미리 로딩
def init_utils():
    thread = threading.Thread(target=preload_encoding)
    thread.daemon = True
    thread.start()

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

import tiktoken

def calculate_char_count(text: str) -> int:
    """Calculate character count of given text"""
    return len(text)

def calculate_token_count(text: str) -> Union[int, None]:
    """Calculate token count using tiktoken"""
    try:
        enc = tiktoken.get_encoding("o200k_base")
        return len(enc.encode(text))
    except Exception as e:
        print(f"토큰 계산 중 오류 발생: {str(e)}")
        return None
