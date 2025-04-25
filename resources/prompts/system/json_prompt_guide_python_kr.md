# 통합 개발 가이드 (JSON 응답 + 파이썬 코딩 지침)

본 가이드는 LLM이 고품질의 파이썬 코드를 생성하고, 이 코드를 **JSON 구조**에 반영할 때 준수해야 할 사항들을 통합적으로 정리한 문서입니다. 모든 지침을 빠짐없이 준수하여 일관성 있고 효율적인 개발을 진행해야 합니다.

---

## 1. 공통 주의 사항

- **언어 및 출력**: 모든 응답과 문서는 **한국어**로 작성합니다. 수정된 코드는 생략 없이 전체를 출력하고, 수정하지 않은 파일은 "수정 없음"으로 명시합니다.
- **스타일**: 명확하고 간결한 기술적 스타일을 지향하며, 코드 가독성을 최우선으로 합니다.
- **프로그래밍 패러다임**: 함수형 프로그래밍을 지향하고, 클래스는 꼭 필요한 경우에만 사용합니다.
- **모듈화 및 관심사 분리**: 중복 코드는 함수나 모듈로 분리하고, 관심사 분리 원칙을 준수하여 유지보수성을 높입니다.
- **유틸리티 구성**:
  - 서브 프로젝트별 유틸리티는 `src/<sub_project_name>/utils/` 폴더 내에 기능별 파일로 분리하여 저장합니다. (예: `src/my_feature/utils/parser.py`, `src/my_feature/utils/formatter.py`) 개별 서브 프로젝트 루트에 `utils.py` 단일 파일을 만들지 않습니다.
  - 프로젝트 전체에서 공통으로 사용하는 유틸리티는 `src/utils/` 폴더 내에 기능별 파일로 분리하여 저장합니다. (예: `src/utils/data_helper.py`, `src/utils/network.py`)
- **변수 네이밍**:
  - 상수: 대문자와 언더스코어 (예: `IS_LOADING`, `MAX_RETRIES`)
  - 변수, 함수: 스네이크 케이스 (예: `process_data()`, `user_input`)
- **실행 방식**: 프로젝트 루트의 `main.py`를 실행 진입점으로 사용하며, 이 파일은 `src` 내부의 핵심 로직을 임포트하여 실행합니다. `src/<sub-project_name>/main.py` 내 `__main__` 블록 직접 실행 대신 루트 `main.py`를 사용합니다. `parser`나 터미널 입력 직접 사용은 지양합니다.
- **설정 정보 관리**:
  - API 키, 비밀값, 환경별 설정 등은 각 서브 프로젝트의 설정 파일인 `src/<sub_project_name>/config.yml`에 저장합니다.
  - 설정 파일 로드는 프로젝트 공통 유틸리티인 `src/utils/config.py` 를 사용하여 수행합니다. `.env` 파일은 사용하지 않습니다.
- **오류 처리**:
  - `try-except` 블록으로 예외를 처리하고, 유용한 오류 메시지를 출력합니다.
  - `termcolor`를 사용해 각 단계의 진행 상황을 사용자에게 알립니다.
- **파일 처리**: `with open()` 사용 시 `encoding="utf-8"`을 항상 지정합니다.
- **주요 변수 관리**: 스크립트 상단에 주요 변수(상수 포함)를 선언합니다.
- **모델 명시**: 스크립트에 `gpt-4o`, `gpt-4o-mini` 등의 AI 모델명이 명시되어 있다면 변경하지 않습니다.
- **파이썬 버전**: **파이썬 3.12 이상** 버전을 사용합니다.
- **의존성 관리**:
  - **파이썬 가상 환경**: `uv`를 사용하여 파이썬 가상 환경을 관리합니다.
  - **의존성 명세**: 프로젝트 의존성은 `pyproject.toml` 파일에 명시하고 관리합니다. `requirements.txt`는 사용하지 않습니다.
