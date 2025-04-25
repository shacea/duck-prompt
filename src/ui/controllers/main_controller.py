
import os
import base64 # 추가
import mimetypes # 추가
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import Qt, QModelIndex, QMimeData # QMimeData 추가
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QApplication, QListWidgetItem # QListWidgetItem 추가
from PyQt5.QtGui import QImage # QImage 추가

# 서비스 및 모델 import
from core.services.config_service import ConfigService
from core.services.state_service import StateService
from core.services.template_service import TemplateService
from core.services.prompt_service import PromptService
from core.services.xml_service import XmlService
from core.services.filesystem_service import FilesystemService
from core.services.token_service import TokenCalculationService
from core.pydantic_models.app_state import AppState
from utils.helpers import calculate_char_count

# MainWindow는 타입 힌트용으로만 사용 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window import MainWindow
    from .resource_controller import ResourceController
    from .prompt_controller import PromptController
    from .xml_controller import XmlController
    from .file_tree_controller import FileTreeController

# Pillow import 시도 (이미지 처리용)
try:
    from PIL import Image
    from PIL.ImageQt import ImageQt
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False
    print("Warning: Pillow library not installed. Image handling from clipboard might be limited.")


class MainController:
    """
    메인 컨트롤러는 애플리케이션의 전반적인 흐름과
    다른 컨트롤러 간의 조정 역할을 담당 (필요한 경우).
    주요 기능 로직은 각 전문 컨트롤러에 위임.
    """
    def __init__(self, main_window: 'MainWindow'):
        self.mw = main_window
        self.token_service: TokenCalculationService = self.mw.token_service
        self.config_service: ConfigService = self.mw.config_service
        self.last_token_count: Optional[int] = None

    def reset_program(self):
        """Resets the application to its initial state."""
        self._initialized = False
        self.mw.reset_state()
        self._initialized = False

        self.mw.project_folder_label.setText("현재 프로젝트 폴더: (선택 안 됨)")
        self.mw.system_tab.clear()
        self.mw.user_tab.clear()
        if hasattr(self.mw, "dir_structure_tab"): self.mw.dir_structure_tab.clear()
        if hasattr(self.mw, "xml_input_tab"): self.mw.xml_input_tab.clear()
        if hasattr(self.mw, "prompt_output_tab"): self.mw.prompt_output_tab.clear()
        if hasattr(self.mw, "summary_tab"): self.mw.summary_tab.clear()
        if hasattr(self.mw, "attachment_list_widget"): self.mw.attachment_list_widget.clear() # 첨부 목록 클리어

        self.mw.file_tree_controller.reset_gitignore_and_filter()
        self.mw.file_tree_controller.reset_file_tree()

        self.mw.llm_combo.setCurrentIndex(self.mw.llm_combo.findText("Gemini"))
        self.on_llm_selected()

        self.update_char_count_for_active_tab()
        self.reset_token_label()
        if hasattr(self.mw, 'api_time_label'): # API 시간 라벨 초기화 추가
            self.mw.api_time_label.setText("API 시간: -")

        self.mw.update_window_title()
        self.mw.status_bar.showMessage("프로그램 리셋 완료.")

        self._initialized = True
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
        else:
            self.mw.char_count_label.setText("Chars: 0")

    def reset_token_label(self):
        """Resets the token count label to its default state."""
        if hasattr(self.mw, '_initialized') and self.mw._initialized:
            self.mw.token_count_label.setText("토큰 계산: -")
            self.last_token_count = None

    def handle_text_changed(self):
        """Handles text changes in editors: updates char count and resets token label."""
        self.update_char_count_for_active_tab()
        self.reset_token_label()

    def calculate_and_display_tokens(self, text: str, attachments: Optional[List[Dict[str, Any]]] = None):
        """Calculates tokens for the given text and attachments, updates the status bar."""
        if not hasattr(self.mw, '_initialized') or not self.mw._initialized:
            print("Token calculation skipped: MainWindow not initialized.")
            self.reset_token_label()
            return

        attachments = attachments or []
        char_count = calculate_char_count(text)
        self.mw.char_count_label.setText(f"Chars: {char_count:,}")

        token_count = None
        token_text = "토큰 계산: -"
        self.last_token_count = None

        # 텍스트와 첨부파일 모두 없으면 계산 안 함
        if not text and not attachments:
            print("Token calculation skipped: Text and attachments are empty.")
            self.mw.token_count_label.setText(token_text)
            return

        selected_llm = self.mw.llm_combo.currentText()
        model_name = self.mw.model_name_combo.currentText().strip()

        if not model_name:
            token_text = f"{selected_llm} 모델명을 선택하거나 입력하세요."
            print("Token calculation skipped: Model name is empty.")
            self.mw.token_count_label.setText(token_text)
            return

        token_text = f"{selected_llm} 토큰 계산 중..."
        self.mw.token_count_label.setText(token_text)
        QApplication.processEvents()

        print(f"Calling token_service.calculate_tokens for {selected_llm}, {model_name}...")
        # calculate_tokens에 attachments 전달
        token_count = self.token_service.calculate_tokens(selected_llm, model_name, text, attachments)
        print(f"Token calculation result: {token_count}")

        if token_count is not None:
            token_text = f"Total Token ({selected_llm}): {token_count:,}" # "Calculated" 제거
            self.last_token_count = token_count
        else:
            token_text = f"{selected_llm} 토큰 계산 오류"
            print(f"Token calculation failed for {selected_llm}, {model_name}.")

        print(f"Updating token label to: {token_text}")
        self.mw.token_count_label.setText(token_text)
        QApplication.processEvents()

    def on_llm_selected(self):
        """Handles the selection change in the LLM dropdown."""
        selected_llm = self.mw.llm_combo.currentText()
        available_models = self.config_service.get_available_models(selected_llm)

        self.mw.model_name_combo.blockSignals(True)
        self.mw.model_name_combo.clear()
        self.mw.model_name_combo.addItems(available_models)
        self.mw.model_name_combo.blockSignals(False)

        default_model = self.config_service.get_default_model_name(selected_llm)
        default_index = self.mw.model_name_combo.findText(default_model)
        if default_index != -1:
            self.mw.model_name_combo.setCurrentIndex(default_index)
        elif available_models:
            self.mw.model_name_combo.setCurrentIndex(0)
            print(f"Warning: Default model '{default_model}' not found. Selecting first available.")
        else:
             print(f"Warning: No available models found for {selected_llm}.")

        self.reset_token_label()
        self.update_char_count_for_active_tab()

        is_gemini_selected = (selected_llm == "Gemini")
        if hasattr(self.mw, 'gemini_param_widget'):
            self.mw.gemini_param_widget.setVisible(is_gemini_selected)

    # --- Attachment Handling ---
    def attach_files(self):
        """Opens a file dialog to select multiple files for attachment."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "정보", "Meta Prompt Builder 모드에서는 파일 첨부가 필요 없습니다.")
            return

        start_dir = self.mw.current_project_folder if self.mw.current_project_folder else os.path.expanduser("~")
        # getOpenFileNames는 파일 경로 리스트와 필터 문자열을 반환
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.mw,
            "파일 첨부",
            start_dir,
            "모든 파일 (*.*);;이미지 파일 (*.png *.jpg *.jpeg *.webp);;텍스트 파일 (*.txt *.md *.py *.json *.yaml *.yml *.html *.css *.js)"
        )

        if file_paths:
            added_count = 0
            for file_path in file_paths:
                if not os.path.exists(file_path): continue

                file_name = os.path.basename(file_path)
                # 중복 체크 (경로 기준)
                if any(item.get('path') == file_path for item in self.mw.attached_items):
                    print(f"Skipping duplicate attachment: {file_name}")
                    continue

                # 파일 타입 추정 (이미지 vs 일반 파일)
                mime_type, _ = mimetypes.guess_type(file_path)
                item_type = 'image' if mime_type and mime_type.startswith('image/') else 'file'

                # 첨부 목록에 추가 (데이터는 필요 시 로드)
                attachment_info = {
                    "type": item_type,
                    "path": file_path,
                    "name": file_name,
                    "data": None # 필요 시 로드하도록 None으로 초기화
                }
                self.mw.attached_items.append(attachment_info)
                added_count += 1

            if added_count > 0:
                self.mw._update_attachment_list_ui() # UI 업데이트
                self.mw.status_bar.showMessage(f"{added_count}개 파일 첨부 완료.")
                self.reset_token_label() # 첨부 변경 시 토큰 리셋
            else:
                self.mw.status_bar.showMessage("선택한 파일이 이미 첨부되어 있거나 유효하지 않습니다.")

    def paste_from_clipboard(self):
        """Pastes image or file paths from the clipboard."""
        if self.mw.mode == "Meta Prompt Builder":
            QMessageBox.information(self.mw, "정보", "Meta Prompt Builder 모드에서는 클립보드 첨부가 필요 없습니다.")
            return

        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        added_count = 0

        if mime_data.hasImage():
            qimage = clipboard.image()
            if not qimage.isNull():
                # QImage를 bytes로 변환 (Pillow 사용 권장)
                image_data = None
                image_format = "PNG" # 기본 포맷
                if _PILLOW_AVAILABLE:
                    try:
                        pil_image = ImageQt(qimage).copy() # Pillow Image로 변환
                        # RGBA -> RGB 변환 (JPEG 저장 시 필요할 수 있음)
                        if pil_image.mode == 'RGBA':
                             pil_image = pil_image.convert('RGB')
                        # 메모리에 저장하여 bytes 얻기
                        import io
                        buffer = io.BytesIO()
                        # 이미지 포맷 결정 (예: PNG 또는 JPEG)
                        # 투명도 없으면 JPEG, 있으면 PNG 고려
                        save_format = "JPEG" if pil_image.mode == 'RGB' else "PNG"
                        pil_image.save(buffer, format=save_format)
                        image_data = buffer.getvalue()
                        image_format = save_format
                        print(f"Pasted image converted to {save_format} bytes.")
                    except Exception as e:
                        print(f"Error converting QImage with Pillow: {e}")
                else:
                    # Pillow 없으면 QBuffer 사용 시도 (덜 안정적일 수 있음)
                    try:
                        import io
                        from PyQt5.QtCore import QBuffer, QIODevice
                        buffer = QBuffer()
                        buffer.open(QIODevice.ReadWrite)
                        # PNG로 저장 시도
                        if qimage.save(buffer, "PNG"):
                            image_data = buffer.data().data() # QByteArray -> bytes
                            image_format = "PNG"
                            print("Pasted image converted to PNG bytes using QBuffer.")
                        else:
                            print("Failed to save QImage using QBuffer.")
                        buffer.close()
                    except Exception as e:
                        print(f"Error converting QImage with QBuffer: {e}")


                if image_data:
                    # 중복 체크 (데이터 기준 - 비효율적일 수 있음)
                    # if any(item.get('data') == image_data for item in self.mw.attached_items if item['type'] == 'image'):
                    #     print("Skipping duplicate image data from clipboard.")
                    # else:
                    # 임시 이름 생성
                    import time
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    image_name = f"clipboard_image_{timestamp}.{image_format.lower()}"
                    attachment_info = {
                        "type": "image",
                        "path": None, # 클립보드 이미지는 경로 없음
                        "name": image_name,
                        "data": image_data
                    }
                    self.mw.attached_items.append(attachment_info)
                    added_count += 1
                    print(f"Image pasted from clipboard: {image_name}")

        elif mime_data.hasUrls():
            urls = mime_data.urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.exists(file_path):
                        file_name = os.path.basename(file_path)
                        # 중복 체크 (경로 기준)
                        if any(item.get('path') == file_path for item in self.mw.attached_items):
                            print(f"Skipping duplicate attachment from clipboard: {file_name}")
                            continue

                        mime_type, _ = mimetypes.guess_type(file_path)
                        item_type = 'image' if mime_type and mime_type.startswith('image/') else 'file'

                        attachment_info = {
                            "type": item_type,
                            "path": file_path,
                            "name": file_name,
                            "data": None
                        }
                        self.mw.attached_items.append(attachment_info)
                        added_count += 1
                        print(f"File path pasted from clipboard: {file_name}")
                    else:
                        print(f"Ignoring non-existent file path from clipboard: {file_path}")
                else:
                    print(f"Ignoring non-local URL from clipboard: {url.toString()}")

        if added_count > 0:
            self.mw._update_attachment_list_ui()
            self.mw.status_bar.showMessage(f"{added_count}개 항목 클립보드에서 첨부 완료.")
            self.reset_token_label() # 첨부 변경 시 토큰 리셋
        else:
            self.mw.status_bar.showMessage("클립보드에 첨부할 수 있는 이미지나 파일 경로가 없습니다.")

    def remove_selected_attachment(self):
        """Removes the selected item from the attachment list."""
        if not hasattr(self.mw, 'attachment_list_widget'): return

        selected_items = self.mw.attachment_list_widget.selectedItems()
        if not selected_items:
            self.mw.status_bar.showMessage("제거할 첨부 파일을 선택하세요.")
            return

        removed_count = 0
        # 리스트 위젯에서 선택된 항목의 인덱스를 가져와 역순으로 제거 (인덱스 변경 방지)
        selected_indices = sorted([self.mw.attachment_list_widget.row(item) for item in selected_items], reverse=True)

        for index in selected_indices:
            if 0 <= index < len(self.mw.attached_items):
                removed_item = self.mw.attached_items.pop(index)
                self.mw.attachment_list_widget.takeItem(index) # UI에서도 제거
                print(f"Removed attachment: {removed_item.get('name')}")
                removed_count += 1

        if removed_count > 0:
            self.mw.status_bar.showMessage(f"{removed_count}개 첨부 파일 제거 완료.")
            self.reset_token_label() # 첨부 변경 시 토큰 리셋
        else:
             self.mw.status_bar.showMessage("첨부 파일 제거 중 오류 발생.")
