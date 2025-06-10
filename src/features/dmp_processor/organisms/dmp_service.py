import logging
import re
from pathlib import Path
from src.gateway import ServiceLocator
from ..atoms.patch_applier import PatchApplier

logger = logging.getLogger(__name__)

class DmpService:
    """High-level service for handling DMP operations."""

    def __init__(self):
        self.patch_applier = PatchApplier()

    def _split_patches(self, unified_patch_text: str) -> list[tuple[str, str]]:
        """Splits a unified diff text containing multiple files into individual patches."""
        # Split by the file header, keeping the header with the content
        # The pattern looks for '--- ' at the beginning of a line.
        # We use a positive lookahead `(?=^--- )` to split without consuming the delimiter.
        patch_chunks = re.split(r'(?=^--- .*\n)', unified_patch_text, flags=re.MULTILINE)
        
        file_patches = []
        for chunk in patch_chunks:
            if not chunk.strip():
                continue
            
            # Extract file path from '--- a/path/to/file' or '--- /dev/null'
            # For new files, the target path is in the '+++' line
            from_path_match = re.search(r'^--- (?:a/)?(.+?)\n', chunk, flags=re.MULTILINE)
            to_path_match = re.search(r'^\+\+\+ (?:b/)?(.+?)\n', chunk, flags=re.MULTILINE)

            from_path = from_path_match.group(1).strip() if from_path_match else None
            to_path = to_path_match.group(1).strip() if to_path_match else None

            # Determine the definitive path for file operations
            # If a file is being created, from_path is /dev/null, use to_path
            # If a file is being deleted, to_path is /dev/null, use from_path
            # If a file is being modified, both should be the same
            path_str = to_path if from_path == '/dev/null' else from_path

            if path_str and path_str != '/dev/null':
                file_patches.append((path_str, chunk))
            else:
                 logger.warning(f"Could not determine file path for patch chunk:\n{chunk}")

        return file_patches

    async def apply_dmp_patch(self, patch_text: str) -> tuple[bool, str]:
        """
        Applies a DMP patch, potentially containing multiple files, to the workspace.
        """
        try:
            file_system_service = ServiceLocator.get("file_system")
            project_folder_str = file_system_service.get_project_folder()

            if not project_folder_str:
                return False, "프로젝트 폴더가 설정되지 않았습니다. 먼저 폴더를 선택해주세요."
            
            project_root = Path(project_folder_str)
            
            # Split the unified patch into per-file patches
            file_patches = self._split_patches(patch_text)

            if not file_patches:
                return False, "패치 텍스트에서 유효한 파일 변경사항을 찾을 수 없습니다. (헤더 '--- a/...' 누락?)"

            applied_files = []
            errors = []

            for file_path_str, single_patch_text in file_patches:
                target_file_path = project_root / file_path_str

                # For new files, the original text is empty.
                original_text = ""
                is_new_file = "--- /dev/null" in single_patch_text
                
                if not is_new_file and target_file_path.exists():
                    original_text = target_file_path.read_text(encoding='utf-8')
                elif is_new_file:
                    # Ensure parent directory exists for new files
                    target_file_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Target file '{file_path_str}' does not exist. Treating as a new file.")
                elif not is_new_file and not target_file_path.exists():
                    errors.append(f"'{file_path_str}': 원본 파일을 찾을 수 없습니다.")
                    continue

                # Apply the patch for this specific file
                success, result_text = self.patch_applier.apply_patch(single_patch_text, original_text)

                if success:
                    target_file_path.write_text(result_text, encoding='utf-8')
                    applied_files.append(file_path_str)
                else:
                    errors.append(f"'{file_path_str}': {result_text}")

            if errors:
                error_message = "\n".join(errors)
                # Still refresh if some files succeeded
                if applied_files:
                    file_system_service.refresh_file_system()
                    return False, f"일부 파일 패치 적용 실패:\n{error_message}\n\n성공한 파일: {', '.join(applied_files)}"
                return False, f"패치 적용 실패:\n{error_message}"

            # Refresh the file system to reflect all changes in the UI
            file_system_service.refresh_file_system()
            
            success_message = f"패치가 성공적으로 적용되었습니다.\n수정된 파일: {', '.join(applied_files)}"
            return True, success_message

        except KeyError:
            logger.error("file_system service not found in ServiceLocator.")
            return False, "파일 시스템 서비스를 찾을 수 없습니다."
        except Exception as e:
            logger.error(f"Error in DmpService while applying patch: {e}", exc_info=True)
            return False, f"DMP 서비스 처리 중 오류 발생: {e}"