- **요구 사항 관리 (PRD)**:
  - **저장 위치**: `docs/PRD(Product Requirement Document)/` 폴더 내에 기능별 마크다운(`.md`) 파일로 문서를 생성 및 업데이트합니다.
  - **업데이트 방식**: PRD 문서는 매번 업데이트하는 것이 아니라, 특정 기능의 요구사항 변경 또는 추가 시 해당 기능의 파일을 수정합니다.
- **코드 포매팅**: `black`과 `isort`로 코드 포매팅을 진행합니다.
- **문법**: 단순 조건문은 한 줄로 작성하고, 리스트/딕셔너리 컴프리헨션을 적극 활용합니다.
- **웹 개발 (FastAPI)**: FastAPI 기본 패턴 및 REST API 설계 원칙을 준수하고, 적절한 캐싱 전략을 수립합니다.
- **로깅**:
  - 실행 과정 추적 및 문제 진단을 위해 `logging` 모듈을 적극 활용합니다.
  - 로그 설정 및 관리는 프로젝트 공통 유틸리티인 **`src/utils/log_manager.py`** 를 통해 중앙에서 관리합니다.
  - 로그 파일은 `logs/` 폴더에 저장하며, 파일명에는 날짜와 시각 정보(예: `project_name_YYYYMMDD_HHMMSS.log`)를 포함하여 로그가 시간에 따라 구분되도록 합니다. (`log_manager.py` 에서 설정)
- **타입 힌트**: `typing` 모듈을 활용하여 타입 힌트를 적극 사용합니다.
- **데이터 구조**: **`Pydantic` 라이브러리를 사용하여 데이터 구조를 정의하고 유효성 검사를 수행합니다.**
- **파일 크기**: **개별 파일의 내용이 LLM 기준 15000 토큰을 초과할 경우 기능별로 분리하고, 관련 기능끼리 같은 폴더에 위치시킵니다.**
- **JSON 문자열 이스케이프**: JSON 출력 시 문자열 내 특수 문자(줄바꿈 `\n`, 따옴표 `"`, 백슬래시 `\\` 등)가 JSON 표준에 맞게 올바르게 이스케이프 처리되도록 합니다.
- **수정 없는 파일**: 수정이 없는 파일은 **JSON 응답**에 포함하지 않습니다.
- **응답 구조 및 요약**: **응답은 `code_changes` 키와 `summary` 키를 포함하는 단일 JSON 객체여야 합니다.** `summary` 객체는 **1000 토큰 이하**로 간결하게 작성합니다.

---

## 2. 파이썬 코딩 상세 지침

## 2.1. 코드 구조

- **파일 구조 템플릿 (예: `src/sub_project_name/main.py`)**:

  ```python
  # Standard library imports
  import logging

  # Third-party imports
  from fastapi import FastAPI # 예시: FastAPI 사용 시
  from pydantic import BaseModel
  from termcolor import colored

  # Local application imports
  from .models import MyData # 예시: 같은 패키지 내 모델 임포트
  from .utils.parser import parse_data # 예시: 서브 프로젝트 유틸리티 임포트
  from src.utils.config import load_config # 프로젝트 공통 설정 로더 임포트
  from src.utils.log_manager import get_logger # 프로젝트 공통 로거 임포트

  # 로거 설정 (log_manager.py 통해 가져옴)
  logger = get_logger(__name__)

  # 설정 로드 (루트 main.py 또는 애플리케이션 초기화 시점에 수행 권장)
  # config = load_config('sub_project_name') # 서브 프로젝트 이름 전달

  # Pydantic models
  class Item(BaseModel):
      name: str
      price: float

  # FastAPI 앱 인스턴스 생성 (웹 애플리케이션의 경우)
  app = FastAPI()

  # main functions/classes
  @app.post("/items/", response_model=Item)
  async def create_item(item: Item):
      """Creates an item."""
      logger.info(f"Received item: {item.name}")
      # ... 로직 ...
      # config = load_config('sub_project_name') # 함수 내에서 필요시 로드
      # parsed = parse_data(...) # 서브 프로젝트 유틸리티 사용
      logger.info(colored(f"Item '{item.name}' created successfully.", "green"))
      return item

  def core_logic_function():
      """애플리케이션 핵심 로직 함수 (웹이 아닌 경우)."""
      logger.info("Starting core logic...")
      config = load_config('sub_project_name') # 함수 내에서 필요시 로드
      # ... 로직 수행 ...
      logger.info("Core logic finished.")

  # helper functions (이 모듈 내부에서만 사용되는)
  def _internal_helper():
      pass

  # __main__ 블록은 루트 main.py에서 실행하므로 여기서는 불필요
  # if __name__ == "__main__":
  #     pass
  ```

