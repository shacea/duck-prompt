from PyQt5.QtWidgets import QTabBar, QTabWidget, QInputDialog, QMessageBox, QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent

# 변경된 경로에서 import (필요시)
# from .tab_manager import is_tab_deletable # tab_manager도 widgets로 이동 가정

# 임시: tab_manager 임포트 경로 수정
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
        # "+" 탭은 닫거나 이동할 수 없도록 설정 (선택적)
        # self.setTabButton(self.count() - 1, QTabBar.RightSide, None) # 닫기 버튼 제거
        # self.setMovable(False) # "+" 탭 이동 불가

    def mousePressEvent(self, event: QMouseEvent):
        """Handles left mouse button press for adding new tabs."""
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            index = self.tabAt(pos)
            # "+" 탭 클릭 시 새 탭 추가 동작 연결
            if index >= 0 and self.tabText(index) == "+":
                # MainWindow의 메서드를 호출하여 새 탭 추가
                if hasattr(self.main_window, 'add_new_custom_tab'):
                    self.main_window.add_new_custom_tab()
                return # 이벤트 처리 완료
        super().mousePressEvent(event) # 다른 버튼이나 영역 클릭 시 기본 동작 수행

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handles middle mouse button release for closing tabs."""
        if event.button() == Qt.MiddleButton:
            pos = event.pos()
            index = self.tabAt(pos)
            if index >= 0:
                tab_text = self.tabText(index)
                # 보호된 탭 또는 "+" 탭은 닫지 않음
                if tab_text != "+" and is_tab_deletable(tab_text):
                    # 닫기 전 확인 (선택적)
                    # reply = QMessageBox.question(self.parentWidget(), "탭 닫기 확인",
                    #                              f"'{tab_text}' 탭을 닫으시겠습니까?",
                    #                              QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    # if reply == QMessageBox.Yes:
                    self.parentWidget().removeTab(index) # QTabWidget에서 탭 제거
                elif tab_text != "+": # 보호된 탭 클릭 시 경고
                    QMessageBox.warning(self.parentWidget(), "경고", f"'{tab_text}' 탭은 제거할 수 없습니다.")
                # "+" 탭은 아무 동작 안 함
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handles left mouse button double-click for renaming tabs."""
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            index = self.tabAt(pos)
            if index >= 0:
                tab_text = self.tabText(index)
                # 보호된 탭 또는 "+" 탭은 이름 변경 불가
                if tab_text != "+" and is_tab_deletable(tab_text):
                    new_name, ok = QInputDialog.getText(self.parentWidget(), "탭 이름 변경",
                                                        "새 탭 이름을 입력하세요:", text=tab_text)
                    if ok and new_name and new_name.strip():
                        # TODO: 중복 탭 이름 검사 추가
                        # TODO: 보호된 이름으로 변경 불가 처리
                        new_name_stripped = new_name.strip()
                        if not is_tab_deletable(new_name_stripped):
                             QMessageBox.warning(self.parentWidget(), "경고", f"'{new_name_stripped}'(으)로는 변경할 수 없습니다.")
                             return
                        self.setTabText(index, new_name_stripped)
                    elif ok:
                         QMessageBox.warning(self.parentWidget(), "경고", "탭 이름은 비워둘 수 없습니다.")
                # "+" 탭 또는 보호된 탭은 아무 동작 안 함
        super().mouseDoubleClickEvent(event)
