## LLM을 위한 파이썬 코딩 지침
이 지침은 LLM이 고품질의 파이썬 코드를 생성하도록 돕기 위해 작성되었습니다. 아래의 가이드라인을 꼼꼼히 읽고 모든 코드 작성에 반영해 주시기 바랍니다.

### 1. 기본 원칙

*   **전체 출력**: 수정된 코드를 출력할 땐 생략된 코드가 없이 전체코드를 출력합니다.
*   **전체 출력**: 수정이 없는 파일은 "수정 없음" 이라고만 출력합니다.
*   **명확성과 가독성**: 모든 응답은 **반드시 한국어로** 해야 합니다.
*   **명확성과 가독성**: 코드는 이해하기 쉽고 명확해야 합니다. 간결하고 기술적인 스타일을 지향합니다.
*   **함수형 프로그래밍**: 가능한 한 함수형 프로그래밍 패러다임을 따릅니다. 클래스는 꼭 필요한 경우에만 사용합니다.
*   **모듈화**: 코드 중복을 피하고, 반복되는 작업은 함수나 모듈로 분리합니다.
*   **서술적 변수명**: 변수의 의미와 용도를 명확히 알 수 있는 이름을 사용합니다 (예: `IS_LOADING`, `HAS_ERROR`).
*   **실행**: 코드 실행에 필요한 변수는 `__main__`에서 직접 설정합니다. `parser`나 터미널 입력을 사용하지 않습니다.
*   **API 키**: API 키는 `.env` 파일을 사용합니다.
*   **오류 처리**: `try-except` 블록을 사용하여 예외를 적절히 처리하고, 사용자에게 유용한 오류 메시지를 제공합니다.
    *   **진행 상황 알림**: `termcolor`를 사용하여 코드의 각 단계를 사용자에게 알립니다.
    *   **정보성 오류 메시지**: 오류 발생 시, 유익한 정보를 담은 오류 메시지를 출력합니다.
*   **파일 열기**: `with open()`을 사용할 때는 항상 `encoding="utf-8"`을 지정합니다.
*   **주요 변수**: 주요 변수(상수 포함)는 스크립트 상단에 모두 대문자로 선언합니다.
*   **모델**: 스크립트에 `gpt-4o`, `gpt-4o-mini`, `o1-mini-preview`와 같은 모델이 명시되어 있으면 변경하지 않습니다.
*   **관심사 분리**: 프로젝트를 구현할 때 관심사 분리 원칙을 준수합니다.
*   **요구 사항**:
    *   `requirements.txt` 파일을 생성하고 업데이트합니다. 버전 번호는 포함하지 않습니다.
    *   `PRD(Product Requirement Document).md` 파일을 생성하고 업데이트합니다.

### 2. 코드 스타일 및 구조

*   **파일 구조**:
    *   주요 함수/클래스
    *   보조 함수
    *   상수
    *   타입 힌트
*   **디렉토리 구조**: 소문자와 언더스코어를 사용합니다 (예: `components/auth_wizard`).
*   **실행 파일 구조**:
    *   실행 파일은 `app/` 폴더에 저장합니다.
    *   프로젝트 루트에 `main.py`를 두어 파일을 실행할 수 있도록 합니다.
*   **파일 크기 관리**:
    *   개별 파일이 300줄을 초과할 경우 기능별로 여러 파일로 분리합니다.
    *   분리된 파일은 관련 기능끼리 같은 폴더에 위치시킵니다.

### 3. 네이밍 컨벤션

*   **함수**: `snake_case`를 사용합니다.
*   **클래스**: `PascalCase`를 사용합니다.

### 4. 타입 힌트

*   `typing` 모듈을 활용하여 타입 힌트를 적극적으로 사용합니다.
*   `dataclasses` 또는 `NamedTuple`을 선호합니다.
*   `Enum` 대신 딕셔너리나 상수를 사용합니다.

### 5. 문법 및 포매팅

*   `black`과 `isort`를 사용하여 코드를 포매팅합니다.
*   단순한 조건문은 한 줄로 작성합니다.
*   `list/dict comprehension`을 적절히 활용합니다.

### 6. 웹 개발

*   **프레임워크**: `FastAPI`를 사용하는 경우, 해당 프레임워크의 기본 패턴을 준수합니다.
*   **라우팅/데이터 처리**: `FastAPI` 문서를 참고하여 라우팅 및 데이터 처리를 구현합니다.
*   **REST API**: REST API 설계 원칙을 준수합니다.
*   **캐싱**: 적절한 캐싱 전략을 수립합니다.

### 7. 로깅

*   코드 실행 과정을 추적하고 문제를 진단할 수 있도록 로깅을 적극 활용합니다.

### 8. 환경 설정

*   환경 변수를 사용하여 설정을 관리합니다.

이 지침을 준수하여 가독성 높고 유지보수가 용이한 파이썬 코드를 작성해 주시기 바랍니다. 특히, `termcolor`를 사용한 진행 상황 알림과 유익한 오류 메시지 출력을 잊지 마세요.