
from PyQt6.QtWidgets import QTextEdit # PyQt5 -> PyQt6
from PyQt6.QtCore import QMimeData # PyQt5 -> PyQt6

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
