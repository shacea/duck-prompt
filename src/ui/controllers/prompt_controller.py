
import os
import logging # 로깅 추가
from PyQt6.QtWidgets import QMessageBox, QApplication # PyQt5 -> PyQt6

# 서비스 및 모델 import
from core.services.prompt_service import PromptService

# MainWindow는 타입 힌트용으로만 사용
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = logging.getLogger(__name__) # 로거 설정

class PromptController:
    """
    Handles logic related to prompt generation and clipboard operations.
    Token calculation is now triggered asynchronously by MainController.
    """
    def __init__(self, main_window: 'MainWindow', prompt_service: PromptService):
        self.mw = main_window
        self.prompt_service = prompt_service

    def generate_prompt(self):
        """Generates the prompt for the Code Enhancer mode and triggers token calculation."""
        if self.mw.mode == "Meta Prompt Builder":
            return self.generate_meta_prompt() # Meta 모드면 해당 함수 호출

        if not self.mw.current_project_folder:
             QMessageBox.warning(self.mw, "경고", "프로젝트 폴더를 먼저 선택해주세요.")
             return False

        checked_files = self.mw.checkable_proxy.get_checked_files() if hasattr(self.mw, 'checkable_proxy') else []
        if not checked_files:
            QMessageBox.warning(self.mw, "경고", "프롬프트에 포함할 파일을 하나 이상 선택해주세요.")
            return False

        file_contents = []
        self.mw.selected_files_data = []
        read_errors = []
        for fpath in checked_files:
            try:
                size = os.path.getsize(fpath)
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                file_contents.append((fpath, content))
                self.mw.selected_files_data.append((fpath, size))
            except Exception as e:
                error_msg = f"파일 읽기 오류 ({os.path.basename(fpath)}): {e}"
                logger.error(error_msg) # 로깅 사용
                read_errors.append(error_msg)
                continue

        if read_errors:
             QMessageBox.warning(self.mw, "파일 로딩 오류", "일부 파일을 읽는 중 오류 발생:\n" + "\n".join(read_errors))
             # return False # 오류 시 중단 원하면 주석 해제

        system_text = self.mw.system_tab.toPlainText()
        user_text = self.mw.user_tab.toPlainText()
        dir_structure_content = ""
        if self.mw.tree_generated and hasattr(self.mw, "dir_structure_tab"):
            dir_structure_content = self.mw.dir_structure_tab.toPlainText()

        # --- 첨부 파일 정보 로드 ---
        # generate_code_enhancer_prompt는 마커만 사용하므로 실제 데이터 로드는 불필요
        # 토큰 계산 시에는 실제 데이터가 필요하므로 MainController에서 처리
        attachments_metadata = []
        for item in self.mw.attached_items:
            meta_item = item.copy()
            meta_item.pop('data', None) # 데이터 제외하고 메타데이터만 전달
            attachments_metadata.append(meta_item)
        # -------------------------

        final_prompt = self.prompt_service.generate_code_enhancer_prompt(
            system_text=system_text,
            user_text=user_text,
            file_contents=file_contents,
            root_dir=self.mw.current_project_folder,
            dir_structure_content=dir_structure_content,
            attached_items=attachments_metadata # 메타데이터 전달
        )

        self.mw.last_generated_prompt = final_prompt
        self.mw.prompt_output_tab.setText(final_prompt)

        # --- Trigger token calculation asynchronously ---
        # Pass the final prompt text and the *original* attached_items list (which might contain data)
        self.mw.main_controller.calculate_and_display_tokens(final_prompt, self.mw.attached_items)
        # -----------------------------------------------

        self.mw.status_bar.showMessage(f"Prompt generated! Length: {len(final_prompt):,} chars. Token calculation started...")
        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)
        return True

    def generate_meta_prompt(self):
        """Generates the intermediate meta prompt and triggers token calculation."""
        system_text = self.mw.system_tab.toPlainText() # 메타 템플릿
        user_text = self.mw.user_tab.toPlainText() # 메타 사용자 입력

        final_output = self.prompt_service.generate_meta_prompt(
            meta_template=system_text,
            meta_user_input=user_text
        )

        self.mw.prompt_output_tab.setText(final_output) # 메타 프롬프트 출력 탭
        self.mw.last_generated_prompt = final_output

        # --- Trigger token calculation asynchronously ---
        self.mw.main_controller.calculate_and_display_tokens(final_output) # Meta mode has no attachments
        # -----------------------------------------------

        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)
        self.mw.status_bar.showMessage("META Prompt generated! Token calculation started...")
        return True

    def generate_final_meta_prompt(self):
        """Generates the final prompt by replacing variables and triggers token calculation."""
        meta_prompt_content = ""
        user_prompt_content = ""
        if hasattr(self.mw, 'meta_prompt_tab'):
             meta_prompt_content = self.mw.meta_prompt_tab.toPlainText()
        if hasattr(self.mw, 'user_prompt_tab'):
             user_prompt_content = self.mw.user_prompt_tab.toPlainText()

        variables = {}
        if hasattr(self.mw, 'build_tabs'):
            for i in range(self.mw.build_tabs.count()):
                tab_name = self.mw.build_tabs.tabText(i)
                if tab_name.startswith("var-"):
                    var_name = tab_name[4:]
                    tab_widget = self.mw.build_tabs.widget(i)
                    if tab_widget and hasattr(tab_widget, 'toPlainText'):
                        variables[var_name] = tab_widget.toPlainText()

        final_prompt = self.prompt_service.generate_final_meta_prompt(
            meta_prompt_content=meta_prompt_content,
            user_prompt_content=user_prompt_content,
            variables=variables
        )

        if hasattr(self.mw, 'final_prompt_tab'):
            self.mw.final_prompt_tab.setText(final_prompt)
            self.mw.last_generated_prompt = final_prompt

            # --- Trigger token calculation asynchronously ---
            self.mw.main_controller.calculate_and_display_tokens(final_prompt) # Meta mode has no attachments
            # -----------------------------------------------

            self.mw.build_tabs.setCurrentWidget(self.mw.final_prompt_tab)
            self.mw.status_bar.showMessage("Final Prompt generated! Token calculation started...")
        else:
             QMessageBox.warning(self.mw, "오류", "최종 프롬프트 탭을 찾을 수 없습니다.")

    def copy_to_clipboard(self):
        """Copies the content of the active prompt output tab to the clipboard."""
        current_widget = self.mw.build_tabs.currentWidget()
        prompt_to_copy = ""

        # Code Enhancer 모드의 프롬프트 출력 탭
        if current_widget == self.mw.prompt_output_tab and self.mw.mode != "Meta Prompt Builder":
            prompt_to_copy = self.mw.prompt_output_tab.toPlainText()
        # Meta 모드의 메타 프롬프트 출력 탭
        elif current_widget == self.mw.prompt_output_tab and self.mw.mode == "Meta Prompt Builder":
             prompt_to_copy = self.mw.prompt_output_tab.toPlainText()
        # Meta 모드의 최종 프롬프트 탭
        elif hasattr(self.mw, 'final_prompt_tab') and current_widget == self.mw.final_prompt_tab:
             prompt_to_copy = self.mw.final_prompt_tab.toPlainText()
        # 파일 트리 탭 (선택적)
        elif hasattr(self.mw, 'dir_structure_tab') and current_widget == self.mw.dir_structure_tab:
             prompt_to_copy = self.mw.dir_structure_tab.toPlainText()

        # 위 경우에 해당하지 않으면 마지막 생성된 프롬프트 사용 (last_generated_prompt)
        if not prompt_to_copy:
             prompt_to_copy = self.mw.last_generated_prompt

        if prompt_to_copy:
            QApplication.clipboard().setText(prompt_to_copy)
            self.mw.status_bar.showMessage("Copied!")
            return True
        else:
            self.mw.status_bar.showMessage("복사할 내용이 없습니다!")
            return False

    def generate_all_and_copy(self):
        """
        Generates directory tree, prompt, triggers token calculation, and copies to clipboard (Code Enhancer mode only).
        Returns True if prompt generation was successful, False otherwise.
        Clipboard copy failure only logs a warning but doesn't cause the function to return False.
        """
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 이 기능을 사용할 수 없습니다.")
            return False # 작업 수행 안 함

        # FileTreeController의 트리 생성 메서드 호출
        tree_success = self.mw.file_tree_controller.generate_directory_tree_structure()
        if not tree_success:
            logger.warning("generate_all_and_copy: Directory tree generation failed.")
            # 트리 생성 실패 시에도 프롬프트 생성은 시도할 수 있음 (선택 사항)
            # return False # 트리 생성 실패 시 즉시 중단하려면 주석 해제

        # 자신의 프롬프트 생성 메서드 호출 (내부에서 토큰 계산 트리거)
        prompt_success = self.generate_prompt() # This now triggers calculate_and_display_tokens
        if not prompt_success:
            logger.error("generate_all_and_copy: Prompt generation failed.")
            return False # 프롬프트 생성 실패 시 False 반환

        # 자신의 클립보드 복사 메서드 호출
        copy_success = self.copy_to_clipboard()
        if not copy_success:
            # 복사 실패는 경고만 로깅하고, 함수는 True 반환 (프롬프트 생성 성공 기준)
            logger.warning("generate_all_and_copy: Copy to clipboard failed, but prompt generation succeeded.")

        # 프롬프트 생성이 성공했으므로 True 반환
        # 상태 메시지는 generate_prompt에서 이미 설정됨 ("... Token calculation started...")
        return True
