import sys
import os
import ctypes
from dotenv import load_dotenv

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from main_window import MainWindow
from utils import init_utils, get_resource_path # get_resource_path 추가

# resource_path 함수 제거 (utils.get_resource_path 사용)

if __name__ == '__main__':
    # .env 로드
    load_dotenv()

    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    init_utils()
    app = QApplication(sys.argv)
    # utils.get_resource_path 사용
    icon_path = get_resource_path("resources/rubber_duck.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    # MainWindow 생성 시 mode 전달
    window = MainWindow(mode="Code Enhancer Prompt Builder")
    window.show()
    sys.exit(app.exec_())
