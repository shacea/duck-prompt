
class Config:
    def __init__(self):
        # 기본 허용 확장자 (비어 있으면 모든 파일 허용)
        self.allowed_extensions = set()
        # 폴더 및 파일 무시 목록(하위 파일까지 체크되지 않도록)
        self.excluded_dirs = set()

        # 기본 무시 목록(유저 편집 가능)
        self.default_ignore_list = [
            "__pycache__/",
            ".git/",
            ".gitignore",
            ".windsurfrules",
            ".cursorrules"
        ]

config = Config()
