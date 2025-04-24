from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCharFormat, QColor, QMouseEvent # QMouseEvent 추가
from PyQt5.QtCore import Qt, QMimeData

class CustomTextEdit(QTextEdit):
    """
    Custom QTextEdit that only allows plain text pasting.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def insertFromMimeData(self, source: QMimeData):
        """Overrides insertFromMimeData to paste only plain text."""
        if source.hasText():
            # 붙여넣기 시 일반 텍스트로 삽입
            self.insertPlainText(source.text())
        # else:
            # 텍스트가 아닌 다른 형식(이미지 등)은 기본 동작 또는 무시
            # super().insertFromMimeData(source) # 다른 형식 붙여넣기 허용 시
            # pass # 다른 형식 무시 시

    # 선택적: 컨텍스트 메뉴 커스터마이징 (예: 서식 관련 액션 제거)
    # def contextMenuEvent(self, event: QMouseEvent):
    #     menu = self.createStandardContextMenu()
    #     # 서식 관련 액션 제거 로직 추가
    #     # ...
    #     menu.exec_(event.globalPos())
