from PyQt6.QtWidgets import QTreeView, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent

class FileTreeView(QTreeView):
    """
    마우스 드래그로 여러 파일 선택 시 핸들링하여
    선택된 모든 파일의 체크 상태를 토글합니다.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_pos = None
        self._dragging = False

    def mousePressEvent(self, event):
        if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos:
            distance = (event.pos() - self._drag_start_pos).manhattanLength()
            if distance > QApplication.startDragDistance():
                self._dragging = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton and self._dragging:
            # 드래그로 선택된 후 마우스 릴리즈 시 선택된 모든 파일 토글
            super().mouseReleaseEvent(event)
            indexes = self.selectionModel().selectedIndexes()
            # 0번 컬럼만 필터링
            col0_indexes = []
            rows = set()
            for idx in indexes:
                if idx.column() == 0 and idx.row() not in rows:
                    col0_indexes.append(idx)
                    rows.add(idx.row())
            if col0_indexes:
                first_state = self.model().data(col0_indexes[0], Qt.ItemDataRole.CheckStateRole)
                if isinstance(first_state, Qt.CheckState):
                    current_state = first_state
                elif isinstance(first_state, int):
                    current_state = Qt.CheckState(first_state)
                else:
                    return
                target_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                for idx in col0_indexes:
                    self.model().setData(idx, target_state, Qt.ItemDataRole.CheckStateRole)
            self._drag_start_pos = None
            self._dragging = False
        else:
            super().mouseReleaseEvent(event) 