from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCharFormat, QColor
from PyQt5.QtCore import Qt

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def insertFromMimeData(self, source):
        """Override insertFromMimeData to handle pasted text with custom formatting"""
        if source.hasHtml():
            # Create a new text format with black color
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(Qt.black))
            
            # Get cursor and save its position
            cursor = self.textCursor()
            pos = cursor.position()
            
            # Insert the HTML content
            cursor.insertHtml(source.html())
            
            # Select the newly inserted text
            cursor.setPosition(pos)
            cursor.movePosition(cursor.End, cursor.KeepAnchor)
            
            # Apply black color to the selected text
            cursor.mergeCharFormat(fmt)
            
            # Clear the selection
            cursor.clearSelection()
            self.setTextCursor(cursor)
        else:
            # If the source doesn't have HTML, just insert plain text
            super().insertFromMimeData(source)
