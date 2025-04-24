import sys
import os
import ctypes
from dotenv import load_dotenv

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# 변경된 경로에서 import
from ui.main_window import MainWindow
from utils.helpers import init_utils, get_resource_path

def main():
    # .env 로드 (프로젝트 루트 기준)
    # src/app.py 기준 상위 폴더의 .env 파일
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

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

    # 아이콘 경로 설정 (get_resource_path 사용)
    try:
        # get_resource_path는 resources 폴더 기준이므로 파일명만 전달
        icon_path = get_resource_path("rubber_duck.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
        else:
            print(f"Icon file not found at: {icon_path}") # 아이콘 파일 부재 로깅
    except Exception as e:
        print(f"Error loading application icon: {e}") # 아이콘 로딩 오류 로깅

    # MainWindow 생성 및 실행
    # TODO: Core 서비스 초기화 및 주입 필요
    window = MainWindow(mode="Code Enhancer Prompt Builder") # 기본 모드 설정
    window.show()
    sys.exit(app.exec_())

# 이 파일이 직접 실행될 때 main 함수 호출 (기존 방식 유지)
# if __name__ == '__main__':
#     main()
# 위 방식 대신 main.py에서 app.main()을 호출하도록 변경됨
