# 보호되어 사용자가 직접 닫거나 이름을 바꿀 수 없는 탭 이름 집합
# TODO: 이 목록을 설정 파일이나 다른 방식으로 관리하는 것 고려
PROTECTED_TABS = {
    # 기본 UI 탭
    "시스템", "사용자", "파일 트리", "프롬프트 출력", "XML 입력", # Code Enhancer 모드
    "메타 프롬프트 템플릿", "메타 사용자 입력", "메타 프롬프트 출력", # Meta Prompt 모드 (기본)
    "메타 프롬프트", "사용자 프롬프트", "최종 프롬프트", # Meta Prompt 모드 (추가)

    # 기능성 탭
    "+", # 새 탭 추가 버튼
    "   |   ", # 구분자 탭 (Meta Prompt 모드) - 현재 사용 안 함

    # 하드코딩된 변수 탭 이름 (더 나은 방식 필요)
    # "var-...", # 동적으로 생성되는 탭 이름 규칙에 따라 달라짐

    # 이전 버전 호환성 또는 다른 고정 탭 이름
    # "Template Manager", # 이전 버전 또는 다른 UI 요소 이름
    # "META Prompt Template", "META User Input", # 중복될 수 있으나 명시적 포함
    # "META Prompt", "user-prompt", "Final Prompt" # 중복될 수 있으나 명시적 포함
}

def is_tab_deletable(tab_name: str) -> bool:
    """Checks if a tab with the given name can be deleted or renamed by the user."""
    # 보호 목록에 없으면 삭제/이름 변경 가능
    return tab_name not in PROTECTED_TABS

# 사용 예시 (CustomTabBar에서):
# if is_tab_deletable(tab_text):
#     # 탭 닫기 또는 이름 변경 로직 수행
# else:
#     # 사용자에게 알림 (닫거나 변경할 수 없음)
