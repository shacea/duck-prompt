from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtCore import Qt

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def insertFromMimeData(self, source):
        """Override insertFromMimeData to handle pasted text with custom formatting"""
        if source.hasHtml():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(Qt.black))

            cursor = self.textCursor()
            pos = cursor.position()

            # HTML 내용 삽입
            cursor.insertHtml(source.html())

            cursor.setPosition(pos)
            cursor.movePosition(cursor.NextCharacter, cursor.KeepAnchor, len(source.html()))
            cursor.mergeCharFormat(fmt)
            cursor.clearSelection()

            self.setTextCursor(cursor)
        else:
            super().insertFromMimeData(source)
