import os
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QApplication

# 서비스 및 모델 import
from core.services.config_service import ConfigService
from core.services.state_service import StateService
from core.services.template_service import TemplateService
from core.services.prompt_service import PromptService
from core.services.xml_service import XmlService
from core.services.filesystem_service import FilesystemService
from core.pydantic_models.app_state import AppState
from utils.helpers import calculate_char_count, calculate_token_count

# MainWindow는 타입 힌트용으로만 사용 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow
    # 하위 컨트롤러 타입 힌트 (선택적)
    from .resource_controller import ResourceController
    from .prompt_controller import PromptController
    from .xml_controller import XmlController
    from .file_tree_controller import FileTreeController


class MainController:
    """
    메인 컨트롤러는 애플리케이션의 전반적인 흐름과
    다른 컨트롤러 간의 조정 역할을 담당 (필요한 경우).
    주요 기능 로직은 각 전문 컨트롤러에 위임.
    """
    def __init__(self, main_window: 'MainWindow'):
        self.mw = main_window # MainWindow 인스턴스
        # 서비스는 MainWindow에서 생성되어 각 컨트롤러에 주입됨
        # 하위 컨트롤러 참조는 MainWindow를 통해 접근 (예: self.mw.resource_controller)

    def reset_program(self):
        """Resets the application to its initial state."""
        # UI 초기화 (MainWindow 메서드 호출)
        self.mw.reset_state()
        self.mw.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
        self.mw.system_tab.clear()
        self.mw.user_tab.clear()
        if hasattr(self.mw, "dir_structure_tab"): self.mw.dir_structure_tab.clear()
        if hasattr(self.mw, "xml_input_tab"): self.mw.xml_input_tab.clear()
        if hasattr(self.mw, "prompt_output_tab"): self.mw.prompt_output_tab.clear()
        self.mw.gitignore_edit.clear()
        # self.mw.tree_generated = False # MainWindow의 reset_state에서 처리

        # 설정 및 필터 초기화 (FileTreeController에게 위임)
        self.mw.file_tree_controller.reset_gitignore_and_filter()

        # 파일 탐색기 트리 리셋 (FileTreeController에게 위임)
        self.mw.file_tree_controller.reset_file_tree()

        # 윈도우 제목 리셋
        self.mw.update_window_title()
        self.mw.status_bar.showMessage("프로그램 리셋 완료.")
        QMessageBox.information(self.mw, "Info", "프로그램이 초기 상태로 리셋되었습니다.")

    def update_counts_for_text(self, text: str):
        """Updates character and token counts in the status bar."""
        char_count = calculate_char_count(text)
        token_count = None
        token_text = "토큰 계산: 비활성화"

        if self.mw.auto_token_calc_check.isChecked():
            token_count = calculate_token_count(text)
            if token_count is not None:
                 token_text = f"Calculated Total Token: {token_count:,}"
            else:
                 token_text = "토큰 계산 오류"

        self.mw.char_count_label.setText(f"Chars: {char_count:,}")
        self.mw.token_count_label.setText(token_text)

    def update_active_tab_counts(self):
        """Updates the counts based on the currently active text edit tab."""
        current_widget = self.mw.build_tabs.currentWidget()
        if hasattr(current_widget, 'toPlainText'):
            self.update_counts_for_text(current_widget.toPlainText())
        else:
            # 현재 탭이 텍스트 편집기가 아니면 카운트 초기화 또는 유지
            self.mw.char_count_label.setText("Chars: 0")
            self.mw.token_count_label.setText("토큰 계산: -")


    # on_mode_changed는 MainWindow에서 처리 (_toggle_mode -> _restart_with_mode)

    # 참고: 이전 MainController의 다른 메서드들은
    # ResourceController, PromptController, XmlController, FileTreeController로 이동되었습니다.
