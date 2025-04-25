
import sys
import os
import ctypes
import logging # 로깅 추가
from PyQt5.QtWidgets import QApplication, QMessageBox # QMessageBox 추가
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from utils.helpers import get_resource_path
from core.services.db_service import DbService # DbService 임포트

def setup_logging():
    """Sets up basic logging configuration."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    # Optionally add file handler later if needed
    # handler = logging.FileHandler('app.log', encoding='utf-8')
    # handler.setFormatter(logging.Formatter(log_format))
    # logging.getLogger().addHandler(handler)
    logging.info("Logging setup complete.")

def cleanup_logs(db_service: DbService):
    """Calls the log cleanup function."""
    try:
        logging.info("Attempting to clean up old Gemini logs...")
        db_service.cleanup_old_gemini_logs(days_to_keep=7) # 7일 이상된 로그 삭제
        logging.info("Log cleanup process finished.")
    except Exception as e:
        logging.error(f"Error during log cleanup: {e}", exc_info=True)

def main():
    setup_logging() # 로깅 설정 호출

    if sys.platform.startswith("win"):
        try:
            # DPI 인식 설정 (Windows)
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            logging.info("Set DPI awareness for Windows.")
        except AttributeError:
            logging.warning("ctypes.windll.shcore not available, DPI awareness not set (might be older Windows).")
        except Exception as e:
            logging.warning(f"Error setting DPI awareness: {e}") # 로깅 사용

    # Qt High DPI 설정
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    logging.info("Enabled Qt High DPI scaling attributes.")

    app = QApplication(sys.argv)

    # 애플리케이션 아이콘 설정
    try:
        icon_path = get_resource_path("icons/rubber_duck.ico") # 아이콘 경로 수정
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
            logging.info(f"Application icon set from: {icon_path}")
        else:
            logging.warning(f"Icon file not found at: {icon_path}") # 로깅 사용
    except Exception as e:
        logging.error(f"Error loading application icon: {e}", exc_info=True) # 로깅 사용

    db_service_instance = None # DB 서비스 인스턴스 변수
    try:
        # MainWindow 생성 전에 DB 서비스 초기화 및 로그 정리 시도
        # MainWindow 내부에서도 DBService를 초기화하므로, 여기서 생성된 인스턴스를
        # MainWindow에 전달하거나, MainWindow 내부에서 로그 정리를 호출해야 함.
        # 여기서는 로그 정리만 시도하고, MainWindow는 자체적으로 DBService를 생성하도록 둠.
        try:
            db_service_instance = DbService()
            cleanup_logs(db_service_instance)
        except (ConnectionError, ValueError) as db_init_err:
             # DB 연결 또는 설정 오류 시에도 일단 앱 실행 시도 (MainWindow에서 다시 처리)
             logging.error(f"Initial DB connection/cleanup failed: {db_init_err}. MainWindow will attempt connection.")
        except Exception as cleanup_err:
             logging.error(f"Error during initial log cleanup: {cleanup_err}")
        finally:
            # 로그 정리 후 연결 닫기 (MainWindow에서 새로 연결)
            if db_service_instance:
                db_service_instance.disconnect()
                logging.info("Initial DB connection for cleanup closed.")


        # MainWindow 생성 및 실행
        window = MainWindow(mode="Code Enhancer Prompt Builder")
        window.show()
        sys.exit(app.exec_())

    except (ConnectionError, ValueError) as e:
         # Catch DB connection or config load errors from MainWindow init
         logging.critical(f"Application initialization failed: {e}", exc_info=True)
         # GUI가 부분적으로 사용 가능할 때 간단한 메시지 박스 표시 (선택 사항)
         QMessageBox.critical(None, "치명적 오류", f"애플리케이션 시작 실패:\n{e}")
         sys.exit(1) # 오류 코드로 종료
    except SystemExit as e:
         # MainWindow 내부에서 DB/Config 오류로 SystemExit 호출 시
         logging.info(f"Application exited with code {e.code}")
         sys.exit(e.code)
    except Exception as e:
         logging.critical(f"An unexpected error occurred during application startup: {e}", exc_info=True)
         QMessageBox.critical(None, "예상치 못한 오류", f"애플리케이션 시작 중 오류 발생:\n{e}")
         sys.exit(1)

if __name__ == "__main__":
    main()
            