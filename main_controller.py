import os
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox
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
        self.gitignore_path = None

    def load_gitignore_settings(self):
        self.gitignore_path = None
        if self.mw.current_project_folder:
            possible_path = os.path.join(self.mw.current_project_folder, ".gitignore")
            self.gitignore_path = possible_path if os.path.isfile(possible_path) else None

        # 기본 무시 목록으로 초기화
        config.excluded_dirs = set(config.default_ignore_list)

        # .gitignore 파일이 있으면 내용 추가
        if self.gitignore_path:
            try:
                with open(self.gitignore_path, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                # 주석과 빈 줄 제외
                lines = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]
                for ln in lines:
                    config.excluded_dirs.add(ln) # 중복 제거하며 추가
                self.mw.gitignore_edit.setText("\n".join(lines)) # 편집창에는 파일 내용만 표시
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f".gitignore 로드 중 오류: {str(e)}")
                # 오류 발생 시 기본값만 표시
                self.mw.gitignore_edit.setText("\n".join(config.default_ignore_list))
        else:
            # .gitignore 파일 없으면 기본값 표시
            self.mw.gitignore_edit.setText("\n".join(config.default_ignore_list))

        # 필터 갱신
        self.mw.checkable_proxy.invalidateFilter()


    def save_gitignore_settings(self):
        if not self.mw.current_project_folder:
            QMessageBox.warning(self.mw, "Error", "프로젝트 폴더가 설정되지 않았습니다.")
            return
        lines = self.mw.gitignore_edit.toPlainText().splitlines()
        # 저장 시에도 주석과 빈 줄 제외
        lines = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]

        target_path = os.path.join(self.mw.current_project_folder, ".gitignore")
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                for ln in lines:
                    f.write(ln + "\n")
            QMessageBox.information(self.mw, "Info", f".gitignore가 저장되었습니다: {target_path}")
            # 저장 후 다시 로드하여 config.excluded_dirs 업데이트 및 필터 갱신
            self.load_gitignore_settings()
        except Exception as e:
            QMessageBox.warning(self.mw, "Error", f".gitignore 저장 중 오류: {str(e)}")

    def reset_program(self):
        self.mw.reset_state()
        self.mw.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
        self.mw.system_tab.clear()
        self.mw.user_tab.clear()
        if hasattr(self.mw, "dir_structure_tab"):
            self.mw.dir_structure_tab.clear()
        if hasattr(self.mw, "xml_input_tab"):
            self.mw.xml_input_tab.clear()
        if hasattr(self.mw, "prompt_output_tab"):
            self.mw.prompt_output_tab.clear()
        self.mw.gitignore_edit.clear()

        # 기본 ignore 리스트 설정 및 필터 갱신
        config.excluded_dirs = set(config.default_ignore_list)
        self.mw.gitignore_edit.setText("\n".join(config.default_ignore_list))
        self.mw.checkable_proxy.invalidateFilter()

        # 파일 탐색기 트리를 홈 디렉토리로 재설정하고 체크 상태도 초기화
        import os
        home_path = os.path.expanduser("~")
        idx = self.mw.dir_model.setRootPathFiltered(home_path)
        self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))
        self.mw.checkable_proxy.checked_files_dict.clear()
        self.mw.tree_view.collapseAll()
        self.mw.tree_view.reset() # 모델 리셋 강제

        # 윈도우 제목 리셋
        self.mw.update_window_title()

        QMessageBox.information(self.mw, "Info", "프로그램이 초기 상태로 리셋되었습니다.")

    def select_project_folder(self):
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 프로젝트 폴더 선택이 필요 없습니다.")
            return
        folder = QFileDialog.getExistingDirectory(self.mw, "프로젝트 폴더 선택", os.path.expanduser("~"))
        if folder:
            self.mw.reset_state() # 상태 초기화 (여기서 기본 ignore 설정됨)
            self.mw.current_project_folder = folder
            folder_name = os.path.basename(folder) # 폴더 이름 추출
            self.mw.project_folder_label.setText(f"현재 프로젝트 폴더: {folder}")

            # .gitignore 로드 (여기서 config.excluded_dirs 업데이트 및 필터 갱신)
            self.load_gitignore_settings()

            # 모델 루트 설정 및 뷰 업데이트
            idx = self.mw.dir_model.setRootPathFiltered(folder)
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))
            self.mw.status_bar.showMessage(f"Project Folder: {folder}")

            # 루트 폴더 자동 체크 및 확장
            root_proxy_index = self.mw.checkable_proxy.mapFromSource(idx)
            if root_proxy_index.isValid(): # 루트 인덱스가 유효한 경우에만 실행
                 self.mw.checkable_proxy.setData(root_proxy_index, Qt.Checked, Qt.CheckStateRole)
                 # expandAll 대신 루트만 확장하거나 필요한 만큼 확장하도록 변경 가능
                 self.mw.tree_view.expand(root_proxy_index) # 루트만 확장

            # 윈도우 제목 업데이트
            self.mw.update_window_title(folder_name)


    def generate_prompt(self):
        if self.mw.mode == "Meta Prompt Builder":
            return False # 성공 여부 반환

        if not self.mw.current_project_folder:
             QMessageBox.warning(self.mw, "경고", "프로젝트 폴더를 먼저 선택해주세요.")
             return False

        checked_files = self.mw.checkable_proxy.get_checked_files()
        if not checked_files:
            QMessageBox.warning(self.mw, "경고", "프롬프트에 포함할 파일을 하나 이상 선택해주세요.")
            return False

        file_contents = []
        self.mw.selected_files_data = []
        for fpath in checked_files:
            try:
                # 필터링으로 숨겨진 파일은 포함하지 않도록 체크 (선택사항)
                # src_index = self.mw.dir_model.index(fpath)
                # if src_index.isValid():
                #     proxy_index = self.mw.checkable_proxy.mapFromSource(src_index)
                #     if not proxy_index.isValid(): # 필터링된 경우 건너뜀
                #         continue

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
        # 선택된 폴더 로직은 현재 필터링과 직접 관련 없으므로 유지
        # for idx in self.mw.tree_view.selectedIndexes():
        #     proxy_idx = self.mw.checkable_proxy.mapToSource(idx) # 원본 인덱스 사용 필요
        #     if self.mw.dir_model.isDir(proxy_idx):
        #         folder_path = self.mw.dir_model.filePath(proxy_idx)
        #         if folder_path != root_dir:
        #             selected_folder = folder_path
        #             break

        dir_structure_content = ""
        if self.tree_generated and hasattr(self.mw, "dir_structure_tab"):
            dir_structure_content = self.mw.dir_structure_tab.toPlainText()

        final_prompt = generate_final_prompt(
            system_text, user_text, dev_text,
            file_contents,
            root_dir,
            config.allowed_extensions, # config 사용
            config.excluded_dirs,      # config 사용
            selected_folder=selected_folder,
            add_tree=self.tree_generated,
            dir_structure_content=dir_structure_content
        )

        self.mw.last_generated_prompt = final_prompt
        self.mw.prompt_output_tab.setText(final_prompt)
        length = len(final_prompt)
        self.update_counts_for_text(final_prompt)
        self.mw.status_bar.showMessage(f"Prompt generated! Length: {format(length, ',')} chars")
        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)
        return True # 성공

    def update_counts_for_text(self, text):
        char_count = calculate_char_count(text)
        token_count = 0
        if self.mw.auto_token_calc_check.isChecked():
            token_count = calculate_token_count(text)
        self.mw.char_count_label.setText(f"Chars: {format(char_count, ',')}")
        if self.mw.auto_token_calc_check.isChecked():
            self.mw.token_count_label.setText(f"Calculated Total Token: {format(token_count, ',') if token_count else 'N/A'}")
        else:
            self.mw.token_count_label.setText("토큰 계산: 비활성화")

    def copy_to_clipboard(self):
        if self.mw.last_generated_prompt:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(self.mw.last_generated_prompt)
            self.mw.status_bar.showMessage("Copied!")
            return True # 성공
        else:
            self.mw.status_bar.showMessage("No prompt generated yet!")
            return False # 실패

    def on_mode_changed(self):
        self.update_buttons_label()

    def on_data_changed(self, topLeft, bottomRight, roles):
        # 체크 상태 변경 시 파일 내용 합산 및 카운트 업데이트
        if Qt.CheckStateRole in roles:
            checked_files = self.mw.checkable_proxy.get_checked_files()
            self.mw.selected_files_data = []
            combined_content = ""
            for fpath in checked_files:
                try:
                    # 필터링된 파일은 제외할 필요 없음 (get_checked_files가 처리 가정)
                    size = os.path.getsize(fpath)
                    with open(fpath, 'r', encoding='utf-8') as fp:
                        content = fp.read()
                    self.mw.selected_files_data.append((fpath, size))
                    combined_content += content
                except Exception as e:
                    print(f"Error reading file for count {fpath}: {e}")
                    pass
            self.update_counts_for_text(combined_content)

    def on_selection_changed(self, selected, deselected):
        """
        폴더 선택 시 자동 체크를 제거하기 위해 함수 내용 제거.
        (이전 버전에서 제거되었으므로 유지)
        """
        pass

    def generate_directory_tree_structure(self):
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 디렉토리 트리 기능이 필요 없습니다.")
            return False # 실패
        if not self.mw.current_project_folder or not os.path.isdir(self.mw.current_project_folder):
            QMessageBox.information(self.mw, "Info", "No project folder selected.")
            return False # 실패

        all_checked_paths = self.mw.checkable_proxy.get_all_checked_paths()
        if not all_checked_paths:
            if hasattr(self.mw, "dir_structure_tab"):
                self.mw.dir_structure_tab.setText("No files or folders selected.")
                self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
            self.mw.status_bar.showMessage("No selected items to build file tree!")
            return False # 실패

        # 필터링된 항목은 트리 구조에 포함하지 않도록 필터링
        visible_checked_paths = []
        for path in all_checked_paths:
            src_index = self.mw.dir_model.index(path)
            if src_index.isValid():
                proxy_index = self.mw.checkable_proxy.mapFromSource(src_index)
                if proxy_index.isValid(): # 보이는 항목만 추가
                    visible_checked_paths.append(path)

        if not visible_checked_paths:
             if hasattr(self.mw, "dir_structure_tab"):
                self.mw.dir_structure_tab.setText("No visible files or folders selected.")
                self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
             self.mw.status_bar.showMessage("No visible selected items to build file tree!")
             return False

        def build_tree(paths):
            tree = {}
            for p in paths:
                # 프로젝트 루트 기준 상대 경로 사용
                try:
                    rel_path = os.path.relpath(p, self.mw.current_project_folder)
                except ValueError: # 다른 드라이브 등 relpath 계산 불가 시 건너뜀
                    continue
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
            # 순환 참조 방지 (이론상 파일 시스템에서는 드물지만 안전장치)
            # if parent_path in visited:
            #     return []
            # visited.add(parent_path)

            lines = []
            indent_str = "  " * indent
            entries = sorted(tree.keys())
            dirs = []
            files = []

            for entry in entries:
                full_path = os.path.join(parent_path, entry)
                # 실제 경로가 존재하는지, 그리고 필터링되지 않았는지 다시 확인
                src_index = self.mw.dir_model.index(full_path)
                if not src_index.isValid(): continue
                proxy_index = self.mw.checkable_proxy.mapFromSource(src_index)
                if not proxy_index.isValid(): continue # 필터링된 항목 제외

                if os.path.isdir(full_path):
                    dirs.append(entry)
                elif os.path.isfile(full_path): # 파일만 추가
                    files.append(entry)

            for d in dirs:
                lines.append(f"{indent_str} 📁 {d}/")
                # 재귀 호출 시에도 full_path 사용
                lines.extend(print_tree(tree[d], os.path.join(parent_path, d), indent+1, visited))
            for f in files:
                size = 0
                full_file_path = os.path.join(parent_path, f)
                if os.path.isfile(full_file_path):
                    try:
                        size = os.path.getsize(full_file_path)
                    except OSError:
                        size = 0 # 접근 불가 등 오류 시 0 처리
                lines.append(f"{indent_str} 📄 {f} ({size:,} bytes)")
            return lines

        # 보이는 체크된 경로만 사용하여 트리 빌드
        tree_data = build_tree(visible_checked_paths)

        # 루트 폴더 이름 가져오기
        root_folder_name = os.path.basename(self.mw.current_project_folder)
        root_lines = [f"File Tree:", f" 📁 {root_folder_name}/"]

        # 루트 아래 항목들 처리
        root_lines.extend(print_tree(tree_data, self.mw.current_project_folder, 1)) # 시작 indent=1

        result_text = "\n".join(root_lines)
        if hasattr(self.mw, "dir_structure_tab"):
            self.mw.dir_structure_tab.setText(result_text)
            self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
        self.mw.status_bar.showMessage("File tree generated!")
        self.tree_generated = True
        return True # 성공


    def run_xml_parser(self):
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 XML 파서 기능이 필요 없습니다.")
            return
        xml_str = ""
        if hasattr(self.mw, "xml_input_tab"):
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
            messages.append("생성된 파일:\n" + "\n".join(result["created"]))
        if result["updated"]:
            messages.append("수정된 파일:\n" + "\n".join(result["updated"]))
        if result["deleted"]:
            messages.append("삭제된 파일:\n" + "\n".join(result["deleted"]))
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

    # 새로운 메서드: 트리 생성 + 프롬프트 생성 + 복사
    def generate_all_and_copy(self):
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 이 기능을 사용할 수 없습니다.")
            return

        # 1. 트리 생성
        tree_success = self.generate_directory_tree_structure()
        if not tree_success:
            # 트리 생성 실패 시 메시지는 generate_directory_tree_structure 내부에서 처리됨
            return

        # 2. 프롬프트 생성
        prompt_success = self.generate_prompt()
        if not prompt_success:
            # 프롬프트 생성 실패 시 메시지는 generate_prompt 내부에서 처리됨
            return

        # 3. 클립보드 복사
        copy_success = self.copy_to_clipboard()
        if copy_success:
            self.mw.status_bar.showMessage("Tree generated, Prompt generated, and Copied!")

    def toggle_file_check(self, file_path):
        if self.mw.mode == "Meta Prompt Builder":
            return
        src_index = self.mw.dir_model.index(file_path)
        if src_index.isValid():
            # 소스 인덱스를 프록시 인덱스로 변환
            proxy_index = self.mw.checkable_proxy.mapFromSource(src_index)
            if proxy_index.isValid(): # 필터링되지 않은 경우에만 토글
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
            # 루트 경로 재설정 (내부적으로 fetch 실행됨)
            idx = self.mw.dir_model.setRootPathFiltered(self.mw.current_project_folder)
            # 필터 갱신 (필수)
            self.mw.checkable_proxy.invalidateFilter()
            # 뷰 루트 인덱스 설정
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))
            # 필요하다면 트리 확장 상태 복원 로직 추가 가능


    def load_templates_list(self):
        self.mw.template_tree.clear()
        current_mode = self.mw.resource_mode_combo.currentText()

        if current_mode == "프롬프트":
            system_item = self.mw.create_tree_item("System")
            user_item = self.mw.create_tree_item("User")

            system_templates = list_templates("resources/prompts/system")
            user_templates = list_templates("resources/prompts/user")

            for st in system_templates:
                self.mw.create_tree_item(st, system_item)
            for ut in user_templates:
                self.mw.create_tree_item(ut, user_item)

            system_item.setExpanded(True)
            user_item.setExpanded(True)

        elif current_mode == "상태":
            states_item = self.mw.create_tree_item("States")
            states_list = list_states()
            for st in states_list:
                self.mw.create_tree_item(st, states_item)
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
                self.mw.set_current_state(s) # set_current_state 내부에서 필터 갱신 필요
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
        meta_prompt_content = self.mw.meta_prompt_tab.toPlainText()

        var_map = {}
        for i in range(self.mw.build_tabs.count()):
            tab_name = self.mw.build_tabs.tabText(i)
            if tab_name.startswith("var-"):
                var_name = tab_name[4:]
                tab_widget = self.mw.build_tabs.widget(i)
                if tab_widget is not None:
                    var_map[var_name] = tab_widget.toPlainText()

        if "user-prompt" in var_map:
            user_prompt_content = var_map["user-prompt"]
        else:
            user_prompt_content = self.mw.user_prompt_tab.toPlainText()

        final_prompt = meta_prompt_content.replace("[[user-prompt]]", user_prompt_content)

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
            self.mw.set_current_state(state) # 내부에서 필터 갱신 필요
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
                self.mw.set_current_state(state) # 내부에서 필터 갱신 필요
                self.mw.status_bar.showMessage("State imported successfully!")
            else:
                self.mw.status_bar.showMessage("Error importing state or empty state")

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

    def update_buttons_label(self):
        current_mode = self.mw.resource_mode_combo.currentText()
        if current_mode == "프롬프트":
            self.mw.load_selected_template_btn.setText("📥 선택한 프롬프트 불러오기")
            self.mw.save_as_template_btn.setText("💾 현재 프롬프트로 저장")
            self.mw.delete_template_btn.setText("❌ 선택한 프롬프트 삭제")
            self.mw.update_template_btn.setText("🔄 현재 프롬프트 업데이트")
            self.mw.backup_button.setText("📦 모든 상태 백업 (비활성화)")
            self.mw.backup_button.setEnabled(False)
            self.mw.restore_button.setText("🔙 백업에서 상태 복원 (비활성화)")
            self.mw.restore_button.setEnabled(False)
            self.mw.template_type_combo.setVisible(True) # 프롬프트 모드일 때 보이게
            self.mw.template_type_label.setVisible(True)
        else: # 상태 모드
            self.mw.load_selected_template_btn.setText("📥 선택한 상태 불러오기")
            self.mw.save_as_template_btn.setText("💾 현재 상태로 저장")
            self.mw.delete_template_btn.setText("❌ 선택한 상태 삭제")
            self.mw.update_template_btn.setText("🔄 현재 상태 업데이트")
            self.mw.backup_button.setText("📦 모든 상태 백업")
            self.mw.backup_button.setEnabled(True)
            self.mw.restore_button.setText("🔙 백업에서 상태 복원")
            self.mw.restore_button.setEnabled(True)
            self.mw.template_type_combo.setVisible(False) # 상태 모드일 때 숨김
            self.mw.template_type_label.setVisible(False)
