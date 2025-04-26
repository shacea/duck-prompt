import logging
import os
from typing import Optional

# 애플리케이션 이름 전역 변수
_APP_NAME = "DuckPrompt"

# winotify import 시도
try:
    from winotify import Notification
    # winotify는 기본적으로 Windows에서만 작동합니다.
    _WINOTIFY_AVAILABLE = os.name == 'nt'
except ImportError:
    _WINOTIFY_AVAILABLE = False
    logging.warning("winotify library not found or OS is not Windows. Desktop notifications will be disabled.")

# helpers에서 아이콘 경로 함수 가져오기
from .helpers import get_resource_path

logger = logging.getLogger(__name__)

def show_notification(title: str, message: str, app_name: str = None, timeout: Optional[int] = None):
    """
    Displays a desktop notification using winotify (Windows only).

    Args:
        title: The title of the notification.
        message: The main message content of the notification.
        app_name: The name of the application sending the notification.
        timeout: Duration in seconds (winotify doesn't directly support timeout, Windows setting applies).
    """
    if not _WINOTIFY_AVAILABLE:
        logger.warning(f"Notification not shown (winotify unavailable or not Windows): Title='{title}', Message='{message[:50]}...'")
        return

    try:
        logger.info(f"Showing notification via winotify: Title='{title}', Message='{message[:50]}...'")

        # 아이콘 경로 가져오기
        icon_path = ""
        try:
            icon_path = get_resource_path("icons/rubber_duck.ico")
            if not os.path.exists(icon_path):
                logger.warning(f"Notification icon not found at: {icon_path}")
                icon_path = "" # 아이콘 경로 없으면 빈 문자열로 설정
        except Exception as e:
            logger.error(f"Error getting notification icon path: {e}")
            icon_path = ""

        # 애플리케이션 이름 설정
        notification_app_name = app_name if app_name else _APP_NAME

        # winotify Notification 객체 생성
        toast = Notification(
            app_id=notification_app_name,
            title=title,
            msg=message,
            icon=icon_path if icon_path else None  # 아이콘 경로 설정 (없으면 None)
        )

        # 알림 표시
        toast.show()
        logger.info("winotify notification shown successfully.")

    except Exception as e:
        logger.error(f"Failed to show winotify notification: {e}", exc_info=True)

# Example usage (for testing):
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Testing winotify notification...")
    if _WINOTIFY_AVAILABLE:
        show_notification("Test Notification", "This is a test message from notifications.py using winotify.")
        print("Notification test finished.")
    else:
        print("winotify is not available on this system (requires Windows and winotify library).")

