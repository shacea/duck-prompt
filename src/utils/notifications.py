
import logging
from typing import Optional

# plyer import 시도
try:
    from plyer import notification
    _PLYER_AVAILABLE = True
except ImportError:
    _PLYER_AVAILABLE = False
    logging.warning("plyer library not found. Desktop notifications will be disabled.")
    # notification 객체를 모의(mock) 객체나 None으로 설정하여 AttributeError 방지
    class MockNotification:
        def notify(self, *args, **kwargs):
            logging.warning("Notification skipped: plyer library not available.")
    notification = MockNotification()

logger = logging.getLogger(__name__)

def show_notification(title: str, message: str, app_name: str = "DuckPrompt", timeout: int = 10):
    """
    Displays a desktop notification.

    Args:
        title: The title of the notification.
        message: The main message content of the notification.
        app_name: The name of the application sending the notification.
        timeout: Duration in seconds for which the notification should be displayed (if supported by the backend).
    """
    if not _PLYER_AVAILABLE:
        logger.warning(f"Notification not shown (plyer unavailable): Title='{title}', Message='{message[:50]}...'")
        return

    try:
        logger.info(f"Showing notification: Title='{title}', Message='{message[:50]}...'")
        notification.notify(
            title=title,
            message=message,
            app_name=app_name,
            timeout=timeout,
            # ticker="New message", # Optional: Ticker text for some systems
            # app_icon=None, # Optional: Path to an icon file (.ico on Windows)
        )
    except Exception as e:
        logger.error(f"Failed to show notification: {e}", exc_info=True)

# Example usage (for testing):
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Testing notification...")
    show_notification("Test Notification", "This is a test message from notifications.py.")
    print("Notification test finished.")
    if not _PLYER_AVAILABLE:
        print("Note: plyer is not installed, so the notification was likely skipped.")

