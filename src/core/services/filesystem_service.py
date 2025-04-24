import os
import fnmatch
from typing import Set, List

class FilesystemService:
    def __init__(self, config_service): # ConfigService 주입
        self.config_service = config_service

    def load_gitignore_patterns(self, project_folder: str) -> Set[str]:
        """Loads .gitignore patterns from the project folder and combines with defaults."""
        gitignore_path = os.path.join(project_folder, ".gitignore")
        settings = self.config_service.get_settings()
        # 기본 무시 목록으로 시작
        patterns = set(settings.default_ignore_list)

        if os.path.isfile(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                # 주석과 빈 줄 제외하고 패턴 추가
                lines = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]
                patterns.update(lines)
            except Exception as e:
                print(f"Error loading .gitignore file {gitignore_path}: {e}")
                # 오류 발생 시 기본값만 사용

        # 설정에 직접 저장된 제외 목록도 추가 (config.yml)
        patterns.update(settings.excluded_dirs)
        return patterns

    def should_ignore(self, file_path: str, project_root: str, ignore_patterns: Set[str], is_dir: bool) -> bool:
        """Checks if a file/directory should be ignored based on patterns."""
        if not project_root or not file_path.startswith(project_root):
            return False # 프로젝트 루트 외부는 무시하지 않음

        if file_path == project_root:
            return False # 프로젝트 루트 자체는 무시하지 않음

        file_name = os.path.basename(file_path)
        try:
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
        except ValueError:
            # 다른 드라이브 등 상대 경로 계산 불가 시 무시하지 않음
            return False

        for pattern in ignore_patterns:
            # 패턴 정리 및 디렉토리 패턴 여부 확인
            is_dir_pattern = pattern.endswith('/')
            cleaned_pattern = pattern.rstrip('/')

            # 디렉토리 패턴인데 현재 항목이 파일이면 건너뜀
            if is_dir_pattern and not is_dir:
                continue

            # 1. 파일 이름 매칭 (e.g., *.log, __pycache__)
            if fnmatch.fnmatch(file_name, cleaned_pattern):
                # 디렉토리 패턴이면 디렉토리만 매칭
                if is_dir_pattern and is_dir:
                    return True
                # 파일 패턴이면 파일/디렉토리 모두 매칭 (gitignore 기본 동작)
                elif not is_dir_pattern:
                    return True

            # 2. 상대 경로 매칭 (e.g., build/, docs/temp.txt)
            # 디렉토리일 경우, 경로 끝에 '/' 추가하여 매칭
            match_path = relative_path + '/' if is_dir else relative_path
            if fnmatch.fnmatch(match_path, pattern):
                 return True
            # 패턴에 /가 포함되어 있고, 디렉토리 패턴이 아닐 때도 경로 매칭 시도
            # (e.g. 'some/dir/file.txt' 패턴)
            if '/' in pattern and not is_dir_pattern:
                 if fnmatch.fnmatch(relative_path, pattern):
                     return True

        return False # 어떤 패턴과도 매치되지 않으면 무시하지 않음

    def get_directory_tree(self, paths: List[str], project_root: str) -> str:
        """Builds a directory tree structure string from a list of paths."""
        if not paths or not project_root:
            return "No items selected or project root not set."

        tree = {}
        visible_paths = [] # 실제 존재하는 경로만 필터링 (필요시)
        for p in paths:
            if os.path.exists(p):
                 visible_paths.append(p)

        if not visible_paths:
            return "No valid items selected."

        for p in visible_paths:
            try:
                rel_path = os.path.relpath(p, project_root)
            except ValueError:
                continue # 다른 드라이브 등 relpath 계산 불가 시 건너뜀
            parts = rel_path.split(os.sep)
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        def print_tree(subtree, current_path, indent=0):
            lines = []
            indent_str = "  " * indent
            entries = sorted(subtree.keys())
            dirs = []
            files = []

            for entry in entries:
                full_path = os.path.join(current_path, entry)
                if os.path.isdir(full_path):
                    dirs.append(entry)
                elif os.path.isfile(full_path):
                    files.append(entry)

            for d in dirs:
                lines.append(f"{indent_str} 📁 {d}/")
                lines.extend(print_tree(subtree[d], os.path.join(current_path, d), indent + 1))
            for f in files:
                size = 0
                full_file_path = os.path.join(current_path, f)
                try:
                    size = os.path.getsize(full_file_path)
                except OSError:
                    size = 0
                lines.append(f"{indent_str} 📄 {f} ({size:,} bytes)")
            return lines

        root_folder_name = os.path.basename(project_root)
        root_lines = [f"File Tree:", f" 📁 {root_folder_name}/"]
        root_lines.extend(print_tree(tree, project_root, 1))

        return "\n".join(root_lines)

# 사용 예시 (Controller에서):
# config_service = ConfigService()
# fs_service = FilesystemService(config_service)
# ignore_patterns = fs_service.load_gitignore_patterns(project_folder)
# should_ignore = fs_service.should_ignore(file_path, project_folder, ignore_patterns, is_dir)
# tree_string = fs_service.get_directory_tree(checked_paths, project_folder)