## 2.2. 네이밍 컨벤션

- **함수**: `snake_case` (예: `process_data()`, `calculate_average()`)
- **클래스**: `PascalCase` (예: `DataProcessor`, `UserManager`)
- **상수**: `UPPER_SNAKE_CASE` (예: `MAX_ITERATIONS`, `API_KEY_NAME`)
- **디렉토리**: `lower_snake_case` (예: `data_processing`, `api_clients`, `utils`)

## 2.3. 타입 힌트 및 Pydantic

- `typing` 모듈을 적극 활용하여 함수의 인자, 반환 값, 변수 등에 타입 힌트를 명시합니다.
- **`Pydantic`을 사용하여 데이터 모델을 정의하고, 데이터 유효성 검사를 수행합니다.** API 응답, 설정 구조, 데이터 처리 파이프라인 등 데이터 구조가 명확해야 하는 곳에 사용합니다. (기존 예시 코드 유지)

  ```python
  from typing import List, Optional
  from pydantic import BaseModel, Field, validator, EmailStr

  class UserProfile(BaseModel):
      username: str = Field(..., min_length=3, description="Unique username")
      email: EmailStr
      full_name: Optional[str] = None
      age: Optional[int] = Field(None, gt=0, le=120)

  class Order(BaseModel):
      order_id: int
      user: UserProfile
      items: List[str]

      @validator("items")
      def items_must_not_be_empty(cls, value):
          if not value:
              raise ValueError("Order must contain at least one item")
          return value
  ```

## 2.4. 문법 및 포매팅

- `black`과 `isort`를 사용하여 코드 스타일을 통일합니다. `pyproject.toml`에 설정을 포함할 수 있습니다.
- 단순 조건문은 가독성을 해치지 않는 선에서 한 줄로 작성 가능합니다.
- 리스트/딕셔너리 컴프리헨션을 사용하여 간결하고 효율적인 코드를 작성합니다.

## 2.5. 웹 개발 (FastAPI)

- FastAPI의 기본 패턴(경로 연산 함수, Pydantic 모델 통합 등)을 준수합니다. (`src/sub_project_name/main.py` 에서 `app` 객체 정의)
- REST API 설계 원칙(자원 기반 URL, 적절한 HTTP 메서드 사용 등)을 따릅니다.
- 필요한 경우 `FastAPI-Cache2` 등의 라이브러리를 활용하여 적절한 캐싱 전략을 수립합니다.
- **Pydantic 모델을 사용하여 요청 본문(request body)과 응답 모델(response model)을 정의하여 자동 데이터 유효성 검사 및 문서화를 활용합니다.**

## 2.6. 로깅 상세

- **`src/utils/log_manager.py`** 를 통해 로깅 설정을 중앙에서 관리합니다. 이 모듈은 로거 인스턴스를 생성하고 필요한 핸들러(콘솔, 파일 등)를 설정하는 역할을 합니다.
- 로그 레벨(DEBUG, INFO, WARNING, ERROR, CRITICAL)을 적절히 사용하여 로그의 중요도를 구분합니다.
- **로그 파일 저장**: `log_manager.py` 내에서 `FileHandler`를 사용하여 `logs/` 디렉토리에 로그를 저장하도록 설정합니다. 파일명에 날짜와 시간을 포함시켜 로그 파일을 관리하기 용이하게 합니다.
- 중요한 실행 단계, 오류 발생, 외부 시스템과의 통신 등을 기록합니다. 각 모듈에서는 `from src.utils.log_manager import get_logger; logger = get_logger(__name__)` 와 같이 로거 인스턴스를 가져와 사용합니다.

