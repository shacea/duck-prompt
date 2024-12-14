PROTECTED_TABS = {"Template Manager", "File Tree", "Prompt Output", "+"}

def is_tab_deletable(tab_name: str) -> bool:
    return tab_name not in PROTECTED_TABS
