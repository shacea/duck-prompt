
PROTECTED_TABS = {"Template Manager", "File Tree", "Prompt Output", "+", "Meta Prompt Output", "   |   ", "META Prompt", "user-prompt", "Final Prompt", "META Prompt Template", "META User Input"}

def is_tab_deletable(tab_name: str) -> bool:
    return tab_name not in PROTECTED_TABS
