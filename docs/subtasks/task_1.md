# 리팩토링 1단계: 환경 설정, 구조 생성, Core 분리 및 Pydantic 도입 - 세부 작업 목록

## 목표

리팩토링 준비 완료, `src/` 구조 및 개발 환경 설정, Core 계층 분리 및 Pydantic 모델 도입, 초기 테스트 확보.

## Git 작업

- [ ] 새 브랜치 생성: `refactor/phase1-core-separation`
- [ ] 작업 내용을 작은 단위로 커밋 (의미 있는 메시지 사용)
- [ ] 파일 이동 시 `git mv` 사용하여 이력 추적

## 환경 설정

- [ ] Python 3.12 개발 환경 구성 (`uv venv` 또는 다른 가상환경 도구)
- [ ] `uv` 패키지 관리자 설치 및 기본 사용 설정

## 의존성 관리

- [ ] `requirements.txt` 파일 업데이트 또는 생성:
  - `PyQt5`
  - `PyYAML` (config_service용)
  - `termcolor` (로깅 전략 변경 시 제거 고려)
  - `tiktoken`
  - `python-dotenv`
  - `pydantic>=2.0`
- [ ] `requirements-dev.txt` 파일 생성:
  - `pytest`
  - `pytest-qt`
  - `pytest-mock`
  - `pytest-cov`
  - `ruff`
  - `black`
  - `mypy`
  - `radon`
  - `uv`
- [ ] `uv pip install -r requirements.txt` 실행
- [ ] `uv pip install -r requirements-dev.txt` 실행

## 프로젝트 설정 (`pyproject.toml`)

- [ ] `pyproject.toml` 파일 생성
- [ ] `[project]` 섹션 정의 (이름, 버전, 설명, 의존성 등)
- [ ] `[build-system]` 섹션 정의 (`hatchling` 사용)
- [ ] `[tool.uv]` 섹션 추가 (필요시 설정)
- [ ] `[tool.ruff]` 섹션 설정 (규칙셋, 대상 경로 등)
- [ ] `[tool.black]` 섹션 설정 (라인 길이 등)
- [ ] `[tool.mypy]` 섹션 설정 (Python 버전, **pydantic 플러그인 활성화**, 대상 경로 등)
- [ ] `[tool.pytest.ini_options]` 섹션 설정 (테스트 경로, `pythonpath` 설정 등)
- [ ] `[tool.coverage.run]` 및 `[tool.coverage.report]` 섹션 설정 (커버리지 측정 대상 및 기준)

## 디렉토리 구조 생성

- [ ] `src/` 디렉토리 생성
- [ ] `src/core/`, `src/ui/`, `src/utils/` 디렉토리 생성
- [ ] `src/core/pydantic_models/`, `src/core/services/` 디렉토리 생성
- [ ] `src/ui/controllers/`, `src/ui/models/`, `src/ui/widgets/` 디렉토리 생성
- [ ] `tests/` 디렉토리 생성 (루트 레벨)
- [ ] `tests/core/`, `tests/ui/`, `tests/utils/` 디렉토리 생성
- [ ] `tests/core/pydantic_models/`, `tests/core/services/` 디렉토리 생성
- [ ] `tests/ui/models/` 디렉토리 생성
- [ ] 각 생성된 패키지 디렉토리에 `__init__.py` 파일 추가

## 파일 이동 및 엔트리 포인트 생성

- [ ] 기존 `.py` 파일들을 `src/` 아래의 적절한 하위 디렉토리로 이동 (`git mv` 사용):
  - `app.py` -> `src/app.py`
  - `config.py` -> 삭제 (대체됨)
  - `custom_text_edit.py` -> `src/ui/widgets/custom_text_edit.py`
  - `file_explorer.py` -> `src/ui/models/file_system_models.py`
  - `main_controller.py` -> `src/ui/controllers/main_controller.py`
  - `main_window.py` -> `src/ui/main_window.py`
  - `parse_xml_string.py` -> 삭제 (대체됨)
  - `prompt_manager.py` -> 삭제 (대체됨)
  - `state_manager.py` -> 삭제 (대체됨)
  - `system_prompt_controller.py` -> `src/ui/controllers/system_prompt_controller.py`
  - `tab_manager.py` -> `src/ui/widgets/tab_manager.py`
  - `template_manager.py` -> 삭제 (대체됨)
  - `utils.py` -> 삭제 (대체됨)
- [ ] 루트 경로에 `main.py` 생성 (내용: `src/app.py` 임포트 및 실행)
- [ ] `src/app.py` 수정 (애플리케이션 설정 및 메인 윈도우 실행 로직)

## Import 경로 수정

- [ ] `src/` 내부의 모든 `.py` 파일에서 `import` 구문을 절대 경로 (`from src...` 또는 `from core...`, `from ui...` 등) 방식으로 수정

## Core 계층 분리 및 Pydantic 도입

