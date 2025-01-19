
import sys
import os
import ctypes
from dotenv import load_dotenv

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from main_window import MainWindow
from utils import init_utils

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

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
    icon_path = resource_path("resources/rubber_duck.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    window = MainWindow(mode="Code Enhancer Prompt Builder")
    window.show()
    sys.exit(app.exec_())
