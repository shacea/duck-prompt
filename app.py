import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from main_window import MainWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    icon_path = resource_path("resources/rubber_duck.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    # 기본 모드: "Code Enhancer Prompt Builder"
    window = MainWindow(mode="Code Enhancer Prompt Builder")
    window.show()
    sys.exit(app.exec_())
