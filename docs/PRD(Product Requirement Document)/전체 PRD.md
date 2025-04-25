# 전체 PRD

## 프로젝트명

DuckPrompt (덕 프롬프트)

## 개요

DuckPrompt는 여러 파일 내용을 쉽게 통합하여 LLM에게 넘길 수 있는 프롬프트를 생성하는 **GUI 도구**입니다.

- **코드 강화 빌더 모드**: 특정 디렉토리(또는 파일)를 선택하여, 시스템 프롬프트 + 사용자 프롬프트 + 선택한 파일의 내용을 하나로 합칩니다.
- **메타 프롬프트 빌더 모드**: 이미 만들어진 하나의 프롬프트를 상위 템플릿(메타 프롬프트)으로 감싸, 새로운 맥락의 프롬프트를 생성합니다.

## 주요 목표

1. **파일 선택 및 통합**: 다수의 파일을 선택 후 자동으로 내용을 합쳐 제공.
2. **시스템 / 사용자 프롬프트 분리**: 시스템 / 사용자 프롬프트를 탭으로 구분하여 편집 용이성 확보.
3. **디렉토리 구조 시각화**: 선택된 파일과 폴더 구조를 한눈에 확인.
4. **XML 파서 연동**: XML 형식으로 정리된 수정 사항을 자동으로 해당 파일에 반영 (파일 생성/수정/삭제).
5. **템플릿/상태 관리**: 리소스 관리 뷰를 통해 템플릿(프롬프트) 및 현재 상태를 불러오기/저장/백업/복원.
6. **설정 관리**: 환경 설정 다이얼로그를 통해 기본 시스템 프롬프트, LLM 모델명, API 키, 필터링 규칙 등 관리 (`config.yml`).
7. **토큰 계산**: GPT(`tiktoken`), Gemini(API), Claude(API) 모델별 토큰 수 계산 기능 제공.

## 세부 요구사항

- **GUI**: PyQt5 기반으로 마우스 클릭만으로 직관적 조작.
- **설정 관리**: `config.yml` 파일을 통해 확장자, 제외 목록, 기본 모델명, API 키 등 설정 관리. 환경 설정 다이얼로그 제공.
- **상태 관리**: Pydantic 모델(`AppState`)을 사용하여 애플리케이션 상태 관리 및 JSON 파일로 저장/로드.
- **토큰 계산 기능**: `tiktoken` (GPT) 및 각 LLM 제공사 API (`google-generativeai`, `anthropic`)를 사용한 토큰 수 추정.
- **배포**: PyInstaller를 통해 Windows 환경에서 단일 실행 파일 형태로 배포 가능 (AMD64, ARM64).
- **서비스 지향 아키텍처**: 핵심 로직을 서비스 계층으로 분리하여 재사용성 및 테스트 용이성 확보.

## 프로젝트 아키텍처 (간단 요약)

- **`main.py`**: 최상위 진입점, `sys.path` 설정 및 `src/app.py` 호출.
- **`src/app.py`**: QApplication 초기화, `MainWindow` 생성 및 실행. (DPI 설정 등)
- **`src/config.yml`**: 애플리케이션 설정 파일 (YAML 형식). API 키, 기본 모델명, 필터 규칙 등 포함.
- **`src/core/`**: 핵심 비즈니스 로직 및 데이터 모델.
  - **`pydantic_models/`**: Pydantic 모델 정의 (`AppState`, `ConfigSettings`).
  - **`services/`**: 핵심 기능 서비스 구현 (`ConfigService`, `FilesystemService`, `PromptService`, `StateService`, `TemplateService`, `XmlService`, `TokenCalculationService`, `GeminiService`).
  - **`langgraph_state.py`**: LangGraph 상태 정의 (`GeminiGraphState`).
- **`src/ui/`**: 사용자 인터페이스 관련 코드.
  - **`controllers/`**: UI 이벤트 처리 및 서비스 계층 호출 (`FileTreeController`, `MainController`, `PromptController`, `ResourceController`, `XmlController`, `system_prompt_controller` 함수).
  - **`models/`**: UI 관련 모델 (`FilteredFileSystemModel`, `CheckableProxyModel`).
  - **`widgets/`**: 커스텀 UI 위젯 (`CustomTabBar`, `CustomTextEdit`, `tab_manager`, `check_box_delegate`).
  - **`main_window.py`**: 메인 UI 창 정의 및 위젯 배치, 컨트롤러/서비스 초기화 및 연결. LangGraph 실행 로직 포함.
  - **`main_window_setup_ui.py`**: 메인 윈도우 UI 요소 생성 로직 분리.
  - **`main_window_setup_signals.py`**: 메인 윈도우 시그널 연결 로직 분리.
  - **`settings_dialog.py`**: 환경 설정 다이얼로그 UI 및 로직.
- **`src/utils/`**: 보조 유틸리티 함수.
  - **`helpers.py`**: 경로 관리, 텍스트 계산 등. (tiktoken 초기화 로직 제거)
- **`resources/`**: 아이콘, 프롬프트 템플릿, 상태 파일 등 리소스 저장.
  - `status/`: 상태 저장 파일(`.json`) 기본 저장 위치.
- **`docs/`**: 문서 (PRD 등).
- **Build/Dependency Files**: `app_*.spec`, `build.bat`, `pyproject.toml`, `requirements*.txt`, `uv.lock`.

## 비기능적 요구사항

- **코드 가독성 및 유지보수성**: 서비스 계층 분리, Pydantic 모델 사용, 타입 힌트 적용, UI 로직 분리.
- **로그**: 표준 출력 및 상태 표시줄을 통해 사용자에게 정보/오류 안내.
- **성능**: 파일 시스템 모델 최적화, API 기반 토큰 계산 시 UI 블로킹 최소화 (LangGraph Worker 스레드 사용).

## 테스트 및 검증

- (향후 추가 예정) 단위 테스트 및 통합 테스트.
- XML 파서 동작 시, 임시 폴더에서 테스트 진행.
- 폴더 구조가 큰 경우도 안정적으로 동작하는지 확인.
- 다양한 LLM 모델명 및 API 키 설정 시 토큰 계산 동작 확인.
- LangGraph Worker 스레드 동작 및 UI 응답성 확인.

## 기타

- 자세한 파일별 설명은 [파일별 기능 상세](파일별 기능 상세.md) 문서를 참고하세요.