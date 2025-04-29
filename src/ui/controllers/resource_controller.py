
import os
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QTreeWidgetItem # PyQt5 -> PyQt6, QTreeWidgetItem 추가

# 서비스 및 모델 import
from core.services.template_service import TemplateService
from core.services.state_service import StateService
from core.pydantic_models.app_state import AppState

# MainWindow는 타입 힌트용으로만 사용
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow

class ResourceController:
    """
    Handles logic related to resource management (templates and states).
    """
    def __init__(self, main_window: 'MainWindow', template_service: TemplateService, state_service: StateService):
        self.mw = main_window
        self.template_service = template_service
        self.state_service = state_service

    def load_templates_list(self):
        """Loads the list of templates or states into the resource tree."""
        self.mw.template_tree.clear() # 트리 초기화
        current_mode = self.mw.resource_mode_combo.currentText()

        if current_mode == "프롬프트":
            system_templates = self.template_service.list_templates("prompts/system")
            user_templates = self.template_service.list_templates("prompts/user")

            system_item = self.mw.create_tree_item("System")
            user_item = self.mw.create_tree_item("User")
            for st in sorted(system_templates): self.mw.create_tree_item(st, system_item)
            for ut in sorted(user_templates): self.mw.create_tree_item(ut, user_item)
            system_item.setExpanded(True)
            user_item.setExpanded(True)

        elif current_mode == "상태":
            states_list = self.state_service.list_states()
            states_item = self.mw.create_tree_item("States")
            for st_file in sorted(states_list): self.mw.create_tree_item(st_file, states_item)
            states_item.setExpanded(True)

        self.update_buttons_label() # 버튼 레이블 업데이트

    def load_selected_item(self):
        """Loads the selected template or state."""
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", f"{current_mode} 파일을 선택해주세요.")
            return

        filename = item.text(0)

        if current_mode == "프롬프트":
            parent_text = item.parent().text(0)
            relative_path = ""
            target_tab = None
            if parent_text == "System":
                relative_path = os.path.join("prompts", "system", filename)
                target_tab = self.mw.system_tab
            elif parent_text == "User":
                relative_path = os.path.join("prompts", "user", filename)
                target_tab = self.mw.user_tab

            if relative_path and target_tab:
                content = self.template_service.load_template(relative_path)
                target_tab.setText(content)
                self.mw.status_bar.showMessage(f"Loaded {parent_text.lower()} template: {filename}")

        elif current_mode == "상태":
            fname_no_ext = os.path.splitext(filename)[0]
            loaded_state = self.state_service.load_state(fname_no_ext)
            if loaded_state:
                # 상태 로드 시 전체 로드로 간주 (partial_load=False)
                self.mw.set_current_state(loaded_state, partial_load=False)
            else:
                QMessageBox.warning(self.mw, "오류", "상태 파일을 불러오는 데 실패했습니다.")

    def save_current_as_item(self):
        """Saves the current prompt or state as a new item."""
        current_mode = self.mw.resource_mode_combo.currentText()

        if current_mode == "프롬프트":
            template_type = self.mw.template_type_combo.currentText()
            content = ""
            target_dir_relative = ""
            source_tab = None
            if template_type == "시스템":
                source_tab = self.mw.system_tab
                target_dir_relative = os.path.join("prompts", "system")
            else: # 사용자
                source_tab = self.mw.user_tab
                target_dir_relative = os.path.join("prompts", "user")

            content = source_tab.toPlainText()
            if not content.strip():
                 QMessageBox.warning(self.mw, "경고", "저장할 내용이 없습니다.")
                 return

            fname, ok = QInputDialog.getText(self.mw, "템플릿 저장", "템플릿 파일 이름(확장자 제외)을 입력하세요:")
            if not ok or not fname or not fname.strip(): return
            fname_stripped = fname.strip()
            fname_md = fname_stripped + ".md"
            relative_path = os.path.join(target_dir_relative, fname_md)

            if self.template_service.save_template(relative_path, content):
                self.mw.status_bar.showMessage(f"Template saved: {fname_md}")
                self.load_templates_list()
            else:
                 QMessageBox.warning(self.mw, "오류", "템플릿 저장 중 오류가 발생했습니다.")

        elif current_mode == "상태":
            current_state = self.mw.get_current_state()
            fname, ok = QInputDialog.getText(self.mw, "상태 저장", "상태 파일 이름(확장자 제외)을 입력하세요:")
            if not ok or not fname or not fname.strip(): return
            fname_stripped = fname.strip()

            if self.state_service.save_state(current_state, fname_stripped):
                self.mw.status_bar.showMessage(f"State saved: {fname_stripped}.json")
                self.load_templates_list()
            else:
                QMessageBox.warning(self.mw, "오류", "상태 저장 중 오류가 발생했습니다.")

    def delete_selected_item(self):
        """Deletes the selected template or state file."""
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", f"{current_mode} 파일을 선택해주세요.")
            return

        filename = item.text(0)
        parent_text = item.parent().text(0)

        reply = QMessageBox.question(self.mw, "삭제 확인", f"정말로 '{filename}'을(를) 삭제하시겠습니까?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) # QMessageBox.Yes/No -> QMessageBox.StandardButton.Yes/No
        if reply != QMessageBox.StandardButton.Yes: return # QMessageBox.Yes -> QMessageBox.StandardButton.Yes

        deleted = False
        if current_mode == "프롬프트":
            relative_path = ""
            if parent_text == "System":
                relative_path = os.path.join("prompts", "system", filename)
            elif parent_text == "User":
                relative_path = os.path.join("prompts", "user", filename)
            if relative_path:
                deleted = self.template_service.delete_template(relative_path)
        elif current_mode == "상태":
            fname_no_ext = os.path.splitext(filename)[0]
            deleted = self.state_service.delete_state(fname_no_ext)

        if deleted:
            self.mw.status_bar.showMessage(f"Deleted: {filename}")
            self.load_templates_list()
        else:
            QMessageBox.warning(self.mw, "오류", f"'{filename}' 삭제 중 오류가 발생했습니다.")

    def update_current_item(self):
        """Updates the selected template or state file with the current content/state."""
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", f"{current_mode} 파일을 선택해주세요.")
            return

        filename = item.text(0)
        parent_text = item.parent().text(0)

        reply = QMessageBox.question(self.mw, "업데이트 확인", f"'{filename}'의 내용을 현재 편집 중인 내용으로 덮어쓰시겠습니까?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes) # QMessageBox.Yes/No -> QMessageBox.StandardButton.Yes/No
        if reply != QMessageBox.StandardButton.Yes: return # QMessageBox.Yes -> QMessageBox.StandardButton.Yes

        updated = False
        if current_mode == "프롬프트":
            content = ""
            relative_path = ""
            source_tab = None
            if parent_text == "System":
                source_tab = self.mw.system_tab
                relative_path = os.path.join("prompts", "system", filename)
            elif parent_text == "User":
                source_tab = self.mw.user_tab
                relative_path = os.path.join("prompts", "user", filename)

            if relative_path and source_tab:
                content = source_tab.toPlainText()
                updated = self.template_service.save_template(relative_path, content)
        elif current_mode == "상태":
            current_state = self.mw.get_current_state()
            fname_no_ext = os.path.splitext(filename)[0]
            updated = self.state_service.save_state(current_state, fname_no_ext)

        if updated:
            self.mw.status_bar.showMessage(f"Updated: {filename}")
        else:
            QMessageBox.warning(self.mw, "오류", f"'{filename}' 업데이트 중 오류가 발생했습니다.")

    def save_state_to_default(self):
        """Saves the current state to the default state file ('default.json')."""
        state = self.mw.get_current_state()
        if self.state_service.save_state(state, "default"):
            self.mw.status_bar.showMessage("현재 작업 자동 저장 완료!")
        else:
            # 자동 저장은 사용자에게 오류 메시지를 띄우지 않음 (로그로 대체 가능)
            print("Error: Failed to auto-save state to default.json")
            # QMessageBox.warning(self.mw, "오류", "기본 상태 저장 중 오류가 발생했습니다.")

    def load_state_from_default(self):
        """
        Loads the state from the default state file ('default.json').
        Uses partial_load=True to only load specific fields.
        """
        state = self.state_service.load_state("default")
        if state:
            # 부분 로드 플래그를 True로 설정하여 set_current_state 호출
            self.mw.set_current_state(state, partial_load=True)
        else:
             # 파일이 없거나 로드 실패 시 사용자에게 알림 (최초 실행 등)
             QMessageBox.information(self.mw, "정보", "저장된 이전 작업 상태 파일을 찾을 수 없습니다.")

    def export_state_to_file(self):
        """Exports the current state to a user-selected file."""
        path, _ = QFileDialog.getSaveFileName(self.mw, "상태 내보내기", os.path.expanduser("~"), "JSON Files (*.json)")
        if path:
            state = self.mw.get_current_state()
            if self.state_service.export_state_to_file(state, path):
                self.mw.status_bar.showMessage("상태 내보내기 완료!")
            else:
                QMessageBox.warning(self.mw, "오류", "상태 내보내기 중 오류가 발생했습니다.")

    def import_state_from_file(self):
        """Imports state from a user-selected file."""
        path, _ = QFileDialog.getOpenFileName(self.mw, "상태 가져오기", os.path.expanduser("~"), "JSON Files (*.json)")
        if path:
            state = self.state_service.import_state_from_file(path)
            if state:
                # 상태 가져오기는 전체 로드로 간주 (partial_load=False)
                self.mw.set_current_state(state, partial_load=False)
            else:
                 QMessageBox.warning(self.mw, "오류", "상태 가져오기 중 오류가 발생했거나 파일 내용이 유효하지 않습니다.")

    # 백업/복원 관련 메서드 제거
    # def backup_all_states_action(self): ...
    # def restore_states_from_backup_action(self): ...

    def update_buttons_label(self):
        """Updates the labels of buttons in the resource manager section based on the mode."""
        current_mode = self.mw.resource_mode_combo.currentText()
        is_prompt_mode = (current_mode == "프롬프트")

        self.mw.load_selected_template_btn.setText(f"📥 선택한 {current_mode} 불러오기")
        self.mw.save_as_template_btn.setText(f"💾 현재 {current_mode}로 저장")
        self.mw.delete_template_btn.setText(f"❌ 선택한 {current_mode} 삭제")
        self.mw.update_template_btn.setText(f"🔄 현재 {current_mode} 업데이트")

        # 백업/복원 버튼 관련 코드 제거
        # self.mw.backup_button.setEnabled(not is_prompt_mode)
        # self.mw.restore_button.setEnabled(not is_prompt_mode)
        # self.mw.backup_button.setText("📦 모든 상태 백업" + (" (비활성화)" if is_prompt_mode else ""))
        # self.mw.restore_button.setText("🔙 백업에서 상태 복원" + (" (비활성화)" if is_prompt_mode else ""))

        self.mw.template_type_combo.setVisible(is_prompt_mode)
        self.mw.template_type_label.setVisible(is_prompt_mode)

