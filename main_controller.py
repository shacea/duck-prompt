import os
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QTreeWidgetItem
from prompt_manager import generate_final_prompt
from config import config
import parse_xml_string
from template_manager import list_templates, load_template, save_template
from utils import calculate_char_count, calculate_token_count

class MainController:
    def __init__(self, main_window):
        self.mw = main_window
        self.tree_generated = False

    def select_project_folder(self):
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 프로젝트 폴더 선택이 필요 없습니다.")
            return
        folder = QFileDialog.getExistingDirectory(self.mw, "Select Project Folder", os.path.expanduser("~"))
        if folder:
            self.mw.reset_state()
            self.mw.current_project_folder = folder
            idx = self.mw.dir_model.setRootPathFiltered(folder)
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))
            self.mw.status_bar.showMessage(f"Project Folder: {folder}")

            root_proxy_index = self.mw.checkable_proxy.mapFromSource(idx)
            self.mw.checkable_proxy.setData(root_proxy_index, Qt.Checked, Qt.CheckStateRole)
            self.mw.tree_view.expandAll()

    def load_file_preview(self, index):
        if self.mw.mode == "Meta Prompt Builder":
            return
        src_index = self.mw.checkable_proxy.mapToSource(index)
        if self.mw.dir_model.isDir(src_index):
            return
        file_path = self.mw.dir_model.filePath(src_index)

        if not self.mw.dir_model.is_file_allowed(file_path, self.mw.current_project_folder):
            self.mw.prompt_output_tab.setText("This file is excluded by the current filter settings.")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.mw.prompt_output_tab.setText(content)
            self.mw.status_bar.showMessage(f"File loaded: {file_path}")
            self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)
        except Exception as e:
            self.mw.prompt_output_tab.setText("Error occurred while reading the file...")
            self.mw.status_bar.showMessage(f"Error: {str(e)}")

    # 필터 관련 기능 제거
    # def set_allowed_extensions(self):
    #     ...
    # def set_excluded_dirs(self):
    #     ...
    # def apply_filters(self):
    #     ...

    def refresh_tree(self):
        if self.mw.current_project_folder:
            idx = self.mw.dir_model.setRootPathFiltered(self.mw.current_project_folder)
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))

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
                file_contents.append((fpath, f"File load error: {str(e)}"))
                self.mw.selected_files_data.append((fpath, 0))

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

        # 토큰/문자수 계산
        self.update_counts_for_text(final_prompt)

        self.mw.update_selected_files_panel()
        self.mw.status_bar.showMessage(f"Prompt generated! Length: {format(length, ',')} chars")
        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)

    def update_counts_for_text(self, text):
        """주어진 텍스트에 대해 문자수와 토큰수를 업데이트한다."""
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
            self.mw.status_bar.showMessage("Copied to clipboard!")
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

        # 파일 선택 변화 시 토큰/문자수 업데이트
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

        def print_tree(tree, parent_path, indent=0):
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
                lines.extend(print_tree(tree[d], os.path.join(parent_path, d), indent+1))
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
            self.mw.status_bar.showMessage("XML 내용이 비어있습니다.")
            return

        project_dir = self.mw.current_project_folder
        if not project_dir or not os.path.isdir(project_dir):
            QMessageBox.information(self.mw, "Info", "프로젝트 폴더를 먼저 선택해주세요.")
            return

        parse_xml_string.apply_changes_from_xml(xml_str, project_dir)
        self.mw.status_bar.showMessage("XML 파싱이 완료되었습니다!")

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

    def load_templates_list(self):
        self.mw.template_tree.clear()
        system_item = QTreeWidgetItem(["System Templates"])
        user_item = QTreeWidgetItem(["User Templates"])
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

    def load_selected_template(self):
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", "Please select a template file.")
            return

        parent_text = item.parent().text(0)
        filename = item.text(0)
        if parent_text == "System Templates":
            file_path = os.path.join("resources", "prompts", "system", filename)
            content = load_template(file_path)
            self.mw.system_tab.setText(content)
            self.mw.status_bar.showMessage(f"Loaded system template: {filename}")
        elif parent_text == "User Templates":
            file_path = os.path.join("resources", "prompts", "user", filename)
            content = load_template(file_path)
            self.mw.user_tab.setText(content)
            self.mw.status_bar.showMessage(f"Loaded user template: {filename}")

    def save_current_as_template(self):
        template_type = self.mw.template_type_combo.currentText()
        if template_type == "System":
            content = self.mw.system_tab.toPlainText()
            target_dir = "resources/prompts/system"
        else:
            content = self.mw.user_tab.toPlainText()
            target_dir = "resources/prompts/user"

        fname, ok = QInputDialog.getText(self.mw, "Save Template", "Enter template file name (without extension):")
        if not ok or not fname.strip():
            return
        fname = fname.strip() + ".md"
        file_path = os.path.join(target_dir, fname)
        save_template(file_path, content)
        self.mw.status_bar.showMessage(f"Template saved: {file_path}")
        self.load_templates_list()

    def delete_selected_template(self):
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", "Please select a template file.")
            return

        parent_text = item.parent().text(0)
        filename = item.text(0)
        if parent_text == "System Templates":
            file_path = os.path.join("resources", "prompts", "system", filename)
        elif parent_text == "User Templates":
            file_path = os.path.join("resources", "prompts", "user", filename)
        else:
            QMessageBox.information(self.mw, "Info", "Invalid template selection.")
            return

        reply = QMessageBox.question(self.mw, "Delete", f"Are you sure you want to delete '{filename}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            from template_manager import delete_template
            delete_template(file_path)
            self.mw.status_bar.showMessage(f"Deleted template: {filename}")
            self.load_templates_list()

    def update_current_template(self):
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", "Please select a template file.")
            return

        parent_text = item.parent().text(0)
        filename = item.text(0)

        if parent_text == "System Templates":
            target_dir = "resources/prompts/system"
            content = self.mw.system_tab.toPlainText()
        elif parent_text == "User Templates":
            target_dir = "resources/prompts/user"
            content = self.mw.user_tab.toPlainText()
        else:
            QMessageBox.information(self.mw, "Info", "Invalid template selection.")
            return

        file_path = os.path.join(target_dir, filename)
        save_template(file_path, content)
        self.mw.status_bar.showMessage(f"Template updated: {filename}")

    def generate_meta_prompt(self):
        if self.mw.mode != "Meta Prompt Builder":
            return
        system_text = self.mw.system_tab.toPlainText()
        user_text = self.mw.user_tab.toPlainText()
        final_output = system_text.replace("{{user-input}}", user_text)
        self.mw.prompt_output_tab.setText(final_output)
        self.mw.last_generated_prompt = final_output
        self.update_counts_for_text(final_output)
        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)
        self.mw.status_bar.showMessage("META Prompt generated!")
