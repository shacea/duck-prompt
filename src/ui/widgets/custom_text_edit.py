from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import QMimeData

class CustomTextEdit(QTextEdit):
    """
    Custom QTextEdit that only allows plain text pasting.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def insertFromMimeData(self, source: QMimeData):
        """Overrides insertFromMimeData to paste only plain text."""
        if source.hasText():
            self.insertPlainText(source.text())