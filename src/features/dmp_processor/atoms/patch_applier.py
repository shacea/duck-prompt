import logging
from pathlib import Path
import patch  # Assumes python-patch library is installed

logger = logging.getLogger(__name__)

class PatchApplier:
    """Applies a unified diff patch to a directory."""

    @staticmethod
    def apply_patch(patch_text: str, root_dir: Path) -> tuple[bool, str]:
        """
        Applies the given patch text to the specified root directory.

        Args:
            patch_text: The unified diff patch string.
            root_dir: The root directory to apply the patch against.

        Returns:
            A tuple containing a success boolean and a message.
        """
        try:
            # The python-patch library expects bytes, so we encode the string.
            patch_set = patch.fromstring(patch_text.encode('utf-8'))
            if not patch_set:
                return False, "패치 텍스트를 파싱할 수 없습니다. 형식이 올바른지 확인하세요."

            # Apply the patch.
            if patch_set.apply(root=root_dir):
                logger.info(f"Successfully applied patch to root: {root_dir}")
                # Provide a more detailed success message
                patched_files = [p.path for p in patch_set.items]
                return True, f"패치가 성공적으로 적용되었습니다.\n수정된 파일: {', '.join(patched_files)}"
            else:
                # python-patch can fail if the source files are different.
                # It returns False, but doesn't raise an exception.
                logger.error(f"Failed to apply patch to root: {root_dir}. Some hunks may have failed.")
                return False, "패치 적용에 실패했습니다. 원본 파일의 내용이 패치가 생성될 때와 다를 수 있습니다."

        except Exception as e:
            logger.error(f"Exception while applying patch: {e}", exc_info=True)
            return False, f"패치 적용 중 예외 발생: {e}"
