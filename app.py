import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from main_window import MainWindow
from utils import init_utils

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    # 윈도우 DPI 인식 활성화
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    # High DPI Scaling 활성화
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    init_utils()  # 인코딩 모델 미리 로딩 시작
    app = QApplication(sys.argv)
    icon_path = resource_path("resources/rubber_duck.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    # 기본 모드: "Code Enhancer Prompt Builder"
    window = MainWindow(mode="Code Enhancer Prompt Builder")
    window.show()
    sys.exit(app.exec_())