## 2.7. 환경 설정 (config.yml)

- 설정 정보는 각 서브 프로젝트 내 **`src/<sub_project_name>/config.yml`** 파일에 YAML 형식으로 저장합니다.
- 설정 파일 로드는 프로젝트 공통 유틸리티인 **`src/utils/config.py`** 에 정의된 함수(예: `load_config(sub_project_name: str)`)를 사용합니다. 이 함수는 서브 프로젝트 이름을 인자로 받아 해당 경로의 `config.yml` 파일을 파싱하고 파이썬 딕셔너리로 반환합니다.
- 설정 파일에는 API 키, 데이터베이스 접속 정보, 외부 서비스 URL, 애플리케이션 동작 파라미터 등을 포함할 수 있습니다. 민감 정보는 실제 값 대신 플레이스홀더나 환경 변수 참조 방식으로 관리하는 것을 고려할 수 있습니다.

  ```yaml
  # src/sub_project_name/config.yml Example
  api_settings:
    service_a:
      api_key: "your_api_key_here" # 실제 키 또는 환경 변수 참조
      base_url: "https://api.service_a.com/v1"
      timeout: 10
  database:
    type: "postgresql"
    host: "localhost"
    port: 5432
    username: "user"
    password: "password" # 실제 비밀번호 또는 환경 변수 참조
    db_name: "my_app_db"
  app_parameters:
    max_retries: 3
    feature_flags:
      new_dashboard: true
  ```

---

## 3. 가상 환경 및 의존성 관리

- **가상 환경**: `uv`를 사용하여 프로젝트별 격리된 파이썬 환경을 생성하고 관리합니다.
  - 생성: `uv venv`
  - 활성화: `. .venv/bin/activate` (Linux/macOS) 또는 `.venv\Scripts\activate` (Windows)
- **의존성 관리**: `pyproject.toml` 파일을 사용하여 프로젝트 메타데이터와 의존성을 관리합니다.

  - 의존성 추가: `uv pip install <package_name>`
  - 의존성 설치: `uv pip install -r requirements.lock` 또는 `uv sync` (lock 파일 기반)
  - `pyproject.toml` 예시:

    ```toml
    [project]
    name = "my_project"
    version = "0.1.0"
    description = "My project description."
    requires-python = ">=3.12" # 파이썬 버전 명시
    dependencies = [
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "pydantic>=2.0",
        "PyYAML>=6.0",
        "termcolor>=2.0",
        "requests>=2.28.0",
        # 다른 필요한 라이브러리 추가
    ]

    [tool.black]
    line-length = 88

    [tool.isort]
    profile = "black"

    [tool.uv.sources]
    # Optional: Specify custom package sources if needed
    ```

---

## 4. 프로젝트 구조

아래는 권장하는 프로젝트 구조입니다.

