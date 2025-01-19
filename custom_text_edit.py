
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtCore import Qt

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def insertFromMimeData(self, source):
        # 오직 plain text 형태로만 붙여넣기
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)
