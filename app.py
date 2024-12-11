import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from main_window import MainWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 앱 아이콘 설정 (수정된 경로)
    icon_path = resource_path("resources/rubber_duck.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())