```tree
project-name/
├── src/                             # 소스 코드 루트 (파이썬 패키지)
│   ├── sub_project_name/            # 메인 애플리케이션 또는 라이브러리 모듈
│   │   ├── models/                  # Pydantic 모델 또는 데이터베이스 모델
│   │   │   ├── __init__.py
│   │   │   └── data_models.py
│   │   ├── tools/                   # 특정 기능을 수행하는 도구 모듈들
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── specific_tool.py
│   │   ├── utils/                   # ★ 서브 프로젝트별 유틸리티 폴더 ★
│   │   │   ├── __init__.py
│   │   │   ├── parser.py            # 예시: 파싱 관련 유틸
│   │   │   └── formatter.py         # 예시: 포맷팅 관련 유틸
│   │   ├── __init__.py
│   │   ├── config.yml               # ★ 서브 프로젝트 설정 파일 ★
│   │   └── main.py                  # 애플리케이션 핵심 로직 (예: FastAPI app 정의)
│   └── utils/                       # ★ 프로젝트 공통 유틸리티 폴더 ★
│       ├── __init__.py
│       ├── config.py                # ★ 공통 설정 로더 ★
│       ├── log_manager.py           # ★ 공통 로깅 관리자 ★
│       └── common_helper.py         # 예시: 다른 공통 유틸
├── tests/                           # 테스트 코드 루트
│   ├── __init__.py
│   └── stage_{number}_{stage_description}/
│       ├── __init__.py
│       └── test_{feature_name}.py
├── docs/                            # 문서 루트
│   ├── PRD(Product Requirement Document)/
│   │   ├── 00_overview.md
│   │   └── feature_a_spec.md
│   └── developer_guide.md
├── logs/                            # 로그 파일 저장 디렉토리 (자동 생성 권장)
├── docker/                          # Docker 관련 파일 디렉토리
│   ├── Dockerfile
│   └── docker-compose.yml
├── data/                            # 입력/출력 데이터 저장 디렉토리 (버전 관리 제외 권장)
├── main.py                          # ★ 프로젝트 루트 실행 진입점 ★
├── pyproject.toml                   # 프로젝트 설정 및 의존성 관리
├── README.md                        # 프로젝트 소개 및 사용법
└── .gitignore                       # Git 추적 제외 파일 목록
```

**주요 디렉토리 및 파일 설명:** (설명은 원본 가이드와 동일)

- **`src/`**: 모든 파이썬 소스 코드가 위치하는 루트 패키지 디렉토리...
- **`src/sub_project_name/`**: 특정 기능 또는 마이크로서비스 단위의 서브 프로젝트 코드...
- **`src/sub_project_name/models/`**: Pydantic 모델, 데이터베이스 스키마...
- **`src/sub_project_name/tools/`**: 특정 기능을 수행하는 재사용 가능한 도구 모듈들...
- **`src/sub_project_name/utils/`**: 해당 `sub_project_name` 서브 프로젝트 내에서만 공통으로 사용되는 유틸리티 함수들...
- **`src/sub_project_name/config.yml`**: 해당 서브 프로젝트에 특화된 설정값...
- **`src/sub_project_name/main.py`**: 해당 서브 프로젝트의 핵심 로직을 포함하는 메인 파일...
- **`src/utils/`**: 프로젝트 전체에서 여러 서브 프로젝트가 공통으로 사용할 수 있는 유틸리티 모듈들...
- **`src/utils/config.py`**: 각 서브 프로젝트의 `config.yml` 파일을 안전하게 로드하고 파싱하는 공통 함수...
- **`src/utils/log_manager.py`**: 프로젝트 전체의 로깅 설정을 초기화하고...
- **`tests/`**: 단위 테스트, 통합 테스트, 엔드투엔드 테스트 등 모든 종류의 테스트 코드...
- **`tests/stage_{number}_{stage_description}/`**: 개발 단계를 구분하여 테스트를 구성하는 하위 디렉토리...
- **`docs/`**: 프로젝트 관련 문서...
- **`docs/PRD/`**: 제품 요구사항 문서...
- **`logs/`**: 애플리케이션 실행 중 생성되는 로그 파일...
- **`docker/`**: Docker 관련 파일...
- **`data/`**: 프로그램 실행에 필요한 입력 데이터...
- **`main.py` (루트)**: 프로젝트의 **최상위 실행 진입점** 파일...
- **`pyproject.toml`**: 프로젝트의 메타데이터...
- **`README.md`**: 프로젝트의 루트 디렉토리에 위치하며...
- **`.gitignore`**: Git 버전 관리 시스템이 추적하지 않아야 할 파일...

---

## 5. PRD (Product Requirement Document) 관리

- PRD 문서는 `docs/PRD/` 디렉토리 내에 기능별 또는 주제별 마크다운 파일로 작성하고 관리합니다.
- **전체 PRD 내용을 하나의 파일로 관리하거나 매번 업데이트할 필요는 없습니다.** 변경 사항이 발생한 특정 기능의 요구사항 문서만 수정합니다.
- 파일명 규칙 (예시): `01_user_authentication.md`, `02_data_processing_pipeline.md` 등 번호와 설명을 조합하여 사용하면 좋습니다.

