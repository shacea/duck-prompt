import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from utils.helpers import init_utils, get_resource_path

def main():
    if sys.platform.startswith("win"):
        try:
            # DPI 인식 설정 (Windows)
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception as e:
            print(f"Error setting DPI awareness: {e}") # 오류 로깅

    # Qt High DPI 설정
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 유틸리티 초기화 (tiktoken 로딩 등)
    init_utils()

    app = QApplication(sys.argv)

    try:
        icon_path = get_resource_path("rubber_duck.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
        else:
            print(f"Icon file not found at: {icon_path}") # 아이콘 파일 부재 로깅
    except Exception as e:
        print(f"Error loading application icon: {e}") # 아이콘 로딩 오류 로깅

    # MainWindow 생성 및 실행
    # TODO: Core 서비스 초기화 및 주입 필요 (app.py 또는 main.py에서 수행)
    window = MainWindow(mode="Code Enhancer Prompt Builder") # 기본 모드 설정
    window.show()
    sys.exit(app.exec_())
