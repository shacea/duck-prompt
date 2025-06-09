PROTECTED_TABS = {
    # 기본 UI 탭
    "시스템", "사용자", "파일 트리", "프롬프트 출력", "XML 입력", "Summary",
    # 기능성 탭
    "+", # 새 탭 추가 버튼
}

def is_tab_deletable(tab_name: str) -> bool:
    """Checks if a tab with the given name can be deleted or renamed by the user."""
    # 보호 목록에 없으면 삭제/이름 변경 가능
    return tab_name not in PROTECTED_TABS