---

## 6. JSON 응답 형식

**명심하세요:** 응답은 **유효한 단일 JSON 객체**여야 합니다. 이 객체는 `code_changes`와 `summary`라는 두 개의 주요 키를 포함합니다. `summary` 객체는 **1000 토큰 이하**로 간결하게 작성해야 합니다.

1.  **응답 구조**: `code_changes`와 `summary` 키를 가진 단일 JSON 객체.

    ```json
    {
      "code_changes": { ... },
      "summary": { ... }
    }
    ```

2.  **`code_changes` 객체 상세**:

    - `changed_files`라는 단일 키를 포함하며, 이 키의 값은 객체들의 배열입니다.
    - `changed_files` 배열의 각 객체는 수정된 파일 하나를 나타내며 다음 키들을 가집니다:
      - `file_summary` (문자열): 파일 변경 사항에 대한 간략한 설명.
      - `file_operation` (문자열): 수행된 작업 ("CREATE", "UPDATE", "DELETE").
      - `file_path` (문자열): 프로젝트 구조를 따르는 정확한 파일 경로.
      - `file_code` (문자열, 선택 사항): 파일의 전체 코드를 담은 문자열. `file_operation`이 "DELETE"인 경우 이 키를 생략합니다. 코드 내용에 대해 올바른 JSON 문자열 이스케이프(예: 줄바꿈은 `\n`, 따옴표는 `\"`)를 적용해야 합니다.
    - **수정 없는 파일은 `changed_files` 배열에 포함하지 않습니다.**
    - **파일 경로는 위 '프로젝트 구조' 섹션에 명시된 경로를 정확히 따릅니다.** (예: `main.py`, `src/sub_project_name/main.py`, `src/sub_project_name/config.yml`, `src/utils/log_manager.py`, `docs/PRD/feature_x.md`, `docker/Dockerfile`)

3.  **`summary` 객체 상세**:

    - 다음 키들을 포함합니다:
      - `overall_summary` (문자열): 전체 변경 사항에 대한 요약.
      - `file_specific_summary` (배열): 각 파일 변경/삭제를 설명하는 객체들의 배열. 각 객체는 다음을 포함해야 합니다:
        - `file` (문자열): 변경/삭제된 파일의 경로.
        - `operation` (문자열): "CREATE", "UPDATE", 또는 "DELETE".
        - `reason` (문자열): 변경/삭제에 대한 간략한 이유.
      - `git_commit_message` (문자열): Git 커밋 메시지 형식의 요약 (feat, fix, docs 등 prefix 사용, **한국어로 작성**).
    - `summary` 객체의 전체 내용은 **1000 토큰 이하**여야 합니다.

4.  **JSON 문법 확인**: **최종 응답 생성 후, JSON 문법이 올바른지 반드시 다시 확인하십시오.** 중괄호 `{}`, 대괄호 `[]`, 쉼표 `,`, 콜론 `:`, 따옴표 `""`의 올바른 사용 및 문자열 내 특수 문자 이스케이프 처리를 확인합니다.

**변경된 가이드라인에 따른 예시 JSON Snippet:**
(루트 `main.py` 예시 업데이트: `log_manager`, `config` 사용 반영)

