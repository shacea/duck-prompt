# 전체 PRD

## 프로젝트명

DuckPrompt (덕 프롬프트)

## 개요

DuckPrompt는 여러 파일 내용과 첨부 파일(이미지, 일반 파일)을 쉽게 통합하여 LLM(대규모 언어 모델)에게 전달할 프롬프트를 생성하는 **GUI 도구**입니다. Gemini API와 직접 연동하여 프롬프트를 전송하고 구조화된 응답(XML, 요약)을 받을 수 있습니다. **설정, API 키, 모델 목록 등 주요 정보는 PostgreSQL 데이터베이스에서 관리됩니다.**

- **코드 강화 빌더 모드**: 특정 디렉토리(또는 파일) 및 첨부 파일을 선택하여, 시스템 프롬프트 + 사용자 프롬프트 + 선택한 파일 내용 + 첨부 파일 정보를 하나로 합칩니다. Gemini API 직접 호출 및 응답 처리 기능 포함.
- **메타 프롬프트 빌더 모드**: 이미 만들어진 하나의 프롬프트를 상위 템플릿(메타 프롬프트)으로 감싸, 새로운 맥락의 프롬프트를 생성합니다.

## 주요 목표

1.  **파일 및 첨부 파일 통합**: 다수의 파일 및 첨부 파일(이미지, 일반 파일)을 선택 후 자동으로 내용을 합쳐 제공.
2.  **시스템 / 사용자 프롬프트 분리**: 시스템 / 사용자 프롬프트를 탭으로 구분하여 편집 용이성 확보.
3.  **디렉토리 구조 시각화**: 선택된 파일과 폴더 구조를 한눈에 확인.
4.  **XML 파서 연동**: LLM이 생성한 XML 형식의 수정 사항을 자동으로 해당 파일에 반영 (파일 생성/수정/삭제).
5.  **템플릿/상태 관리**: 리소스 관리 뷰를 통해 템플릿(프롬프트) 및 현재 상태를 불러오기/저장. **"⏪ 마지막 작업 불러오기" 버튼 제공.**
6.  **설정 관리 (DB 기반)**: **PostgreSQL 데이터베이스**에 설정(기본 시스템 프롬프트, LLM 모델 목록/기본값, 필터링 규칙, Gemini 파라미터), API 키, 모델별 Rate Limit 정보 저장 및 관리. 환경 설정 메뉴에서 DB 설정 확인 및 `.gitignore` 편집/저장 기능 제공.
7.  **토큰 계산**: GPT(`tiktoken`), Gemini(API, 멀티모달 지원), Claude(API) 모델별 토큰 수 계산 기능 제공. DB에 저장된 API 키 사용.
8.  **Gemini API 직접 연동**: 생성된 프롬프트와 첨부 파일을 LangGraph 워크플로우를 통해 Gemini API로 직접 전송하고, 구조화된 응답(XML, 요약)을 받아 UI에 표시. **DB 기반 API 키 관리(사용량 기반 자동 선택/회전, Rate Limit 체크) 및 로깅 기능 포함.**

## 세부 요구사항

- **GUI**: PyQt6 기반으로 마우스 클릭만으로 직관적 조작. 파일/이미지 첨부 및 관리 UI 제공. **"⏪ 마지막 작업 불러오기" 버튼 추가.**
- **설정 관리**: **PostgreSQL 데이터베이스**에 설정 저장. 환경 설정 메뉴에서 설정 확인 및 `.gitignore` 편집/저장 가능. API 키 및 사용 가능 모델 목록 관리 기능 제공.
- **상태 관리**: Pydantic 모델(`AppState`)을 사용하여 애플리케이션 상태 관리 및 JSON 파일로 저장/로드 (첨부 파일 정보 포함).
- **토큰 계산 기능**: `tiktoken` (GPT) 및 각 LLM 제공사 API (`google-generativeai`, `anthropic`)를 사용한 토큰 수 추정 (Gemini는 멀티모달 입력 지원). DB에 저장된 API 키 사용.
- **Gemini API 연동**: LangGraph를 사용하여 Gemini API 호출 워크플로우 구성. 비동기 처리(QThread)로 UI 응답성 유지. 멀티모달 입력(텍스트+이미지/파일) 지원. 구조화된 응답(XML, 요약) 파싱. **DB 기반 API 키 관리(사용량 기반 자동 선택/회전, Rate Limit 체크) 및 DB 로깅 연동.**
- **배포**: PyInstaller를 통해 Windows 환경에서 단일 실행 파일 형태로 배포 가능 (AMD64, ARM64). Pillow, LangGraph, psycopg2-binary 등 의존성 포함.
- **서비스 지향 아키텍처**: 핵심 로직을 서비스 계층으로 분리하여 재사용성 및 테스트 용이성 확보.

## 프로젝트 아키텍처 (간단 요약)

