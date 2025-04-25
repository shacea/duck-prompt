

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
from core.services.token_service import TokenCalculationService # Added
from core.pydantic_models.app_state import AppState
from utils.helpers import calculate_char_count # Removed calculate_token_count

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
        self.token_service: TokenCalculationService = self.mw.token_service # Get service from MainWindow
        self.config_service: ConfigService = self.mw.config_service # Get service from MainWindow
        self.last_token_count: Optional[int] = None # 마지막 계산된 토큰 수 저장

    def reset_program(self):
        """Resets the application to its initial state."""
        self.mw._initialized = False # 리셋 시작 시 플래그 해제

        # UI 초기화 (MainWindow 메서드 호출)
        self.mw.reset_state() # reset_state 내부에서 _initialized=True 설정됨
        self.mw._initialized = False # reset_state 후 다시 False로 설정

        self.mw.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
        self.mw.system_tab.clear()
        self.mw.user_tab.clear()
        if hasattr(self.mw, "dir_structure_tab"): self.mw.dir_structure_tab.clear()
        if hasattr(self.mw, "xml_input_tab"): self.mw.xml_input_tab.clear()
        if hasattr(self.mw, "prompt_output_tab"): self.mw.prompt_output_tab.clear()
        # self.mw.gitignore_edit.clear() # gitignore 편집기는 설정 다이얼로그로 이동

        # 설정 및 필터 초기화 (FileTreeController에게 위임)
        self.mw.file_tree_controller.reset_gitignore_and_filter()

        # 파일 탐색기 트리 리셋 (FileTreeController에게 위임)
        self.mw.file_tree_controller.reset_file_tree()

        # 모델 선택 UI 초기화
        self.mw.llm_combo.setCurrentIndex(self.mw.llm_combo.findText("Gemini")) # 기본값 Gemini
        self.on_llm_selected() # 모델명 콤보박스 업데이트 (토큰 계산은 안 함)

        # 리셋 후에는 텍스트가 비어있으므로 update_active_tab_counts 호출해도 계산 안 함
        self.update_char_count_for_active_tab() # 문자 수만 업데이트
        self.reset_token_label() # 토큰 카운트 리셋

        # 윈도우 제목 리셋
        self.mw.update_window_title()
        self.mw.status_bar.showMessage("프로그램 리셋 완료.")

        self.mw._initialized = True # 리셋 완료 후 플래그 설정
        QMessageBox.information(self.mw, "Info", "프로그램이 초기 상태로 리셋되었습니다.")

    def update_char_count(self, text: str):
        """Updates character count in the status bar."""
        char_count = calculate_char_count(text)
        self.mw.char_count_label.setText(f"Chars: {char_count:,}")

    def update_char_count_for_active_tab(self):
        """Updates the character count based on the currently active text edit tab."""
        current_widget = self.mw.build_tabs.currentWidget()
        if hasattr(current_widget, 'toPlainText'):
            self.update_char_count(current_widget.toPlainText())
            # 토큰 레이블 리셋은 별도 함수로 분리
            # self.reset_token_label() # 여기서 리셋하지 않음
        else:
            # 현재 탭이 텍스트 편집기가 아니면 카운트 초기화
            self.mw.char_count_label.setText("Chars: 0")
            # self.reset_token_label() # 여기서 리셋하지 않음

    def reset_token_label(self):
        """Resets the token count label to its default state."""
        # _initialized 체크 추가: 초기화 중이 아닐 때만 리셋
        if hasattr(self.mw, '_initialized') and self.mw._initialized:
            self.mw.token_count_label.setText("토큰 계산: -")
            self.last_token_count = None # 마지막 계산 값도 초기화

    def handle_text_changed(self):
        """Handles text changes in editors: updates char count and resets token label."""
        self.update_char_count_for_active_tab()
        self.reset_token_label() # 텍스트 변경 시 토큰 레이블 리셋

    def calculate_and_display_tokens(self, text: str):
        """Calculates tokens for the given text and updates the status bar. Called on button click."""
        # 초기화 중이거나 MainWindow가 없으면 실행하지 않음
        if not hasattr(self.mw, '_initialized') or not self.mw._initialized:
            print("Token calculation skipped: MainWindow not initialized.")
            self.reset_token_label() # 초기 상태 표시
            return

        char_count = calculate_char_count(text)
        self.mw.char_count_label.setText(f"Chars: {char_count:,}")

        token_count = None
        token_text = "토큰 계산: -" # 기본 메시지
        self.last_token_count = None # 계산 시작 전 초기화

        # 텍스트가 비어 있으면 계산하지 않음
        if not text:
            print("Token calculation skipped: Text is empty.")
            self.mw.token_count_label.setText(token_text)
            return

        selected_llm = self.mw.llm_combo.currentText()
        # model_name = self.mw.model_name_input.text().strip() # QLineEdit 대신 QComboBox 사용
        model_name = self.mw.model_name_combo.currentText().strip() # QComboBox 사용

        if not model_name:
            token_text = f"{selected_llm} 모델명을 선택하거나 입력하세요."
            print("Token calculation skipped: Model name is empty.")
            self.mw.token_count_label.setText(token_text)
            return

        # 계산 중 메시지 표시
        token_text = f"{selected_llm} 토큰 계산 중..."
        self.mw.token_count_label.setText(token_text)
        QApplication.processEvents() # Allow UI update

        print(f"Calling token_service.calculate_tokens for {selected_llm}, {model_name}...")
        token_count = self.token_service.calculate_tokens(selected_llm, model_name, text)
        print(f"Token calculation result: {token_count}") # 디버깅 로그 추가

        if token_count is not None:
            token_text = f"Calculated Total Token ({selected_llm}): {token_count:,}"
            self.last_token_count = token_count # 성공 시 값 저장
        else:
            token_text = f"{selected_llm} 토큰 계산 오류"
            print(f"Token calculation failed for {selected_llm}, {model_name}.") # 실패 로그 추가

        print(f"Updating token label to: {token_text}") # 최종 업데이트 전 로그 추가
        self.mw.token_count_label.setText(token_text)
        QApplication.processEvents() # Ensure the label update is processed


    def on_llm_selected(self):
        """Handles the selection change in the LLM dropdown. Updates model name combo box, resets token label, and updates Gemini param visibility."""
        selected_llm = self.mw.llm_combo.currentText()

        # Load available models for the selected LLM
        available_models = self.config_service.get_available_models(selected_llm)

        # Update the model name combo box
        self.mw.model_name_combo.blockSignals(True) # Prevent triggering signals during update
        self.mw.model_name_combo.clear()
        self.mw.model_name_combo.addItems(available_models)
        self.mw.model_name_combo.blockSignals(False)

        # Load the default model name for the selected LLM from config
        default_model = self.config_service.get_default_model_name(selected_llm)

        # Set the default model in the combo box
        default_index = self.mw.model_name_combo.findText(default_model)
        if default_index != -1:
            self.mw.model_name_combo.setCurrentIndex(default_index)
        elif available_models: # If default not found, select the first available model
            self.mw.model_name_combo.setCurrentIndex(0)
            print(f"Warning: Default model '{default_model}' not found in available list for {selected_llm}. Selecting first available.")
        else: # No models available
             print(f"Warning: No available models found for {selected_llm} in config.")


        # Reset token count label
        self.reset_token_label()
        # Update character count for the active tab
        self.update_char_count_for_active_tab()

        # Update visibility of Gemini parameter widgets
        is_gemini_selected = (selected_llm == "Gemini")
        if hasattr(self.mw, 'gemini_param_widget'):
            self.mw.gemini_param_widget.setVisible(is_gemini_selected)


    # on_mode_changed는 MainWindow에서 처리 (_toggle_mode -> _restart_with_mode)

    # 참고: 이전 MainController의 다른 메서드들은
    # ResourceController, PromptController, XmlController, FileTreeController로 이동되었습니다.
