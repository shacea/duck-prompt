
import os
import sys
import tiktoken
from typing import Union
import threading

ENC = None

def preload_encoding():
    global ENC
    ENC = tiktoken.get_encoding("o200k_base")

def init_utils():
    thread = threading.Thread(target=preload_encoding)
    thread.daemon = True
    thread.start()
    thread.join()  # ENC 초기화 대기

def get_resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def calculate_char_count(text: str) -> int:
    return len(text)

def calculate_token_count(text: str) -> Union[int, None]:
    try:
        enc = tiktoken.get_encoding("o200k_base")
        return len(enc.encode(text))
    except Exception as e:
        print(f"토큰 계산 중 오류 발생: {str(e)}")
        return None