- **`main.py`**: 최상위 진입점, `sys.path` 설정 및 `src/app.py` 호출.
- **`src/app.py`**: QApplication 초기화, `MainWindow` 생성 및 실행. (DPI 설정, DB 로그 정리 시도 등)
- **`src/core/`**: 핵심 비즈니스 로직 및 데이터 모델.
  - **`pydantic_models/`**: Pydantic 모델 정의 (`AppState`, `ConfigSettings`). `AppState`에 `attached_items` 추가. `ConfigSettings`는 DB 스키마 반영 (API 키 필드 제거, 모델 목록, Gemini 파라미터 등).
  - **`services/`**: 핵심 기능 서비스 구현 (`ConfigService`, `DbService`, `FilesystemService`, `PromptService`, `StateService`, `TemplateService`, `XmlService`, `TokenCalculationService`, `GeminiService`).
    - **`DbService`**: PostgreSQL 데이터베이스 상호작용 담당 (설정, API 키, 모델 목록, Rate Limit, 로그 관리).
    - **`ConfigService`**: `DbService`를 사용하여 DB 기반 설정 관리. API 키 선택/관리 로직 포함.
    - **`GeminiService`**: LangGraph 기반 워크플로우 빌드 및 Gemini API 호출 노드 구현. **DB 연동 강화 (키 선택/회전, Rate Limit 체크, 로깅).**
    - **`TokenCalculationService`**: 멀티모달 입력(첨부 파일)을 고려한 Gemini 토큰 계산 로직. **DB에서 API 키 로드.**
    - `PromptService`: 첨부 파일 정보를 프롬프트에 포함하는 로직 추가.
    - `StateService`: `attached_items` 상태 저장/로드 로직 추가.
    - `XmlService`: XML 파싱 전 Markdown 코드 블록 제거 로직 추가.
  - **`langgraph_state.py`**: LangGraph 상태 정의 (`GeminiGraphState`). `input_attachments`, `selected_model_name`, `log_id` 추가됨.
- **`src/ui/`**: 사용자 인터페이스 관련 코드.
  - **`controllers/`**: UI 이벤트 처리 및 서비스 계층 호출 (`FileTreeController`, `MainController`, `PromptController`, `ResourceController`, `XmlController`, `system_prompt_controller` 함수).
    - `MainController`: 첨부 파일 관리, Gemini API 호출 시작, 토큰 계산 시작, 상태 표시줄 업데이트(API 시간 포함).
    - `ResourceController`: 상태 로드 시 `partial_load` 옵션 처리.
  - **`models/`**: UI 관련 모델 (`FilteredFileSystemModel`, `CheckableProxyModel`).
  - **`widgets/`**: 커스텀 UI 위젯 (`CustomTabBar`, `CustomTextEdit`, `tab_manager`, `check_box_delegate`).
  - **`main_window.py`**: 메인 UI 창 정의 및 위젯 배치, 컨트롤러/서비스 초기화 및 연결. LangGraph Worker 스레드(`GeminiWorker`) 생성 및 관리, Gemini API 응답 처리 슬롯 구현. 첨부 파일 목록 UI(`QListWidget`) 관리. 상태 표시줄 API 시간 표시. **DB 기반 설정 로드 및 적용.**
  - **`main_window_setup_ui.py`**: 메인 윈도우 UI 요소 생성 로직 분리. **"⏪ 마지막 작업 불러오기" 버튼 추가.** **"파일" 메뉴 제거, "환경 설정" 메뉴 추가.** 첨부 파일 관리 그룹 및 리스트 위젯 추가. 상태 표시줄 API 시간 라벨 추가. LLM 컨트롤 상단 이동.
  - **`main_window_setup_signals.py`**: 메인 윈도우 시그널 연결 로직 분리. **"⏪ 마지막 작업 불러오기" 버튼 시그널 연결.** 첨부 파일 버튼 시그널 연결.
  - **`settings_dialog.py`**: 환경 설정 다이얼로그 UI 및 로직. **DB 설정 확인 및 API 키/모델 목록 관리 기능 추가.** `.gitignore` 편집/저장 기능.
- **`src/utils/`**: 보조 유틸리티 함수.
  - **`helpers.py`**: 경로 관리, 텍스트 계산 등.
  - **`postgres_db_initializer.py`**: PostgreSQL DB 스키마 생성 및 초기 데이터 로드 스크립트.
  - **`db_migration_script.py`**: DB 스키마 마이그레이션 스크립트 (api_key_usage -> api_keys).
- **`resources/`**: 아이콘, 프롬프트 템플릿, 상태 파일 등 리소스 저장.
  - `status/`: 상태 저장 파일(`.json`) 기본 저장 위치.
- **`docs/`**: 문서 (PRD 등).
- **Build/Dependency Files**: `app_*.spec`, `build.bat`, `pyproject.toml`. Pillow, LangGraph, psycopg2-binary 등 의존성 추가됨.

## 비기능적 요구사항

- **코드 가독성 및 유지보수성**: 서비스 계층 분리, Pydantic 모델 사용, 타입 힌트 적용, UI 로직 분리.
- **로그**: 표준 출력 및 상태 표시줄을 통해 사용자에게 정보/오류 안내. 상세 로그는 터미널/콘솔 확인. **Gemini API 호출 로그는 DB에 저장.**
- **성능**: 파일 시스템 모델 최적화, API 기반 토큰 계산 및 Gemini API 호출 시 UI 블로킹 최소화 (LangGraph Worker 스레드 사용).

## 테스트 및 검증

- (향후 추가 예정) 단위 테스트 및 통합 테스트.
- XML 파서 동작 시, 임시 폴더에서 테스트 진행.
- 폴더 구조가 큰 경우도 안정적으로 동작하는지 확인.
- 다양한 LLM 모델명 및 API 키 설정 시 토큰 계산 동작 확인 (멀티모달 포함).
- LangGraph Worker 스레드 동작 및 UI 응답성 확인.
- 파일/이미지 첨부 및 제거 기능 동작 확인.
- Gemini API 직접 호출 및 응답(XML/Summary) 처리 확인.
- **DB 기반 API 키 선택/회전 및 Rate Limit 동작 확인.**

## 기타

- 자세한 파일별 설명은 [파일별 기능 상세](파일별 기능 상세.md) 문서를 참고하세요.
- 데이터베이스 스키마 정보는 [DB 스키마](PRD_db.md) 문서를 참고하세요.