```json
{
  "code_changes": {
    "changed_files": [
      {
        "file_summary": "프로젝트 루트 실행 스크립트: 공통 로깅 및 설정 로더 사용, FastAPI 앱 실행",
        "file_operation": "UPDATE",
        "file_path": "main.py",
        "file_code": "import uvicorn\nimport os\nimport logging\nfrom termcolor import colored\n\n# 프로젝트 공통 유틸리티 임포트\nfrom src.utils.log_manager import setup_logging, get_logger\nfrom src.utils.config import load_config\n\n# 서브 프로젝트 앱 임포트 (실행할 앱에 따라 변경)\nfrom src.sub_project_name.main import app\n\nif __name__ == \"__main__\":\n    # 로깅 설정 (log_manager 사용)\n    setup_logging()\n    logger = get_logger(__name__)\n    logger.info(colored(\"Starting application from root main.py...\", \"yellow\"))\n\n    # 설정 로드 (예시: sub_project_name 설정 로드)\n    sub_project_name = \"sub_project_name\" # 대상 서브 프로젝트 지정\n    try:\n        app_config = load_config(sub_project_name)\n        logger.info(f\"Configuration for '{sub_project_name}' loaded.\")\n        # 로드된 설정을 앱에 주입하거나 다른 초기화 작업 수행 가능\n        # 예: app.state.config = app_config\n    except FileNotFoundError:\n        logger.warning(f\"Configuration file for '{sub_project_name}' not found. Proceeding with defaults or environment variables if applicable.\")\n    except Exception as e:\n        logger.critical(f\"Failed to load configuration for '{sub_project_name}': {e}\", exc_info=True)\n        exit(1) # 설정 로드 실패 시 종료\n\n    # FastAPI 실행 (Uvicorn 사용)\n    host = os.getenv(\"APP_HOST\", \"127.0.0.1\")\n    port = int(os.getenv(\"APP_PORT\", \"8000\"))\n    reload = os.getenv(\"APP_RELOAD\", \"true\").lower() == \"true\"\n\n    logger.info(f\"Starting Uvicorn server on {host}:{port} with reload={reload}\")\n    try:\n        # 실행할 앱의 경로를 문자열로 지정\n        uvicorn.run(f\"src.{sub_project_name}.main:app\", host=host, port=port, reload=reload)\n    except Exception as e:\n        logger.critical(f\"Failed to start Uvicorn: {e}\", exc_info=True)\n\n"
      },
      {
        "file_summary": "공통 로깅 관리자 모듈 추가",
        "file_operation": "CREATE",
        "file_path": "src/utils/log_manager.py",
        "file_code": "import logging\nimport logging.handlers\nimport os\nimport datetime\n\nLOG_DIR = \"logs\"\nLOG_LEVEL = logging.INFO # 기본 로그 레벨\n\ndef setup_logging():\n    \"\"\"프로젝트 전체 로깅 설정 초기화 함수.\"\"\"\n    os.makedirs(LOG_DIR, exist_ok=True)\n    log_filename = os.path.join(LOG_DIR, f\"app_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log\")\n\n    # 기본 포맷터\n    formatter = logging.Formatter(\n        \"%(asctime)s - %(name)s - %(levelname)s - %(message)s\"\n    )\n\n    # 루트 로거 설정\n    root_logger = logging.getLogger()\n    root_logger.setLevel(LOG_LEVEL)\n\n    # 기존 핸들러 제거 (중복 방지)\n    for handler in root_logger.handlers[:]:\n        root_logger.removeHandler(handler)\n\n    # 파일 핸들러 설정 (UTF-8 인코딩 지정)\n    file_handler = logging.FileHandler(log_filename, encoding='utf-8')\n    file_handler.setFormatter(formatter)\n    root_logger.addHandler(file_handler)\n\n    # 콘솔 핸들러 설정\n    stream_handler = logging.StreamHandler()\n    stream_handler.setFormatter(formatter)\n    root_logger.addHandler(stream_handler)\n\n    logging.getLogger(\"uvicorn.access\").setLevel(logging.WARNING) # uvicorn 로그 레벨 조정 (선택적)\n    logging.getLogger(\"uvicorn.error\").setLevel(logging.WARNING)\n\n    root_logger.info(\"Logging setup complete.\")\n\ndef get_logger(name: str) -> logging.Logger:\n    \"\"\"지정된 이름으로 로거 인스턴스를 반환합니다.\"\"\"\n    return logging.getLogger(name)\n\n# 필요시 여기에 추가적인 로깅 관련 헬퍼 함수 정의 가능\n"
      },
      {
        "file_summary": "공통 설정 로더 유틸리티 추가",
        "file_operation": "CREATE",
        "file_path": "src/utils/config.py",
        "file_code": "import yaml\nimport os\nfrom typing import Dict, Any\n\nCONFIG_DIR_TEMPLATE = \"src/{sub_project_name}/config.yml\"\n\ndef load_config(sub_project_name: str) -> Dict[str, Any]:\n    \"\"\"\n    지정된 서브 프로젝트의 config.yml 파일을 로드합니다.\n\n    Args:\n        sub_project_name: 설정을 로드할 서브 프로젝트의 이름 (예: 'my_feature').\n\n    Returns:\n        설정 내용이 담긴 딕셔너리.\n\n    Raises:\n        FileNotFoundError: 설정 파일이 존재하지 않을 경우.\n        yaml.YAMLError: YAML 파싱 중 오류가 발생할 경우.\n        Exception: 그 외 파일 읽기 오류 발생 시.\n    \"\"\"\n    config_path = CONFIG_DIR_TEMPLATE.format(sub_project_name=sub_project_name)\n\n    if not os.path.exists(config_path):\n        raise FileNotFoundError(f\"Configuration file not found at: {config_path}\")\n\n    try:\n        with open(config_path, 'r', encoding='utf-8') as f:\n            config = yaml.safe_load(f)\n        if config is None: # 빈 파일 처리\n            return {}\n        return config\n    except yaml.YAMLError as e:\n        # YAML 형식 오류 시 더 구체적인 정보 로깅 가능\n        raise yaml.YAMLError(f\"Error parsing YAML file {config_path}: {e}\")\n    except Exception as e:\n        raise Exception(f\"Error reading configuration file {config_path}: {e}\")\n\n# 필요시 환경 변수 오버라이드 또는 기본값 처리 로직 추가 가능\n"
      },
      {
        "file_summary": "서브 프로젝트 설정 파일 생성",
        "file_operation": "CREATE",
        "file_path": "src/sub_project_name/config.yml",
        "file_code": "# src/sub_project_name/config.yml Example\napi_settings:\n  service_a:\n    api_key: \"your_api_key_here\"\n    base_url: \"https://api.service_a.com/v1\"\n    timeout: 10\ndatabase:\n  type: \"sqlite\"\n  path: \"data/sub_project.db\"\napp_parameters:\n  max_items: 100\n"
      }
    ]
  },
  "summary": {
    "overall_summary": "프로젝트 구조 및 관리 방식을 업데이트된 가이드라인에 맞춰 수정했습니다. 주요 변경 사항으로 유틸리티 폴더 구조 개편, 공통 로깅 및 설정 관리 모듈 도입, 서브 프로젝트별 설정 파일 위치 변경 등이 있습니다. 루트 `main.py`는 공통 모듈을 사용하여 로깅 및 설정을 처리하고 Uvicorn 서버를 실행하도록 업데이트했습니다.",
    "file_specific_summary": [
      {
        "file": "main.py",
        "operation": "UPDATE",
        "reason": "공통 로깅(`log_manager`) 및 설정 로더(`config`) 사용하도록 수정, FastAPI 앱 실행 로직 업데이트."
      },
      {
        "file": "src/utils/log_manager.py",
        "operation": "CREATE",
        "reason": "프로젝트 전체 로깅을 관리하는 공통 모듈 추가. 파일/콘솔 핸들러 및 기본 포맷 설정 포함."
      },
      {
        "file": "src/utils/config.py",
        "operation": "CREATE",
        "reason": "서브 프로젝트별 `config.yml` 파일을 로드하는 공통 유틸리티 함수 추가."
      },
      {
        "file": "src/sub_project_name/config.yml",
        "operation": "CREATE",
        "reason": "예시 서브 프로젝트의 설정 파일 생성."
      }
    ],
    "git_commit_message": "feat: 프로젝트 구조 및 공통 유틸리티 개편 (로깅, 설정)"
  }
}
```
