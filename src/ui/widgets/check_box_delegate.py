
# src/ui/widgets/check_box_delegate.py
from PyQt6.QtCore import Qt, QEvent, QRect, QModelIndex, QAbstractItemModel # PyQt5 -> PyQt6
from PyQt6.QtWidgets import QStyledItemDelegate, QApplication, QStyleOptionViewItem, QWidget, QStyle # PyQt5 -> PyQt6, QStyle 추가
from PyQt6.QtGui import QMouseEvent # PyQt5 -> PyQt6

class CheckBoxDelegate(QStyledItemDelegate):
    """
    체크박스 영역을 클릭했을 때만 체크 상태 토글을 처리하는 Delegate
    """
    def __init__(self, parent: QWidget = None): # 부모 위젯 받도록 수정
        super().__init__(parent)

    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool: # 타입 힌트 명시
        """
        마우스 클릭 이벤트를 처리하여 체크박스 영역 클릭 시 모델 데이터를 업데이트합니다.
        """
        # 체크박스는 0번 컬럼에만 있으니, 그 외 컬럼은 기본 동작
        if index.column() != 0:
            return super().editorEvent(event, model, option, index)

        # 마우스 릴리즈 이벤트이고, 왼쪽 버튼일 때만 반응 (QMouseEvent 타입 확인)
        if event.type() == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton: # QEvent.MouseButtonRelease -> QEvent.Type.MouseButtonRelease, Qt.LeftButton -> Qt.MouseButton.LeftButton
            # 체크박스 사각영역 계산 (스타일마다 다를 수 있음)
            style = QApplication.style()
            # QStyleOptionViewItem 객체를 직접 전달하고, delegate의 parent()를 widget으로 전달
            cb_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator, option, self.parent()) # QStyle.SE_ItemViewItemCheckIndicator -> QStyle.SubElement.SE_ItemViewItemCheckIndicator

            # 마우스 클릭 위치가 체크박스 내부라면
            if cb_rect.contains(event.pos()):
                current = model.data(index, Qt.ItemDataRole.CheckStateRole) # Qt.CheckStateRole -> Qt.ItemDataRole.CheckStateRole
                # None 상태 처리 추가 (PartiallyChecked 등)
                if current == Qt.CheckState.Checked: # Qt.Checked -> Qt.CheckState.Checked
                    new_state = Qt.CheckState.Unchecked # Qt.Unchecked -> Qt.CheckState.Unchecked
                else: # Unchecked 또는 PartiallyChecked -> Checked
                    new_state = Qt.CheckState.Checked # Qt.Checked -> Qt.CheckState.Checked

                # 모델 데이터 변경 (setData 호출)
                # CheckableProxyModel의 setData가 호출되어야 함
                if model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole): # Qt.CheckStateRole -> Qt.ItemDataRole.CheckStateRole
                    return True # 이벤트 처리 완료, 다른 핸들러 호출 방지

        # 다른 이벤트는 기본 처리
        return super().editorEvent(event, model, option, index)

