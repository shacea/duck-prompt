
import os
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QTreeWidgetItem
from prompt_manager import generate_final_prompt
from config import config
import parse_xml_string
from template_manager import list_templates, load_template, save_template
from utils import calculate_char_count, calculate_token_count
from state_manager import (
    save_state, load_state, import_state_from_file, export_state_to_file,
    list_states, delete_state, backup_all_states, restore_states_from_backup
)

class MainController:
    def __init__(self, main_window):
        self.mw = main_window
        self.tree_generated = False

    def select_project_folder(self):
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 프로젝트 폴더 선택이 필요 없습니다.")
            return
        folder = QFileDialog.getExistingDirectory(self.mw, "프로젝트 폴더 선택", os.path.expanduser("~"))
        if folder:
            self.mw.reset_state()
            self.mw.current_project_folder = folder
            idx = self.mw.dir_model.setRootPathFiltered(folder)
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))
            self.mw.status_bar.showMessage(f"Project Folder: {folder}")

            root_proxy_index = self.mw.checkable_proxy.mapFromSource(idx)
            self.mw.checkable_proxy.setData(root_proxy_index, Qt.Checked, Qt.CheckStateRole)
            self.mw.tree_view.expandAll()

    def generate_prompt(self):
        if self.mw.mode == "Meta Prompt Builder":
            return
        checked_files = self.mw.checkable_proxy.get_checked_files()

        file_contents = []
        self.mw.selected_files_data = []
        for fpath in checked_files:
            try:
                size = os.path.getsize(fpath)
                with open(fpath, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                file_contents.append((fpath, content))
                self.mw.selected_files_data.append((fpath, size))
            except Exception as e:
                print(f"Error loading file {fpath}: {e}")
                continue

        system_text = self.mw.system_tab.toPlainText()
        user_text = self.mw.user_tab.toPlainText()
        dev_text = ""

        root_dir = self.mw.current_project_folder if (self.mw.current_project_folder and os.path.isdir(self.mw.current_project_folder)) else None

        selected_folder = None
        for idx in self.mw.tree_view.selectedIndexes():
            src_index = self.mw.checkable_proxy.mapToSource(idx)
            if self.mw.dir_model.isDir(src_index):
                folder_path = self.mw.dir_model.filePath(src_index)
                if folder_path != root_dir:
                    selected_folder = folder_path
                    break

        final_prompt = generate_final_prompt(
            system_text, user_text, dev_text,
            file_contents,
            root_dir,
            config.allowed_extensions,
            config.excluded_dirs,
            selected_folder=selected_folder,
            add_tree=self.tree_generated
        )

        self.mw.last_generated_prompt = final_prompt
        self.mw.prompt_output_tab.setText(final_prompt)
        length = len(final_prompt)
        self.update_counts_for_text(final_prompt)
        self.mw.update_selected_files_panel()
        self.mw.status_bar.showMessage(f"Prompt generated! Length: {format(length, ',')} chars")
        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)

    def update_counts_for_text(self, text):
        char_count = calculate_char_count(text)
        token_count = 0
        if self.mw.auto_token_calc_check.isChecked():
            token_count = calculate_token_count(text)
        self.mw.char_count_label.setText(f"Chars: {format(char_count, ',')}")
        if self.mw.auto_token_calc_check.isChecked():
            self.mw.token_count_label.setText(f"Calculated Total Token: {format(token_count, ',')}")
        else:
            self.mw.token_count_label.setText("토큰 계산: 비활성화")

    def copy_to_clipboard(self):
        if self.mw.last_generated_prompt:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(self.mw.last_generated_prompt)
            self.mw.status_bar.showMessage("Copied!")
        else:
            self.mw.status_bar.showMessage("No prompt generated yet!")

    def on_data_changed(self, topLeft, bottomRight, roles):
        checked_files = self.mw.checkable_proxy.get_checked_files()
        self.mw.selected_files_data = []
        combined_content = ""
        for fpath in checked_files:
            try:
                size = os.path.getsize(fpath)
                with open(fpath, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                self.mw.selected_files_data.append((fpath, size))
                combined_content += content
            except:
                pass
        self.update_counts_for_text(combined_content)
        self.mw.update_selected_files_panel()

    def on_selection_changed(self, selected, deselected):
        for index in selected.indexes():
            current_state = self.mw.checkable_proxy.data(index, Qt.CheckStateRole)
            new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
            self.mw.checkable_proxy.setData(index, new_state, Qt.CheckStateRole)

    def update_selected_files_panel(self):
        self.mw.update_selected_files_panel()

    def generate_directory_tree_structure(self):
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 디렉토리 트리 기능이 필요 없습니다.")
            return
        import os
        if not self.mw.current_project_folder or not os.path.isdir(self.mw.current_project_folder):
            QMessageBox.information(self.mw, "Info", "No project folder selected.")
            return

        all_checked_paths = self.mw.checkable_proxy.get_all_checked_paths()
        if not all_checked_paths:
            self.mw.dir_structure_tab.setText("No files or folders selected.")
            self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
            self.mw.status_bar.showMessage("No selected items to build file tree!")
            return

        def build_tree(paths):
            tree = {}
            for p in paths:
                rel_path = os.path.relpath(p, self.mw.current_project_folder)
                parts = rel_path.split(os.sep)
                current = tree
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
            return tree

        def print_tree(tree, parent_path, indent=0, visited=None):
            if visited is None:
                visited = set()
            if parent_path in visited:
                return []
            visited.add(parent_path)

            lines = []
            indent_str = "  " * indent
            entries = sorted(tree.keys())
            dirs = []
            files = []
            for entry in entries:
                full_path = os.path.join(parent_path, entry)
                if os.path.isdir(full_path):
                    dirs.append(entry)
                else:
                    files.append(entry)
            for d in dirs:
                lines.append(f"{indent_str} 📁 {d}/")
                lines.extend(print_tree(tree[d], os.path.join(parent_path, d), indent+1, visited))
            for f in files:
                size = 0
                if os.path.isfile(os.path.join(parent_path, f)):
                    size = os.path.getsize(os.path.join(parent_path, f))
                lines.append(f"{indent_str} 📄 {f} ({size:,} bytes)")
            return lines

        tree = build_tree(all_checked_paths)
        root_lines = [f" 📁 {os.path.basename(self.mw.current_project_folder)}/"]
        for k in sorted(tree.keys()):
            full_path = os.path.join(self.mw.current_project_folder, k)
            if os.path.isdir(full_path):
                root_lines.append(f"  📁 {k}/")
                root_lines.extend(print_tree(tree[k], os.path.join(self.mw.current_project_folder, k), 2))
            else:
                size = 0
                if os.path.isfile(full_path):
                    size = os.path.getsize(full_path)
                root_lines.append(f"  📄 {k} ({size:,} bytes)")

        result_text = "File Tree:\n" + "\n".join(root_lines)
        self.mw.dir_structure_tab.setText(result_text)
        self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
        self.mw.status_bar.showMessage("File tree generated!")
        self.tree_generated = True

    def run_xml_parser(self):
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 XML 파서 기능이 필요 없습니다.")
            return
        xml_str = self.mw.xml_input_tab.toPlainText()
        if not xml_str.strip():
            self.mw.status_bar.showMessage("XML content is empty.")
            return

        project_dir = self.mw.current_project_folder
        if not project_dir or not os.path.isdir(project_dir):
            QMessageBox.information(self.mw, "Info", "프로젝트 폴더를 먼저 선택해주세요.")
            return

        result = parse_xml_string.apply_changes_from_xml(xml_str, project_dir)

        messages = []
        if result["created"]:
            messages.append(f"생성된 파일:\n" + "\n".join(result["created"]))
        if result["updated"]:
            messages.append(f"수정된 파일:\n" + "\n".join(result["updated"]))
        if result["deleted"]:
            messages.append(f"삭제된 파일:\n" + "\n".join(result["deleted"]))
        if result["errors"]:
            messages.append("오류:\n" + "\n".join(result["errors"]))

        if not (result["created"] or result["updated"] or result["deleted"] or result["errors"]):
            messages.append("변경 사항 없음.")

        final_message = "\n\n".join(messages)

        if result["status"] == "fail":
            QMessageBox.warning(self.mw, "XML 파싱 결과", final_message)
        else:
            QMessageBox.information(self.mw, "XML 파싱 결과", final_message)

        self.refresh_tree()
        self.mw.status_bar.showMessage("XML parsing completed!")

    def toggle_file_check(self, file_path):
        if self.mw.mode == "Meta Prompt Builder":
            return
        src_index = self.mw.dir_model.index(file_path)
        if src_index.isValid():
            proxy_index = self.mw.checkable_proxy.mapFromSource(src_index)
            if proxy_index.isValid():
                current_state = self.mw.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
                new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                self.mw.checkable_proxy.setData(proxy_index, new_state, Qt.CheckStateRole)

    def rename_item(self, file_path):
        if self.mw.mode == "Meta Prompt Builder":
            return
        if not os.path.exists(file_path):
            QMessageBox.warning(self.mw, "Error", "File or directory does not exist.")
            return
        base_dir = os.path.dirname(file_path)
        old_name = os.path.basename(file_path)
        new_name, ok = QInputDialog.getText(self.mw, "Rename", f"Enter new name for '{old_name}':")
        if ok and new_name.strip():
            new_path = os.path.join(base_dir, new_name.strip())
            try:
                os.rename(file_path, new_path)
                self.mw.status_bar.showMessage(f"Renamed '{old_name}' to '{new_name}'")
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"Error renaming: {str(e)}")

    def delete_item(self, file_path):
        if self.mw.mode == "Meta Prompt Builder":
            return
        if not os.path.exists(file_path):
            QMessageBox.warning(self.mw, "Error", "File or directory does not exist.")
            return
        reply = QMessageBox.question(self.mw, "Delete", f"Are you sure you want to delete '{os.path.basename(file_path)}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            import shutil
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                self.mw.status_bar.showMessage(f"Deleted '{file_path}'")
                self.refresh_tree()
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"Error deleting: {str(e)}")

    def refresh_tree(self):
        if self.mw.current_project_folder:
            idx = self.mw.dir_model.setRootPathFiltered(self.mw.current_project_folder)
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))

    def load_templates_list(self):
        self.mw.template_tree.clear()
        current_mode = self.mw.resource_mode_combo.currentText()

        # 여기서 current_mode는 "프롬프트" 또는 "상태" 로 설정되어 있으므로 이를 기반으로 처리
        if current_mode == "프롬프트":
            system_item = QTreeWidgetItem(["System"])
            user_item = QTreeWidgetItem(["User"])
            self.mw.template_tree.addTopLevelItem(system_item)
            self.mw.template_tree.addTopLevelItem(user_item)

            system_templates = list_templates("resources/prompts/system")
            user_templates = list_templates("resources/prompts/user")

            for st in system_templates:
                QTreeWidgetItem(system_item, [st])
            for ut in user_templates:
                QTreeWidgetItem(user_item, [ut])

            system_item.setExpanded(True)
            user_item.setExpanded(True)

        elif current_mode == "상태":
            states_item = QTreeWidgetItem(["States"])
            self.mw.template_tree.addTopLevelItem(states_item)
            states_list = list_states()
            for st in states_list:
                QTreeWidgetItem(states_item, [st])
            states_item.setExpanded(True)

        self.update_buttons_label()

    def load_selected_item(self):
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            if current_mode == "프롬프트":
                QMessageBox.information(self.mw, "Info", "프롬프트 파일을 선택해주세요.")
            else:
                QMessageBox.information(self.mw, "Info", "상태 파일을 선택해주세요.")
            return

        filename = item.text(0)
        if current_mode == "프롬프트":
            parent_text = item.parent().text(0)
            if parent_text == "System":
                file_path = os.path.join("resources", "prompts", "system", filename)
                content = load_template(file_path)
                self.mw.system_tab.setText(content)
                self.mw.status_bar.showMessage(f"Loaded system template: {filename}")
            elif parent_text == "User":
                file_path = os.path.join("resources", "prompts", "user", filename)
                content = load_template(file_path)
                self.mw.user_tab.setText(content)
                self.mw.status_bar.showMessage(f"Loaded user template: {filename}")

        elif current_mode == "상태":
            fname_no_ext = os.path.splitext(filename)[0]
            s = load_state(fname_no_ext)
            if s:
                self.mw.set_current_state(s)
                self.mw.status_bar.showMessage(f"Loaded state: {filename}")
            else:
                QMessageBox.information(self.mw, "Info", "Failed to load state.")

    def save_current_as_item(self):
        current_mode = self.mw.resource_mode_combo.currentText()
        if current_mode == "프롬프트":
            template_type = self.mw.template_type_combo.currentText()
            if template_type == "시스템":
                content = self.mw.system_tab.toPlainText()
                target_dir = "resources/prompts/system"
            else:
                content = self.mw.user_tab.toPlainText()
                target_dir = "resources/prompts/user"

            fname, ok = QInputDialog.getText(self.mw, "Save Template", "템플릿 파일 이름(확장자 제외)을 입력하세요:")
            if not ok or not fname.strip():
                return
            fname = fname.strip() + ".md"
            file_path = os.path.join(target_dir, fname)
            save_template(file_path, content)
            self.mw.status_bar.showMessage(f"Template saved: {file_path}")
            self.load_templates_list()

        elif current_mode == "상태":
            state = self.mw.get_current_state()
            fname, ok = QInputDialog.getText(self.mw, "Save State", "상태 파일 이름(확장자 제외)을 입력하세요:")
            if not ok or not fname.strip():
                return
            fname = fname.strip()
            if save_state(state, fname):
                self.mw.status_bar.showMessage(f"State saved: {fname}.json")
                self.load_templates_list()
            else:
                self.mw.status_bar.showMessage("Error saving state")

    def delete_selected_item(self):
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            if current_mode == "프롬프트":
                QMessageBox.information(self.mw, "Info", "프롬프트 파일을 선택해주세요.")
            else:
                QMessageBox.information(self.mw, "Info", "상태 파일을 선택해주세요.")
            return

        filename = item.text(0)
        if current_mode == "프롬프트":
            parent_text = item.parent().text(0)
            if parent_text == "System":
                file_path = os.path.join("resources", "prompts", "system", filename)
            elif parent_text == "User":
                file_path = os.path.join("resources", "prompts", "user", filename)
            else:
                QMessageBox.information(self.mw, "Info", "Invalid template selection.")
                return

            reply = QMessageBox.question(self.mw, "Delete", f"'{filename}'를 삭제하시겠습니까?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                from template_manager import delete_template
                delete_template(file_path)
                self.mw.status_bar.showMessage(f"Deleted template: {filename}")
                self.load_templates_list()

        elif current_mode == "상태":
            fname_no_ext = os.path.splitext(filename)[0]
            reply = QMessageBox.question(self.mw, "Delete", f"'{filename}'를 삭제하시겠습니까?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if delete_state(fname_no_ext):
                    self.mw.status_bar.showMessage(f"Deleted state: {filename}")
                    self.load_templates_list()
                else:
                    self.mw.status_bar.showMessage("Error deleting state")

    def update_current_item(self):
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            if current_mode == "프롬프트":
                QMessageBox.information(self.mw, "Info", "프롬프트 파일을 선택해주세요.")
            else:
                QMessageBox.information(self.mw, "Info", "상태 파일을 선택해주세요.")
            return

        filename = item.text(0)

        if current_mode == "프롬프트":
            parent_text = item.parent().text(0)
            if parent_text == "System":
                target_dir = "resources/prompts/system"
                content = self.mw.system_tab.toPlainText()
            elif parent_text == "User":
                target_dir = "resources/prompts/user"
                content = self.mw.user_tab.toPlainText()
            else:
                QMessageBox.information(self.mw, "Info", "Invalid template selection.")
                return

            file_path = os.path.join(target_dir, filename)
            save_template(file_path, content)
            self.mw.status_bar.showMessage(f"Template updated: {filename}")

        elif current_mode == "상태":
            fname_no_ext = os.path.splitext(filename)[0]
            state = self.mw.get_current_state()
            if save_state(state, fname_no_ext):
                self.mw.status_bar.showMessage(f"State updated: {filename}")
            else:
                self.mw.status_bar.showMessage("Error updating state")

    def generate_meta_prompt(self):
        system_text = self.mw.system_tab.toPlainText()
        user_text = self.mw.user_tab.toPlainText()
        final_output = system_text.replace("{{user-input}}", user_text)
        self.mw.prompt_output_tab.setText(final_output)
        self.mw.last_generated_prompt = final_output
        self.update_counts_for_text(final_output)
        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)
        self.mw.status_bar.showMessage("META Prompt generated!")

    def generate_final_meta_prompt(self):
        # 메타 프롬프트 탭 내용
        meta_prompt_content = self.mw.meta_prompt_tab.toPlainText()

        # var- 로 시작하는 탭들을 변수로 매핑
        var_map = {}
        for i in range(self.mw.build_tabs.count()):
            tab_name = self.mw.build_tabs.tabText(i)
            if tab_name.startswith("var-"):
                var_name = tab_name[4:]
                tab_widget = self.mw.build_tabs.widget(i)
                if tab_widget is not None:
                    var_map[var_name] = tab_widget.toPlainText()

        # user-prompt 처리: var-user-prompt 탭이 있으면 그걸 사용, 없으면 기존 user_prompt_tab 사용
        if "user-prompt" in var_map:
            user_prompt_content = var_map["user-prompt"]
        else:
            user_prompt_content = self.mw.user_prompt_tab.toPlainText()

        # user-prompt 치환
        final_prompt = meta_prompt_content.replace("[[user-prompt]]", user_prompt_content)

        # 나머지 var- 변수 치환
        for k, v in var_map.items():
            if k != "user-prompt":
                final_prompt = final_prompt.replace(f"[[{k}]]", v)

        self.mw.final_prompt_tab.setText(final_prompt)
        self.mw.last_generated_prompt = final_prompt
        self.update_counts_for_text(final_prompt)
        self.mw.build_tabs.setCurrentWidget(self.mw.final_prompt_tab)
        self.mw.status_bar.showMessage("Final Prompt generated!")

    def copy_final_prompt(self):
        if self.mw.last_generated_prompt:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(self.mw.last_generated_prompt)
            self.mw.status_bar.showMessage("Final Prompt Copied!")
        else:
            self.mw.status_bar.showMessage("No final prompt generated yet!")

    def save_state_to_default(self):
        state = self.mw.get_current_state()
        if save_state(state, "default"):
            self.mw.status_bar.showMessage("State saved successfully!")
        else:
            self.mw.status_bar.showMessage("Error saving state")

    def load_state_from_default(self):
        state = load_state("default")
        if state:
            self.mw.set_current_state(state)
            self.mw.status_bar.showMessage("State loaded successfully!")
        else:
            self.mw.status_bar.showMessage("No state loaded or empty state")

    def export_state_to_file(self):
        path, _ = QFileDialog.getSaveFileName(self.mw, "Export State", os.path.expanduser("~"), "JSON Files (*.json)")
        if path:
            state = self.mw.get_current_state()
            if export_state_to_file(state, path):
                self.mw.status_bar.showMessage("State exported successfully!")
            else:
                self.mw.status_bar.showMessage("Error exporting state")

    def import_state_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self.mw, "Import State", os.path.expanduser("~"), "JSON Files (*.json)")
        if path:
            state = import_state_from_file(path)
            if state:
                self.mw.set_current_state(state)
                self.mw.status_bar.showMessage("State imported successfully!")
            else:
                self.mw.status_bar.showMessage("Error importing state or empty state")

    def update_buttons_label(self):
        current_mode = self.mw.resource_mode_combo.currentText()
        # current_mode 가 "프롬프트" 또는 "상태"일 때 각각 버튼 텍스트를 변경
        if current_mode == "프롬프트":
            self.mw.load_selected_template_btn.setText("선택한 프롬프트 불러오기")
            self.mw.save_as_template_btn.setText("현재 프롬프트로 저장")
            self.mw.delete_template_btn.setText("선택한 프롬프트 삭제")
            self.mw.update_template_btn.setText("현재 프롬프트 업데이트")
            self.mw.backup_button.setText("모든 상태 백업 (비활성화)")
            self.mw.backup_button.setEnabled(False)
            self.mw.restore_button.setText("백업에서 상태 복원 (비활성화)")
            self.mw.restore_button.setEnabled(False)
        else:
            self.mw.load_selected_template_btn.setText("선택한 상태 불러오기")
            self.mw.save_as_template_btn.setText("현재 상태로 저장")
            self.mw.delete_template_btn.setText("선택한 상태 삭제")
            self.mw.update_template_btn.setText("현재 상태 업데이트")
            self.mw.backup_button.setText("모든 상태 백업")
            self.mw.backup_button.setEnabled(True)
            self.mw.restore_button.setText("백업에서 상태 복원")
            self.mw.restore_button.setEnabled(True)

    def on_mode_changed(self):
        self.load_templates_list()

    def backup_all_states_action(self):
        path, _ = QFileDialog.getSaveFileName(self.mw, "Backup All States", os.path.expanduser("~"), "Zip Files (*.zip)")
        if path:
            if backup_all_states(path):
                self.mw.status_bar.showMessage("All states backed up successfully!")
            else:
                self.mw.status_bar.showMessage("Error backing up states")

    def restore_states_from_backup_action(self):
        path, _ = QFileDialog.getOpenFileName(self.mw, "Restore States from Backup", os.path.expanduser("~"), "Zip Files (*.zip)")
        if path:
            if restore_states_from_backup(path):
                self.mw.status_bar.showMessage("States restored successfully!")
                self.load_templates_list()
            else:
                self.mw.status_bar.showMessage("Error restoring states")
