
from PyQt6.QtWidgets import QTabBar, QTabWidget, QInputDialog, QMessageBox, QMainWindow # PyQt5 -> PyQt6
from PyQt6.QtCore import Qt # PyQt5 -> PyQt6
from PyQt6.QtGui import QMouseEvent # PyQt5 -> PyQt6
from .tab_manager import is_tab_deletable

class CustomTabBar(QTabBar):
    """
    Custom tab bar with features like adding new tabs, closing tabs with middle-click,
    and renaming tabs with double-click.
    """
    def __init__(self, parent: QTabWidget, main_window: QMainWindow):
        super().__init__(parent)
        self.main_window = main_window # MainWindow 참조 (새 탭 추가 시 필요)
        self.setTabsClosable(False) # 기본 닫기 버튼 숨김 (미들 클릭 사용)
        self.setMovable(True) # 탭 이동 가능
        # "+" 탭 추가 (새 탭 생성용)
        self.addTab("+")

    def mousePressEvent(self, event: QMouseEvent):
        """Handles left mouse button press for adding new tabs."""
        if event.button() == Qt.MouseButton.LeftButton: # Qt.LeftButton -> Qt.MouseButton.LeftButton
            pos = event.position().toPoint() # PyQt6: event.pos() -> event.position().toPoint()
            index = self.tabAt(pos)
            # "+" 탭 클릭 시 새 탭 추가 동작 연결
            if index >= 0 and self.tabText(index) == "+":
                # MainWindow의 메서드를 호출하여 새 탭 추가
                if hasattr(self.main_window, 'add_new_custom_tab'):
                    self.main_window.add_new_custom_tab()
                return # 이벤트 처리 완료
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handles middle mouse button release for closing tabs."""
        if event.button() == Qt.MouseButton.MiddleButton: # Qt.MiddleButton -> Qt.MouseButton.MiddleButton
            pos = event.position().toPoint() # PyQt6: event.pos() -> event.position().toPoint()
            index = self.tabAt(pos)
            if index >= 0:
                tab_text = self.tabText(index)
                if tab_text != "+" and is_tab_deletable(tab_text):
                    self.parentWidget().removeTab(index)
                elif tab_text != "+":
                    QMessageBox.warning(self.parentWidget(), "경고", f"'{tab_text}' 탭은 제거할 수 없습니다.")
                # "+" 탭은 아무 동작 안 함
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handles left mouse button double-click for renaming tabs."""
        if event.button() == Qt.MouseButton.LeftButton: # Qt.LeftButton -> Qt.MouseButton.LeftButton
            pos = event.position().toPoint() # PyQt6: event.pos() -> event.position().toPoint()
            index = self.tabAt(pos)
            if index >= 0:
                tab_text = self.tabText(index)
                # 보호된 탭 또는 "+" 탭은 이름 변경 불가
                if tab_text != "+" and is_tab_deletable(tab_text):
                    new_name, ok = QInputDialog.getText(self.parentWidget(), "탭 이름 변경",
                                                        "새 탭 이름을 입력하세요:", text=tab_text)
                    if ok and new_name and new_name.strip():
                        new_name_stripped = new_name.strip()
                        # 보호된 이름으로 변경 불가 처리
                        if not is_tab_deletable(new_name_stripped):
                             QMessageBox.warning(self.parentWidget(), "경고", f"'{new_name_stripped}'(으)로는 변경할 수 없습니다.")
                             return
                        # 중복 탭 이름 검사
                        for i in range(self.count()):
                            if i != index and self.tabText(i) == new_name_stripped:
                                QMessageBox.warning(self.parentWidget(), "경고", f"'{new_name_stripped}' 탭이 이미 존재합니다.")
                                return
                        # 이름 변경 적용
                        self.setTabText(index, new_name_stripped)
                    elif ok:
                         QMessageBox.warning(self.parentWidget(), "경고", "탭 이름은 비워둘 수 없습니다.")
        super().mouseDoubleClickEvent(event)

