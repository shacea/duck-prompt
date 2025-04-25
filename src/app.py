
import sys
import os
import ctypes
import logging # 로깅 추가
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from utils.helpers import get_resource_path

def setup_logging():
    """Sets up basic logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    # Optionally add file handler later if needed
    # handler = logging.FileHandler('app.log', encoding='utf-8')
    # handler.setFormatter(logging.Formatter(log_format))
    # logging.getLogger().addHandler(handler)
    logging.info("Logging setup complete.")

def main():
    setup_logging() # 로깅 설정 호출

    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception as e:
            logging.warning(f"Error setting DPI awareness: {e}") # 로깅 사용

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    try:
        icon_path = get_resource_path("rubber_duck.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
        else:
            logging.warning(f"Icon file not found at: {icon_path}") # 로깅 사용
    except Exception as e:
        logging.error(f"Error loading application icon: {e}", exc_info=True) # 로깅 사용

    try:
        window = MainWindow(mode="Code Enhancer Prompt Builder")
        window.show()
        sys.exit(app.exec_())
    except (ConnectionError, ValueError) as e:
         # Catch DB connection or config load errors from MainWindow init
         logging.critical(f"Application initialization failed: {e}", exc_info=True)
         # Optionally show a simple message box if GUI is partially available
         # QMessageBox.critical(None, "Fatal Error", f"Application failed to start:\n{e}")
         sys.exit(1) # Exit with error code
    except Exception as e:
         logging.critical(f"An unexpected error occurred during application startup: {e}", exc_info=True)
         sys.exit(1)

