import os
from PyQt6.QtWidgets import QMessageBox # PyQt5 -> PyQt6

# 서비스 및 모델 import
from core.services.xml_service import XmlService

# MainWindow는 타입 힌트용으로만 사용
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow
    from .file_tree_controller import FileTreeController # refresh_tree 호출용

class XmlController:
    """
    Handles logic related to XML parsing and applying file changes.
    """
    def __init__(self, main_window: 'MainWindow', xml_service: XmlService):
        self.mw = main_window
        self.xml_service = xml_service
    def run_xml_parser(self):
        """Parses XML input and applies changes to the project files."""
        xml_str = ""
        if hasattr(self.mw, "xml_input_tab"):
            xml_str = self.mw.xml_input_tab.toPlainText()
        if not xml_str.strip():
            self.mw.status_bar.showMessage("XML 내용이 비어 있습니다.")
            return

        project_dir = self.mw.current_project_folder
        if not project_dir or not os.path.isdir(project_dir):
            QMessageBox.warning(self.mw, "경고", "프로젝트 폴더를 먼저 선택해주세요.")
            return

        try:
            result = self.xml_service.apply_changes_from_xml(xml_str, project_dir)
        except Exception as e:
             QMessageBox.critical(self.mw, "XML 파싱 오류", f"XML 처리 중 예외 발생: {e}")
             if hasattr(self.mw, 'file_tree_controller'):
                 self.mw.file_tree_controller.refresh_tree() # 오류 시에도 새로고침
             return

        messages = []
        if result["created"]: messages.append("생성된 파일:\n" + "\n".join(result["created"]))
        if result["updated"]: messages.append("수정된 파일:\n" + "\n".join(result["updated"]))
        if result["deleted"]: messages.append("삭제된 파일:\n" + "\n".join(result["deleted"]))
        if result["errors"]: messages.append("오류:\n" + "\n".join(result["errors"]))
        if not messages: messages.append("변경 사항 없음.")

        final_message = "\n\n".join(messages)

        if result["errors"]:
            QMessageBox.warning(self.mw, "XML 파싱 결과 (오류 발생)", final_message)
        else:
            QMessageBox.information(self.mw, "XML 파싱 결과", final_message)

        # 파일 변경 후 트리 새로고침 (FileTreeController 통해)
        if hasattr(self.mw, 'file_tree_controller'):
            self.mw.file_tree_controller.refresh_tree()
        self.mw.status_bar.showMessage("XML 파싱 완료!")
