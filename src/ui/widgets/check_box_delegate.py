
# src/ui/widgets/check_box_delegate.py
from PyQt6.QtCore import Qt, QEvent, QRect, QModelIndex, QAbstractItemModel
from PyQt6.QtWidgets import QStyledItemDelegate, QApplication, QStyleOptionViewItem, QWidget, QStyle
from PyQt6.QtGui import QMouseEvent
import logging

logger = logging.getLogger(__name__)

class CheckBoxDelegate(QStyledItemDelegate):
    """
    체크박스 영역을 클릭했을 때만 체크 상태 토글을 처리하는 Delegate
    """
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def editorEvent(self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """
        마우스 클릭 이벤트를 처리하여 체크박스 영역 클릭 시 모델 데이터를 업데이트합니다.
        """
        # 체크박스는 0번 컬럼에만 있으니, 그 외 컬럼은 기본 동작
        if index.column() != 0:
            return super().editorEvent(event, model, option, index)

        # 마우스 릴리즈 이벤트이고, 왼쪽 버튼일 때만 반응
        if event.type() == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
            # 체크박스 사각영역 계산
            style = QApplication.style() if self.parent() is None else self.parent().style()
            cb_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator, option, self.parent())

            # 마우스 클릭 위치가 체크박스 내부라면
            if cb_rect.contains(event.position().toPoint()):
                current_value = model.data(index, Qt.ItemDataRole.CheckStateRole)
                # PyQt6에서는 data()가 CheckState enum 값을 직접 반환할 수 있음
                if isinstance(current_value, Qt.CheckState):
                    current_state = current_value
                elif isinstance(current_value, int): # Fallback for integer representation
                    current_state = Qt.CheckState(current_value)
                else: # 예상치 못한 타입이면 처리 중단
                    logger.warning(f"Unexpected data type for CheckStateRole: {type(current_value)}")
                    return False

                # 체크 상태 토글
                new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked

                # 모델 데이터 변경 시도 및 결과 로깅
                logger.debug(f"CheckBoxDelegate: Attempting setData for index {index.row()},{index.column()} with state {new_state}")
                success = model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
                logger.debug(f"CheckBoxDelegate: setData call result: {success}")

                # setData가 성공적으로 모델 데이터를 변경했으면 True 반환
                if success:
                    return True # 이벤트 처리 완료, 다른 핸들러 호출 방지
                else:
                    # setData 실패 시 로그 남기고 기본 처리로 넘어감
                    logger.warning(f"CheckBoxDelegate: setData failed for index {index.row()},{index.column()}")
                    return False # setData 실패 시 False 반환

        # 다른 이벤트는 기본 처리
        return super().editorEvent(event, model, option, index)

    # paint 메서드는 기본 QStyledItemDelegate의 동작을 사용하므로 오버라이드 불필요
    # def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
    #     super().paint(painter, option, index)