- [ ] `src/core/pydantic_models/app_state.py` 생성 및 `AppState` Pydantic 모델 정의
- [ ] `src/core/pydantic_models/config_settings.py` 생성 및 `ConfigSettings` Pydantic 모델 정의
- [ ] `src/config.yml` 파일 생성 및 기본 설정 구조 정의
- [ ] `src/core/services/config_service.py` 생성:
  - `ConfigService` 클래스 정의
  - `src/config.yml` 로드 및 `ConfigSettings` 모델로 파싱/검증 로직 구현
  - 설정 저장/업데이트 기능 구현
- [ ] `src/core/services/state_service.py` 생성:
  - `StateService` 클래스 정의
  - 기존 `state_manager.py` 기능 이전
  - 상태 저장/로드 시 `AppState` 모델 사용 (JSON 직렬화/역직렬화)
  - 상태 파일 CRUD, 백업/복원 기능 구현
- [ ] `src/core/services/template_service.py` 생성:
  - `TemplateService` 클래스 정의
  - 기존 `template_manager.py` 기능 이전 (템플릿 파일 CRUD)
- [ ] `src/core/services/xml_service.py` 생성:
  - `XmlService` 클래스 정의
  - 기존 `parse_xml_string.py` 기능 이전 (XML 파싱 및 파일 변경 적용)
- [ ] `src/core/services/prompt_service.py` 생성:
  - `PromptService` 클래스 정의
  - 기존 `prompt_manager.py` 기능 이전 (프롬프트 생성 로직)
- [ ] `src/core/services/filesystem_service.py` 생성:
  - `FilesystemService` 클래스 정의
  - `.gitignore` 로딩 및 패턴 매칭 로직 구현 (기존 `file_explorer.py`, `main_controller.py` 등에서 분리)
  - 디렉토리 트리 생성 로직 구현 (기존 `main_controller.py`에서 분리)
- [ ] 각 서비스 클래스에서 UI 관련 코드(PyQt 위젯 접근, `QMessageBox` 등) 제거

## Utils 리팩토링

- [ ] `src/utils/helpers.py` 생성
- [ ] 기존 `utils.py` 내용 이전
- [ ] `get_resource_path` 함수 검토 및 수정 (프로젝트 루트 기반 경로 반환)
- [ ] 토큰 계산 함수 (`calculate_token_count`, `calculate_char_count`) 유지/개선
- [ ] `init_utils` 함수 (tiktoken 인코딩 로딩) 유지/개선

## 테스트 설정 및 작성

- [ ] `tests/` 디렉토리 구조 생성 (src 미러링)
- [ ] `tests/__init__.py` 에 `sys.path` 설정 추가
- [ ] `pytest` 기본 설정 (`pyproject.toml` 내)
- [ ] Core/Utils 모듈에 대한 초기 유닛 테스트 파일 생성:
  - `tests/core/pydantic_models/test_app_state.py`
  - `tests/core/pydantic_models/test_config_settings.py`
  - `tests/core/services/test_config_service.py`
  - `tests/core/services/test_state_service.py`
  - `tests/utils/test_helpers.py`
  - (추가) `test_template_service.py`, `test_xml_service.py`, `test_prompt_service.py`, `test_filesystem_service.py`
- [ ] Pydantic 모델 유효성 검사 테스트 작성
- [ ] `ConfigService` (설정 로드/저장), `StateService` (상태 로드/저장) 기본 기능 테스트 작성 (Mock 객체 활용)
- [ ] `helpers.py` 함수 (경로, 토큰 계산) 테스트 작성

## 정적 분석 및 포매팅

- [ ] `uv run ruff check . --fix` 실행 및 오류 수정
- [ ] `uv run black .` 실행 및 코드 포매팅 적용

## 타입 체크

- [ ] `uv run mypy src/core src/utils` 실행 (Core/Utils 우선)
- [ ] 타입 오류 수정 (필요시 타입 힌트 추가/수정)

## 기능 검증

- [ ] `uv run python main.py` 실행하여 애플리케이션 기본 동작 확인 (오류 없이 실행되는지)
- [ ] 주요 기능 (폴더 선택, 기본 프롬프트 로드, 상태 저장/로드 등) 수동 스모크 테스트

## 문서화

- [ ] `README.md` 업데이트: 개발 환경 설정 방법 (`uv` 사용법 포함) 추가

## 코드 복잡도 측정

- [ ] `uv run radon cc . -a` 실행하여 초기 복잡도 측정 및 기록 (참고용)

## 완료 기준

- Python 3.12 환경에서 `uv run python main.py`로 프로젝트 실행 가능.
- 모든 코드가 `src/` 내부에 위치.
- Core/Utils 계층 분리 완료 및 Pydantic 모델 도입 완료.
- Core 모듈에서 UI 의존성 제거 시작.
- 작성된 Core/Utils 유닛 테스트 통과 (`uv run pytest tests/core tests/utils`).
- `ruff`, `black` 검사 통과.
- `mypy` (Core/Utils 대상) 검사 통과.
- 애플리케이션 주요 기능 실행 가능 (일부 기능은 UI-Controller 연결 미완으로 제한될 수 있음).
