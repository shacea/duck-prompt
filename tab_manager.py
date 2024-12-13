# 탭 속성 관리 모듈
PROTECTED_TABS = {"Template Manager", "File Tree", "Prompt Output", "+"}

def is_tab_deletable(tab_name: str) -> bool:
    # PROTECTED_TABS에 없는 탭은 삭제 가능
    return tab_name not in PROTECTED_TABS
