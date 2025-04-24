import os
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QApplication

# 변경된 경로에서 import
from core.services.prompt_service import PromptService
from core.services.xml_service import XmlService
from core.services.template_service import TemplateService
from core.services.state_service import StateService
from core.services.filesystem_service import FilesystemService
from core.services.config_service import ConfigService
from core.pydantic_models.app_state import AppState
# MainWindow는 타입 힌트용으로만 사용 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow


class MainController:
    def __init__(self, main_window: 'MainWindow'):
        self.mw = main_window # MainWindow 인스턴스
        # 서비스 인스턴스 생성 (향후 DI 컨테이너 사용 고려)
        self.config_service = ConfigService()
        self.prompt_service = PromptService()
        self.xml_service = XmlService()
        self.template_service = TemplateService()
        self.state_service = StateService()
        self.fs_service = FilesystemService(self.config_service) # FilesystemService에 ConfigService 주입

        self.tree_generated = False # 파일 트리 생성 여부 상태
        self.gitignore_path = None # .gitignore 파일 경로

    def load_gitignore_settings(self):
        """Loads .gitignore patterns and updates the UI and config."""
        self.gitignore_path = None
        patterns = set() # 로드된 패턴 저장
        lines_for_ui = [] # UI 표시용 라인

        settings = self.config_service.get_settings()
        # 기본 무시 목록으로 시작
        patterns.update(settings.default_ignore_list)
        # UI에는 기본값 + 설정 파일의 excluded_dirs 표시 (선택적)
        # lines_for_ui.extend(sorted(list(settings.default_ignore_list.union(settings.excluded_dirs))))
        # 또는 .gitignore 파일 내용 우선 표시
        lines_for_ui.extend(sorted(list(settings.default_ignore_list)))


        if self.mw.current_project_folder:
            possible_path = os.path.join(self.mw.current_project_folder, ".gitignore")
            if os.path.isfile(possible_path):
                self.gitignore_path = possible_path
                try:
                    with open(self.gitignore_path, 'r', encoding='utf-8') as f:
                        lines = f.read().splitlines()
                    # 주석과 빈 줄 제외
                    gitignore_lines = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]
                    patterns.update(gitignore_lines)
                    lines_for_ui = gitignore_lines # .gitignore 있으면 UI 내용 교체
                except Exception as e:
                    QMessageBox.warning(self.mw, "Error", f".gitignore 로드 중 오류: {str(e)}")
                    # 오류 시 UI는 기본값 유지

        # 설정 파일(config.yml)의 excluded_dirs도 패턴에 추가
        patterns.update(settings.excluded_dirs)

        # UI 업데이트
        self.mw.gitignore_edit.setText("\n".join(lines_for_ui))

        # 파일 탐색기 필터 갱신 (CheckableProxyModel에 패턴 설정)
        if hasattr(self.mw, 'checkable_proxy'):
             self.mw.checkable_proxy.set_ignore_patterns(patterns) # ProxyModel에 패턴 전달
             # invalidateFilter는 set_ignore_patterns 내부에서 호출되도록 수정하는 것이 좋음
             # self.mw.checkable_proxy.invalidateFilter()


    def save_gitignore_settings(self):
        """Saves the content of the gitignore editor to the .gitignore file."""
        if not self.mw.current_project_folder:
            QMessageBox.warning(self.mw, "Error", "프로젝트 폴더가 설정되지 않았습니다.")
            return

        lines = self.mw.gitignore_edit.toPlainText().splitlines()
        # 저장 시에도 주석과 빈 줄 제외
        lines_to_save = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]

        target_path = os.path.join(self.mw.current_project_folder, ".gitignore")
        try:
            # 파일 쓰기 전 사용자 확인 (선택적)
            # reply = QMessageBox.question(self.mw, "저장 확인", f"{target_path}에 저장하시겠습니까?",
            #                              QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            # if reply == QMessageBox.No:
            #     return

            with open(target_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines_to_save) + "\n") # 마지막 줄 개행 추가

            QMessageBox.information(self.mw, "Info", f".gitignore가 저장되었습니다: {target_path}")

            # 저장 후 다시 로드하여 config 및 필터 갱신
            self.load_gitignore_settings()

        except Exception as e:
            QMessageBox.warning(self.mw, "Error", f".gitignore 저장 중 오류: {str(e)}")

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
        self.tree_generated = False # 트리 생성 상태 초기화

        # 설정 및 필터 초기화
        default_settings = self.config_service.get_settings() # 기본 설정 로드
        default_patterns = set(default_settings.default_ignore_list).union(default_settings.excluded_dirs)
        self.mw.gitignore_edit.setText("\n".join(sorted(list(default_patterns)))) # UI 업데이트
        if hasattr(self.mw, 'checkable_proxy'):
             self.mw.checkable_proxy.set_ignore_patterns(default_patterns) # 모델에 패턴 전달

        # 파일 탐색기 트리 리셋 (MainWindow 역할)
        home_path = os.path.expanduser("~")
        if hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
            idx = self.mw.dir_model.setRootPathFiltered(home_path) # 모델 메소드 호출
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))
            # self.mw.checkable_proxy.checked_files_dict.clear() # reset_state에서 처리됨
            self.mw.tree_view.collapseAll()
            # self.mw.tree_view.reset() # setRootIndex가 어느 정도 리셋 효과 있음

        # 윈도우 제목 리셋
        self.mw.update_window_title()
        self.mw.status_bar.showMessage("프로그램 리셋 완료.")
        QMessageBox.information(self.mw, "Info", "프로그램이 초기 상태로 리셋되었습니다.")

    def select_project_folder(self):
        """Opens a dialog to select the project folder and updates the UI."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 프로젝트 폴더 선택이 필요 없습니다.")
            return

        # 현재 프로젝트 폴더 또는 홈 디렉토리에서 시작
        start_dir = self.mw.current_project_folder if self.mw.current_project_folder else os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self.mw, "프로젝트 폴더 선택", start_dir)

        if folder:
            # UI 상태 초기화 (MainWindow 메서드 호출)
            self.mw.reset_state()
            self.mw.current_project_folder = folder
            folder_name = os.path.basename(folder)
            self.mw.project_folder_label.setText(f"현재 프로젝트 폴더: {folder}")

            # .gitignore 로드 및 필터 갱신
            self.load_gitignore_settings()

            # 파일 탐색기 업데이트 (MainWindow 역할)
            if hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
                idx = self.mw.dir_model.setRootPathFiltered(folder)
                root_proxy_index = self.mw.checkable_proxy.mapFromSource(idx)
                self.mw.tree_view.setRootIndex(root_proxy_index)
                self.mw.status_bar.showMessage(f"Project Folder: {folder}")

                # 루트 폴더 자동 체크 및 확장
                if root_proxy_index.isValid():
                    # setData 호출 시 하위 항목 로딩 및 체크/확장 자동 처리됨
                    self.mw.checkable_proxy.setData(root_proxy_index, Qt.Checked, Qt.CheckStateRole)
                    # self.mw.tree_view.expand(root_proxy_index) # setData 내부에서 처리

            # 윈도우 제목 업데이트
            self.mw.update_window_title(folder_name)


    def generate_prompt(self):
        """Generates the prompt based on selected files and inputs."""
        if self.mw.mode == "Meta Prompt Builder":
            # 메타 프롬프트 생성 로직 호출
            return self.generate_meta_prompt() # 성공 여부 반환

        if not self.mw.current_project_folder:
             QMessageBox.warning(self.mw, "경고", "프로젝트 폴더를 먼저 선택해주세요.")
             return False

        # 체크된 파일 목록 가져오기 (CheckableProxyModel 역할)
        checked_files = self.mw.checkable_proxy.get_checked_files() if hasattr(self.mw, 'checkable_proxy') else []
        if not checked_files:
            QMessageBox.warning(self.mw, "경고", "프롬프트에 포함할 파일을 하나 이상 선택해주세요.")
            return False

        # 파일 내용 읽기
        file_contents = []
        self.mw.selected_files_data = [] # UI 상태 업데이트
        read_errors = []
        for fpath in checked_files:
            try:
                # TODO: 파일 크기 제한, 인코딩 처리 강화
                size = os.path.getsize(fpath)
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp: # 에러 처리 추가
                    content = fp.read()
                file_contents.append((fpath, content))
                self.mw.selected_files_data.append((fpath, size))
            except Exception as e:
                error_msg = f"파일 읽기 오류 ({os.path.basename(fpath)}): {e}"
                print(error_msg)
                read_errors.append(error_msg)
                # 오류 발생 시 계속 진행할지 결정
                continue

        if read_errors:
             QMessageBox.warning(self.mw, "파일 로딩 오류", "일부 파일을 읽는 중 오류 발생:\n" + "\n".join(read_errors))
             # 오류 발생 시 프롬프트 생성을 중단할 수도 있음
             # return False

        # UI에서 텍스트 가져오기
        system_text = self.mw.system_tab.toPlainText()
        user_text = self.mw.user_tab.toPlainText()
        dir_structure_content = ""
        if self.tree_generated and hasattr(self.mw, "dir_structure_tab"):
            dir_structure_content = self.mw.dir_structure_tab.toPlainText()

        # PromptService 사용하여 프롬프트 생성
        final_prompt = self.prompt_service.generate_code_enhancer_prompt(
            system_text=system_text,
            user_text=user_text,
            file_contents=file_contents,
            root_dir=self.mw.current_project_folder,
            dir_structure_content=dir_structure_content
        )

        # UI 업데이트
        self.mw.last_generated_prompt = final_prompt # 임시 저장
        self.mw.prompt_output_tab.setText(final_prompt)
        self.update_counts_for_text(final_prompt) # 글자/토큰 수 업데이트
        self.mw.status_bar.showMessage(f"Prompt generated! Length: {len(final_prompt):,} chars")
        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab) # 결과 탭으로 전환
        return True

    def update_counts_for_text(self, text):
        """Updates character and token counts in the status bar."""
        # utils.helpers 사용
        from utils.helpers import calculate_char_count, calculate_token_count

        char_count = calculate_char_count(text)
        token_count = None # 초기화
        token_text = "토큰 계산: 비활성화"

        if self.mw.auto_token_calc_check.isChecked():
            # 백그라운드 스레드에서 계산 고려 (UI 블로킹 방지)
            # TODO: 스레딩 구현 또는 비동기 처리
            token_count = calculate_token_count(text)
            if token_count is not None:
                 token_text = f"Calculated Total Token: {token_count:,}"
            else:
                 token_text = "토큰 계산 오류"

        self.mw.char_count_label.setText(f"Chars: {char_count:,}")
        self.mw.token_count_label.setText(token_text)

    def copy_to_clipboard(self):
        """Copies the last generated prompt to the clipboard."""
        # 현재 활성화된 탭의 내용을 복사하는 것이 더 직관적일 수 있음
        current_widget = self.mw.build_tabs.currentWidget()
        prompt_to_copy = ""
        if current_widget == self.mw.prompt_output_tab:
             prompt_to_copy = self.mw.prompt_output_tab.toPlainText()
        elif hasattr(self.mw, 'final_prompt_tab') and current_widget == self.mw.final_prompt_tab:
             prompt_to_copy = self.mw.final_prompt_tab.toPlainText()
        elif hasattr(self.mw, 'dir_structure_tab') and current_widget == self.mw.dir_structure_tab:
             prompt_to_copy = self.mw.dir_structure_tab.toPlainText()
        else:
             # 다른 탭이면 마지막 생성된 프롬프트(임시 저장된 것) 복사 시도
             prompt_to_copy = self.mw.last_generated_prompt

        if prompt_to_copy:
            QApplication.clipboard().setText(prompt_to_copy)
            self.mw.status_bar.showMessage("Copied!")
            return True
        else:
            self.mw.status_bar.showMessage("복사할 내용이 없습니다!")
            return False

    def on_mode_changed(self):
        """Handles UI updates when the application mode changes."""
        # MainWindow의 _restart_with_mode가 호출되므로, 여기서는 특별한 작업 불필요
        # self.update_buttons_label() # 리소스 관리 버튼 레이블 업데이트 호출 (MainWindow __init__에서 처리)
        pass

    def on_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: List[int]):
        """Handles updates when data in the CheckableProxyModel changes (e.g., check state)."""
        # 체크 상태 변경 시 파일 내용 합산 및 카운트 업데이트 (선택적 기능)
        # if Qt.CheckStateRole in roles:
        #     # 성능 고려: 모든 파일 다시 읽지 않고 변경된 부분만 반영?
        #     # 또는 간단하게 전체 체크된 파일 다시 읽기
        #     checked_files = self.mw.checkable_proxy.get_checked_files()
        #     combined_content = ""
        #     self.mw.selected_files_data = []
        #     for fpath in checked_files:
        #         try:
        #             size = os.path.getsize(fpath)
        #             with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
        #                 content = fp.read()
        #             self.mw.selected_files_data.append((fpath, size))
        #             combined_content += content # 메모리 사용량 주의
        #         except Exception as e:
        #             print(f"Error reading file for count {fpath}: {e}")
        #             pass
        #     # 어떤 텍스트의 카운트를 업데이트할지 결정 필요 (예: 프롬프트 출력 탭?)
        #     # self.update_counts_for_text(combined_content)
        #     print(f"Data changed (check state?), {len(checked_files)} files checked.")
        pass # 현재는 특별한 동작 없음

    # on_selection_changed는 MainWindow에서 처리 (클릭 시 토글)

    def generate_directory_tree_structure(self):
        """Generates the directory tree structure based on checked items."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 디렉토리 트리 기능이 필요 없습니다.")
            return False

        if not self.mw.current_project_folder or not os.path.isdir(self.mw.current_project_folder):
            QMessageBox.warning(self.mw, "경고", "프로젝트 폴더를 먼저 선택해주세요.")
            return False

        # 체크된 모든 경로 가져오기 (CheckableProxyModel 역할)
        all_checked_paths = self.mw.checkable_proxy.get_all_checked_paths() if hasattr(self.mw, 'checkable_proxy') else []

        if not all_checked_paths:
            message = "선택된 파일이나 폴더가 없습니다."
            if hasattr(self.mw, "dir_structure_tab"):
                self.mw.dir_structure_tab.setText(message)
                self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
            self.mw.status_bar.showMessage("파일 트리를 생성할 항목이 없습니다!")
            return False

        # FilesystemService 사용하여 트리 생성
        try:
            tree_string = self.fs_service.get_directory_tree(all_checked_paths, self.mw.current_project_folder)
        except Exception as e:
             QMessageBox.critical(self.mw, "오류", f"디렉토리 트리 생성 중 오류 발생: {e}")
             return False

        # UI 업데이트
        if hasattr(self.mw, "dir_structure_tab"):
            self.mw.dir_structure_tab.setText(tree_string)
            self.mw.build_tabs.setCurrentWidget(self.mw.dir_structure_tab)
        self.mw.status_bar.showMessage("File tree generated!")
        self.tree_generated = True # 상태 플래그 업데이트
        return True


    def run_xml_parser(self):
        """Parses XML input and applies changes to the project files."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 XML 파서 기능이 필요 없습니다.")
            return

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

        # 사용자 확인 (중요!)
        reply = QMessageBox.question(self.mw, "XML 변경 적용 확인",
                                     f"XML 내용에 따라 프로젝트 파일을 변경합니다:\n{project_dir}\n\n계속하시겠습니까? 이 작업은 되돌릴 수 없습니다.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            self.mw.status_bar.showMessage("XML 파싱 취소됨.")
            return

        # XmlService 사용하여 변경 적용
        try:
            result = self.xml_service.apply_changes_from_xml(xml_str, project_dir)
        except Exception as e:
             QMessageBox.critical(self.mw, "XML 파싱 오류", f"XML 처리 중 예외 발생: {e}")
             self.refresh_tree() # 오류 발생 시에도 트리 새로고침 시도
             return

        # 결과 메시지 생성
        messages = []
        if result["created"]: messages.append("생성된 파일:\n" + "\n".join(result["created"]))
        if result["updated"]: messages.append("수정된 파일:\n" + "\n".join(result["updated"]))
        if result["deleted"]: messages.append("삭제된 파일:\n" + "\n".join(result["deleted"]))
        if result["errors"]: messages.append("오류:\n" + "\n".join(result["errors"]))

        if not messages: messages.append("변경 사항 없음.")

        final_message = "\n\n".join(messages)

        # 결과 표시
        if result["errors"]:
            QMessageBox.warning(self.mw, "XML 파싱 결과 (오류 발생)", final_message)
        else:
            QMessageBox.information(self.mw, "XML 파싱 결과", final_message)

        # 파일 변경 후 트리 새로고침
        self.refresh_tree()
        self.mw.status_bar.showMessage("XML 파싱 완료!")

    def generate_all_and_copy(self):
        """Generates directory tree, prompt, and copies to clipboard."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "Info", "Meta Prompt Builder 모드에서는 이 기능을 사용할 수 없습니다.")
            return

        # 1. 트리 생성
        tree_success = self.generate_directory_tree_structure()
        if not tree_success: return

        # 2. 프롬프트 생성
        prompt_success = self.generate_prompt()
        if not prompt_success: return

        # 3. 클립보드 복사
        copy_success = self.copy_to_clipboard()
        if copy_success:
            self.mw.status_bar.showMessage("트리 생성, 프롬프트 생성 및 복사 완료!")

    def toggle_file_check(self, file_path):
        """Toggles the check state of a file/folder in the tree view."""
        if self.mw.mode == "Meta Prompt Builder": return
        # 이 로직은 MainWindow의 on_selection_changed_handler에서 처리되거나
        # FileTreeController로 이동해야 함. Controller가 직접 ProxyModel을 조작하는 것은
        # UI 상태와 로직 간의 결합도를 높일 수 있음.
        # 여기서는 MainWindow의 핸들러를 통해 처리되도록 유지.
        print(f"Toggle check requested for: {file_path} (handled by selection)")
        # 필요한 경우 ProxyModel의 setData를 직접 호출할 수 있으나 권장하지 않음.
        # if hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
        #     src_index = self.mw.dir_model.index(file_path)
        #     if src_index.isValid():
        #         proxy_index = self.mw.checkable_proxy.mapFromSource(src_index)
        #         if proxy_index.isValid():
        #             current_state = self.mw.checkable_proxy.data(proxy_index, Qt.CheckStateRole)
        #             new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
        #             self.mw.checkable_proxy.setData(proxy_index, new_state, Qt.CheckStateRole)


    # --- 파일 시스템 작업 (Rename, Delete) ---
    # TODO: 이 기능들은 FilesystemService 또는 별도 서비스로 분리 고려
    def rename_item(self, file_path):
        """Renames a file or directory."""
        if self.mw.mode == "Meta Prompt Builder": return
        if not os.path.exists(file_path):
            QMessageBox.warning(self.mw, "Error", "파일 또는 디렉토리가 존재하지 않습니다.")
            return

        base_dir = os.path.dirname(file_path)
        old_name = os.path.basename(file_path)
        new_name, ok = QInputDialog.getText(self.mw, "이름 변경", f"'{old_name}'의 새 이름을 입력하세요:", text=old_name)

        if ok and new_name and new_name.strip():
            new_name_stripped = new_name.strip()
            # TODO: 유효하지 않은 파일/폴더 이름 문자 검사 추가
            if new_name_stripped == old_name:
                 self.mw.status_bar.showMessage("이름이 변경되지 않았습니다.")
                 return

            new_path = os.path.join(base_dir, new_name_stripped)

            if os.path.exists(new_path):
                 QMessageBox.warning(self.mw, "Error", f"'{new_name_stripped}' 이름이 이미 존재합니다.")
                 return

            try:
                os.rename(file_path, new_path)
                self.mw.status_bar.showMessage(f"'{old_name}' -> '{new_name_stripped}' 이름 변경 완료")
                # 이름 변경 후 체크 상태 업데이트
                if hasattr(self.mw, 'checkable_proxy'):
                    if file_path in self.mw.checkable_proxy.checked_files_dict:
                        is_checked = self.mw.checkable_proxy.checked_files_dict.pop(file_path)
                        self.mw.checkable_proxy.checked_files_dict[new_path] = is_checked
                self.refresh_tree() # 트리 새로고침
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"이름 변경 중 오류 발생: {str(e)}")
        elif ok:
             QMessageBox.warning(self.mw, "Error", "새 이름은 비워둘 수 없습니다.")


    def delete_item(self, file_path):
        """Deletes a file or directory."""
        if self.mw.mode == "Meta Prompt Builder": return
        if not os.path.exists(file_path):
            QMessageBox.warning(self.mw, "Error", "파일 또는 디렉토리가 존재하지 않습니다.")
            return

        item_name = os.path.basename(file_path)
        item_type = "폴더" if os.path.isdir(file_path) else "파일"
        reply = QMessageBox.question(self.mw, "삭제 확인",
                                     f"정말로 '{item_name}' {item_type}을(를) 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            import shutil
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path) # 폴더 삭제
                else:
                    os.remove(file_path) # 파일 삭제
                self.mw.status_bar.showMessage(f"'{item_name}' 삭제 완료")
                # 삭제 후 체크 상태 업데이트
                if hasattr(self.mw, 'checkable_proxy'):
                    if file_path in self.mw.checkable_proxy.checked_files_dict:
                        del self.mw.checkable_proxy.checked_files_dict[file_path]
                        # 하위 항목 체크 상태도 제거해야 할 수 있음 (폴더 삭제 시)
                        # TODO: 폴더 삭제 시 하위 체크 상태 제거 로직 추가
                self.refresh_tree() # 트리 새로고침
            except Exception as e:
                QMessageBox.warning(self.mw, "Error", f"삭제 중 오류 발생: {str(e)}")

    def refresh_tree(self):
        """Refreshes the file explorer tree view."""
        # 이 로직은 MainWindow 또는 FileTreeController 역할
        if self.mw.current_project_folder and hasattr(self.mw, 'dir_model') and hasattr(self.mw, 'checkable_proxy'):
            # 현재 확장된 노드 저장 (선택적)
            # expanded_indexes = self._get_expanded_indexes()

            # 모델 루트 경로 재설정 (내부적으로 fetch 실행됨)
            idx = self.mw.dir_model.setRootPathFiltered(self.mw.current_project_folder)
            # 필터 갱신 (필수) - setRootPathFiltered 이후 또는 set_ignore_patterns 호출 시 자동 수행되도록
            # self.mw.checkable_proxy.invalidateFilter()
            # 뷰 루트 인덱스 설정
            self.mw.tree_view.setRootIndex(self.mw.checkable_proxy.mapFromSource(idx))

            # 확장 상태 복원 (선택적)
            # self._restore_expanded_indexes(expanded_indexes)

            self.mw.status_bar.showMessage("파일 트리 새로고침 완료.")


    # --- 리소스 관리 (템플릿/상태) ---
    # TODO: 이 기능들은 ResourceController로 분리

    def load_templates_list(self):
        """Loads the list of templates or states into the resource tree."""
        self.mw.template_tree.clear() # 트리 초기화
        current_mode = self.mw.resource_mode_combo.currentText()

        if current_mode == "프롬프트":
            # TemplateService 사용
            system_templates = self.template_service.list_templates("prompts/system")
            user_templates = self.template_service.list_templates("prompts/user")

            # UI 업데이트 (MainWindow 역할)
            system_item = self.mw.create_tree_item("System")
            user_item = self.mw.create_tree_item("User")
            for st in sorted(system_templates): self.mw.create_tree_item(st, system_item)
            for ut in sorted(user_templates): self.mw.create_tree_item(ut, user_item)
            system_item.setExpanded(True)
            user_item.setExpanded(True)

        elif current_mode == "상태":
            # StateService 사용
            states_list = self.state_service.list_states()

            # UI 업데이트 (MainWindow 역할)
            states_item = self.mw.create_tree_item("States")
            for st_file in sorted(states_list): self.mw.create_tree_item(st_file, states_item) # 확장자 포함 표시
            states_item.setExpanded(True)

        self.update_buttons_label() # 버튼 레이블 업데이트

    def load_selected_item(self):
        """Loads the selected template or state."""
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem() # UI 요소 접근
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", f"{current_mode} 파일을 선택해주세요.")
            return

        filename = item.text(0) # 파일 이름 (확장자 포함)

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
                # TemplateService 사용
                content = self.template_service.load_template(relative_path)
                # UI 업데이트
                target_tab.setText(content)
                self.mw.status_bar.showMessage(f"Loaded {parent_text.lower()} template: {filename}")

        elif current_mode == "상태":
            # StateService 사용 (파일 이름에서 확장자 제거)
            fname_no_ext = os.path.splitext(filename)[0]
            loaded_state = self.state_service.load_state(fname_no_ext)

            if loaded_state:
                # MainWindow의 상태 설정 메서드 호출
                self.mw.set_current_state(loaded_state) # Pydantic 모델 전달
                # set_current_state 내부에서 status_bar 메시지 업데이트됨
            else:
                QMessageBox.warning(self.mw, "오류", "상태 파일을 불러오는 데 실패했습니다.")


    def save_current_as_item(self):
        """Saves the current prompt or state as a new item."""
        current_mode = self.mw.resource_mode_combo.currentText()

        if current_mode == "프롬프트":
            template_type = self.mw.template_type_combo.currentText() # UI 요소 접근
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
            if not ok or not fname or not fname.strip():
                return
            fname_stripped = fname.strip()
            # TODO: 유효하지 않은 파일 이름 문자 검사
            fname_md = fname_stripped + ".md"
            relative_path = os.path.join(target_dir_relative, fname_md)

            # TemplateService 사용
            if self.template_service.save_template(relative_path, content):
                self.mw.status_bar.showMessage(f"Template saved: {fname_md}")
                self.load_templates_list() # 목록 새로고침
            else:
                 QMessageBox.warning(self.mw, "오류", "템플릿 저장 중 오류가 발생했습니다.")

        elif current_mode == "상태":
            # MainWindow에서 현재 상태 가져오기 (Pydantic 모델 반환)
            current_state = self.mw.get_current_state() # AppState 모델 반환 가정

            fname, ok = QInputDialog.getText(self.mw, "상태 저장", "상태 파일 이름(확장자 제외)을 입력하세요:")
            if not ok or not fname or not fname.strip():
                return
            fname_stripped = fname.strip()
            # TODO: 유효하지 않은 파일 이름 문자 검사

            # StateService 사용
            if self.state_service.save_state(current_state, fname_stripped):
                self.mw.status_bar.showMessage(f"State saved: {fname_stripped}.json")
                self.load_templates_list() # 목록 새로고침
            else:
                QMessageBox.warning(self.mw, "오류", "상태 저장 중 오류가 발생했습니다.")


    def delete_selected_item(self):
        """Deletes the selected template or state file."""
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", f"{current_mode} 파일을 선택해주세요.")
            return

        filename = item.text(0) # 확장자 포함된 이름
        parent_text = item.parent().text(0)

        reply = QMessageBox.question(self.mw, "삭제 확인", f"정말로 '{filename}'을(를) 삭제하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        deleted = False
        if current_mode == "프롬프트":
            relative_path = ""
            if parent_text == "System":
                relative_path = os.path.join("prompts", "system", filename)
            elif parent_text == "User":
                relative_path = os.path.join("prompts", "user", filename)

            if relative_path:
                # TemplateService 사용
                deleted = self.template_service.delete_template(relative_path)

        elif current_mode == "상태":
            # StateService 사용 (확장자 제거)
            fname_no_ext = os.path.splitext(filename)[0]
            deleted = self.state_service.delete_state(fname_no_ext)

        # 결과 처리
        if deleted:
            self.mw.status_bar.showMessage(f"Deleted: {filename}")
            self.load_templates_list() # 목록 새로고침
        else:
            QMessageBox.warning(self.mw, "오류", f"'{filename}' 삭제 중 오류가 발생했습니다.")


    def update_current_item(self):
        """Updates the selected template or state file with the current content/state."""
        current_mode = self.mw.resource_mode_combo.currentText()
        item = self.mw.template_tree.currentItem()
        if not item or not item.parent():
            QMessageBox.information(self.mw, "Info", f"{current_mode} 파일을 선택해주세요.")
            return

        filename = item.text(0) # 확장자 포함
        parent_text = item.parent().text(0)

        reply = QMessageBox.question(self.mw, "업데이트 확인", f"'{filename}'의 내용을 현재 편집 중인 내용으로 덮어쓰시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply != QMessageBox.Yes:
            return

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
                # TemplateService 사용
                updated = self.template_service.save_template(relative_path, content) # save가 update 역할

        elif current_mode == "상태":
            # MainWindow에서 현재 상태 가져오기
            current_state = self.mw.get_current_state() # AppState 모델
            fname_no_ext = os.path.splitext(filename)[0]
            # StateService 사용
            updated = self.state_service.save_state(current_state, fname_no_ext) # save가 update 역할

        # 결과 처리
        if updated:
            self.mw.status_bar.showMessage(f"Updated: {filename}")
            # 목록 새로고침은 필요 없음 (내용만 업데이트)
        else:
            QMessageBox.warning(self.mw, "오류", f"'{filename}' 업데이트 중 오류가 발생했습니다.")


    # --- 메타 프롬프트 관련 ---
    # TODO: 이 기능들은 PromptController 또는 MetaPromptController로 분리

    def generate_meta_prompt(self):
        """Generates the intermediate meta prompt."""
        # UI에서 텍스트 가져오기
        system_text = self.mw.system_tab.toPlainText() # 메타 템플릿
        user_text = self.mw.user_tab.toPlainText() # 메타 사용자 입력

        # PromptService 사용
        final_output = self.prompt_service.generate_meta_prompt(
            meta_template=system_text,
            meta_user_input=user_text
        )

        # UI 업데이트
        self.mw.prompt_output_tab.setText(final_output) # 메타 프롬프트 출력 탭
        self.mw.last_generated_prompt = final_output # 임시 저장
        self.update_counts_for_text(final_output)
        self.mw.build_tabs.setCurrentWidget(self.mw.prompt_output_tab)
        self.mw.status_bar.showMessage("META Prompt generated!")
        return True # 성공 여부 반환


    def generate_final_meta_prompt(self):
        """Generates the final prompt by replacing variables in the meta prompt."""
        # UI에서 텍스트 가져오기
        meta_prompt_content = ""
        user_prompt_content = ""
        if hasattr(self.mw, 'meta_prompt_tab'):
             meta_prompt_content = self.mw.meta_prompt_tab.toPlainText()
        if hasattr(self.mw, 'user_prompt_tab'):
             user_prompt_content = self.mw.user_prompt_tab.toPlainText()

        # 동적 탭에서 변수 값 가져오기 (MainWindow 역할)
        variables = {}
        if hasattr(self.mw, 'build_tabs'):
            for i in range(self.mw.build_tabs.count()):
                tab_name = self.mw.build_tabs.tabText(i)
                # TODO: var- 접두사 대신 더 명확한 방법 고려
                if tab_name.startswith("var-"):
                    var_name = tab_name[4:]
                    tab_widget = self.mw.build_tabs.widget(i)
                    if tab_widget and hasattr(tab_widget, 'toPlainText'):
                        variables[var_name] = tab_widget.toPlainText()

        # PromptService 사용
        final_prompt = self.prompt_service.generate_final_meta_prompt(
            meta_prompt_content=meta_prompt_content,
            user_prompt_content=user_prompt_content,
            variables=variables
        )

        # UI 업데이트
        if hasattr(self.mw, 'final_prompt_tab'):
            self.mw.final_prompt_tab.setText(final_prompt) # 최종 프롬프트 탭
            self.mw.last_generated_prompt = final_prompt # 임시 저장
            self.update_counts_for_text(final_prompt)
            self.mw.build_tabs.setCurrentWidget(self.mw.final_prompt_tab)
            self.mw.status_bar.showMessage("Final Prompt generated!")
        else:
             QMessageBox.warning(self.mw, "오류", "최종 프롬프트 탭을 찾을 수 없습니다.")


    # --- 상태 관리 액션 ---
    # TODO: 이 기능들은 ResourceController 또는 StateController로 분리

    def save_state_to_default(self):
        """Saves the current state to the default state file."""
        state = self.mw.get_current_state() # AppState 모델
        if self.state_service.save_state(state, "default"):
            self.mw.status_bar.showMessage("기본 상태 저장 완료!")
        else:
            QMessageBox.warning(self.mw, "오류", "기본 상태 저장 중 오류가 발생했습니다.")

    def load_state_from_default(self):
        """Loads the state from the default state file."""
        state = self.state_service.load_state("default")
        if state:
            self.mw.set_current_state(state) # Pydantic 모델 전달
            # set_current_state 내부에서 status_bar 메시지 업데이트됨
        else:
            # load_state 내부에서 이미 로그 출력 또는 기본값 반환 처리됨
             QMessageBox.warning(self.mw, "오류", "기본 상태 파일을 불러오는 데 실패했습니다.")


    def export_state_to_file(self):
        """Exports the current state to a user-selected file."""
        path, _ = QFileDialog.getSaveFileName(self.mw, "상태 내보내기", os.path.expanduser("~"), "JSON Files (*.json)")
        if path:
            state = self.mw.get_current_state() # AppState 모델
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
                self.mw.set_current_state(state) # Pydantic 모델 전달
                # set_current_state 내부에서 status_bar 메시지 업데이트됨
            else:
                 QMessageBox.warning(self.mw, "오류", "상태 가져오기 중 오류가 발생했거나 파일 내용이 유효하지 않습니다.")


    def backup_all_states_action(self):
        """Backs up all states to a user-selected zip file."""
        path, _ = QFileDialog.getSaveFileName(self.mw, "모든 상태 백업", os.path.expanduser("~"), "Zip Files (*.zip)")
        if path:
            if self.state_service.backup_all_states(path):
                self.mw.status_bar.showMessage("모든 상태 백업 완료!")
            else:
                QMessageBox.warning(self.mw, "오류", "상태 백업 중 오류가 발생했습니다.")

    def restore_states_from_backup_action(self):
        """Restores states from a user-selected zip file."""
        path, _ = QFileDialog.getOpenFileName(self.mw, "백업에서 상태 복원", os.path.expanduser("~"), "Zip Files (*.zip)")
        if path:
            reply = QMessageBox.question(self.mw, "복원 확인",
                                         "백업 파일에서 상태를 복원하시겠습니까?\n현재 저장된 모든 상태가 백업 내용으로 대체됩니다.",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self.state_service.restore_states_from_backup(path):
                    self.mw.status_bar.showMessage("상태 복원 완료!")
                    self.load_templates_list() # 상태 목록 새로고침
                else:
                    QMessageBox.warning(self.mw, "오류", "상태 복원 중 오류가 발생했습니다.")

    # --- UI 업데이트 헬퍼 ---
    def update_buttons_label(self):
        """Updates the labels of buttons in the resource manager section based on the mode."""
        # 이 로직은 MainWindow 또는 ResourceController 역할
        current_mode = self.mw.resource_mode_combo.currentText()
        is_prompt_mode = (current_mode == "프롬프트")

        # 버튼 텍스트 설정
        self.mw.load_selected_template_btn.setText(f"📥 선택한 {current_mode} 불러오기")
        self.mw.save_as_template_btn.setText(f"💾 현재 {current_mode}로 저장")
        self.mw.delete_template_btn.setText(f"❌ 선택한 {current_mode} 삭제")
        self.mw.update_template_btn.setText(f"🔄 현재 {current_mode} 업데이트")

        # 상태 관련 버튼 활성화/비활성화 및 텍스트
        self.mw.backup_button.setEnabled(not is_prompt_mode)
        self.mw.restore_button.setEnabled(not is_prompt_mode)
        self.mw.backup_button.setText("📦 모든 상태 백업" + (" (비활성화)" if is_prompt_mode else ""))
        self.mw.restore_button.setText("🔙 백업에서 상태 복원" + (" (비활성화)" if is_prompt_mode else ""))

        # 프롬프트 타입 콤보박스 가시성
        self.mw.template_type_combo.setVisible(is_prompt_mode)
        self.mw.template_type_label.setVisible(is_prompt_mode)
