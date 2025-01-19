## 통합 개발 가이드 (XML 작성 + 파이썬 코딩 지침)

본 가이드는 LLM이 고품질의 파이썬 코드를 생성하고, 이 코드를 XML 구조에 반영할 때 준수해야 할 사항들을 통합적으로 정리한 문서입니다. 모든 지침을 빠짐없이 준수하여 일관성 있고 효율적인 개발을 진행해야 합니다. 

---

### 1. 공통 주의 사항

*   **언어 및 출력**: 모든 응답과 문서는 **한국어**로 작성합니다. 수정된 코드는 생략 없이 전체를 출력하고, 수정하지 않은 파일은 "수정 없음"으로 명시합니다.
*   **스타일**: 명확하고 간결한 기술적 스타일을 지향하며, 코드 가독성을 최우선으로 합니다.
*   **프로그래밍 패러다임**: 함수형 프로그래밍을 지향하고, 클래스는 꼭 필요한 경우에만 사용합니다.
*   **모듈화 및 관심사 분리**: 중복 코드는 함수나 모듈로 분리하고, 관심사 분리 원칙을 준수하여 유지보수성을 높입니다.
*   **변수 네이밍**:
    *   상수: 대문자와 언더스코어 (예: `IS_LOADING`, `MAX_RETRIES`)
    *   변수, 함수: 스네이크 케이스 (예: `process_data()`, `user_input`)
*   **실행 방식**: `__main__`에서 필요한 변수를 직접 설정합니다. `parser`나 터미널 입력을 사용하지 않습니다.
*   **API 키 및 환경 변수**: API 키는 `.env` 파일을 사용하고, 환경 변수를 통해 설정을 관리합니다.
*   **오류 처리**:
    *   `try-except` 블록으로 예외를 처리하고, 유용한 오류 메시지를 출력합니다.
    *   `termcolor`를 사용해 각 단계의 진행 상황을 사용자에게 알립니다.
*   **파일 처리**: `with open()` 사용 시 `encoding="utf-8"`을 항상 지정합니다.
*   **주요 변수 관리**: 스크립트 상단에 주요 변수(상수 포함)를 선언합니다.
*   **모델 명시**: 스크립트에 `gpt-4o`, `gpt-4o-mini` 등의 AI 모델명이 명시되어 있다면 변경하지 않습니다.
*   **요구 사항 관리**:
    *   `requirements.txt`를 생성 및 업데이트합니다. (버전 번호 미포함)
    *   `PRD (Product Requirement Document)` 폴더 내에 기능별 마크다운 파일을 생성 및 업데이트합니다. **(매 답변마다 업데이트 필수)**
*   **코드 포매팅**: `black`과 `isort`로 코드 포매팅을 진행합니다.
*   **문법**: 단순 조건문은 한 줄로 작성하고, 리스트/딕셔너리 컴프리헨션을 적극 활용합니다.
*   **웹 개발 (FastAPI)**: FastAPI 기본 패턴 및 REST API 설계 원칙을 준수하고, 적절한 캐싱 전략을 수립합니다.
*   **로깅**: 실행 과정 추적 및 문제 진단을 위해 로깅을 적극 활용합니다.
*   **타입 힌트**: `typing` 모듈을 활용하여 타입 힌트를 적극 사용합니다.
*   **데이터 구조**: **`Pydantic` 라이브러리를 사용하여 데이터 구조를 정의하고 유효성 검사를 수행합니다.**
*   **파일 및 디렉토리 구조**:
    *   디렉토리: 소문자 + 언더스코어 (예: `data_processing`)
    *   함수: 스네이크 케이스 (예: `calculate_average()`)
    *   클래스: 파스칼 케이스 (예: `DataProcessor`)
    *   실행 파일: `app/` 폴더에 저장, 프로젝트 루트에 `main.py` 배치
*   **파일 크기**: **개별 파일이 500줄을 초과할 경우 기능별로 분리하고, 관련 기능끼리 같은 폴더에 위치시킵니다.**
*   **XML에서 예약된 문자(Reserved Characters)**는 특별한 의미를 가지기 때문에, 텍스트 데이터로 사용할 때는 **이스케이프(Escape)** 처리를 해줘야 합니다.
*   수정이 없는 파일은 XML 출력하지 않습니다.

---

### 2. 파이썬 코딩 상세 지침

#### 2.1. 코드 구조

*   **파일 구조 템플릿**:

    ```python
    # imports
    # constants
    # Pydantic models
    # main functions/classes
    # helper functions

    if __name__ == "__main__":
        # main execution
    ```

#### 2.2. 네이밍 컨벤션

*   **함수**: `snake_case` (예: `process_data()`, `calculate_average()`)
*   **클래스**: `PascalCase` (예: `DataProcessor`, `UserManager`)
*   **상수**: `UPPER_SNAKE_CASE` (예: `MAX_ITERATIONS`, `API_KEY`)

#### 2.3. 타입 힌트 및 Pydantic

*   `typing` 모듈을 적극 활용합니다.
*   **`Pydantic`을 사용하여 데이터 모델을 정의하고, 데이터 유효성 검사를 수행합니다.**

    ```python
    from typing import List, Optional
    from pydantic import BaseModel, Field, validator

    class Item(BaseModel):
        name: str = Field(..., min_length=3, max_length=50)  # Required field with length constraints
        description: Optional[str] = None
        price: float = Field(..., gt=0)  # Required field, must be greater than 0
        tax: Optional[float] = None

        @validator("price")
        def price_must_be_positive(cls, value):
            if value <= 0:
                raise ValueError("Price must be positive")
            return value

    class Order(BaseModel):
        items: List[Item]
        customer_name: str

    # Example usage
    item1 = Item(name="Example Item", price=10.5)
    order1 = Order(items=[item1], customer_name="John Doe")
    ```

#### 2.4. 문법 및 포매팅

*   `black`과 `isort`를 사용하여 코드 스타일을 통일합니다.
*   단순 조건문은 한 줄로 작성합니다.

    ```python
    # Instead of:
    # if x > 5:
    #     result = True
    # else:
    #     result = False

    # Use:
    result = True if x > 5 else False
    ```

*   리스트/딕셔너리 컴프리헨션을 적극 활용합니다.

    ```python
    # Instead of:
    # squares = []
    # for i in range(10):
    #     squares.append(i * i)

    # Use:
    squares = [i * i for i in range(10)]

    # Instead of:
    # even_squares = {}
    # for i in range(10):
    #     if i % 2 == 0:
    #         even_squares[i] = i * i

    # Use:
    even_squares = {i: i * i for i in range(10) if i % 2 == 0}
    ```

#### 2.5. 웹 개발 (FastAPI)

*   FastAPI의 기본 패턴을 준수합니다.
*   REST API 설계 원칙을 따릅니다.
*   적절한 캐싱 전략을 수립합니다.
*   **Pydantic 모델을 사용하여 요청 및 응답 데이터를 정의합니다.**

    ```python
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from typing import Dict
    from pydantic import BaseModel

    app = FastAPI()

    # Example of caching
    cache: Dict[str, "Item"] = {}

    class Item(BaseModel):
        name: str
        description: Optional[str] = None
        price: float
        tax: Optional[float] = None

    @app.post("/items/", response_model=Item)
    async def create_item(item: Item):
        if item.name in cache:
            return JSONResponse(content=cache[item.name].dict())

        # ... some logic to create the item ...
        cache[item.name] = item
        return JSONResponse(content=item.dict())

    @app.get("/items/{item_name}", response_model=Item)
    async def read_item(item_name: str):
        if item_name in cache:
            return JSONResponse(content=cache[item_name].dict())

        # ... some logic to get the item ...
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        cache[item_name] = item
        return JSONResponse(content=item.dict())
    ```

#### 2.6. 로깅

*   `logging` 모듈을 사용하여 코드 실행 과정을 추적하고 문제를 진단합니다.

    ```python
    import logging

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    def my_function():
        logging.info("Starting my_function")
        # ... function body ...
        logging.info("Finished my_function")

    if __name__ == "__main__":
        my_function()
    ```

#### 2.7. 환경 설정

*   `.env` 파일을 사용하여 환경 변수를 관리합니다.
*   `python-dotenv` 라이브러리를 활용하여 환경 변수를 로드합니다.

    ```python
    # .env file
    API_KEY=your_api_key_here
    DATABASE_URL=your_database_url_here

    # main.py
    from dotenv import load_dotenv
    import os

    load_dotenv()

    API_KEY = os.getenv("API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")

    if __name__ == "__main__":
        print(f"API Key: {API_KEY}")
        print(f"Database URL: {DATABASE_URL}")
    ```

---

### 3. PRD (Product Requirement Document) 업데이트

*   **LLM은 답변을 생성할 때마다, 해당 답변과 관련된 기능을 설명하는 PRD 내의 마크다운 파일을 반드시 `전체 내용`으로 업데이트해야 합니다. 부분적인 내용만으로는 XML 파서가 기존 내용을 덮어쓰는 문제가 발생하기 때문에, 반드시 전체 내용을 포함해야 합니다.**

---

#### XML 작성에 관한 추가 지침

아래 XML 작성 규칙은 위 파이썬 코딩 지침과 결합되어야 합니다. 즉, XML 응답 시에도 파이썬 가이드라인을 준수하는 코드를 포함하고, 출력 형식을 정확히 지킵니다.

1. **응답 구조**: 응답은 2개 섹션으로 이뤄집니다.
    *   **Summary 섹션**: 전체 변경 사항의 간략한 요약을 제공합니다.
        *   전체 변경에 대한 간략 요약
        *   변경된 각 파일에 대한 1줄 요약 (이유 포함)
        *   삭제된 각 파일에 대한 1줄 요약 (이유 포함)
        *   git commit message 형식의 변경 요약 (feat, fix, docs 등의 prefix 포함, **한국어로 작성**)
        *   마크다운 형식으로 작성합니다.
    *   **XML 섹션**: XML 형식으로 변경 사항을 표현합니다.
        *   XML 섹션 외에는 다른 텍스트를 넣지 않습니다.
        *   XML 내부에 모든 변경된 파일을 기술합니다.
2. **XML 포맷 상세**:
    *   루트 태그는 `<code_changes>`로 합니다.
    *   `<changed_files>` 내에 `<file>` 요소를 사용합니다.
    *   각 `<file>` 요소 내에 `<file_summary>`, `<file_operation>`, `<file_path>`, `<file_code>`(생성 또는 업데이트 시) 태그를 사용합니다.
    *   `CREATE`, `UPDATE`, `DELETE` 중 하나를 `<file_operation>`에 명시합니다.
    *   `CREATE`나 `UPDATE` 시 `<file_code>` 내에 전체 파일 코드를 `![CDATA[...]]`로 감싸서 넣습니다. 이 때 파이썬 코드 작성 가이드라인을 반영한 전체 코드를 출력합니다.
    *   `DELETE` 시 `<file_code>` 태그를 사용하지 않습니다.
    *   `<file_summary>`에는 변경에 대한 간단한 요약을 적습니다.
    *   `<file_path>`에는 변경 대상 파일의 전체 경로를 적습니다.
3. **예시 구조**:

    ``````xml
    <code_changes>
        <changed_files>
            <file>
                <file_summary>새로운 더미 파일을 생성했어</file_summary>
                <file_operation>CREATE</file_operation>
                <file_path>examples/dummy_file.txt</file_path>
                <file_code><![CDATA[
    이것은 새로 만든 더미 파일의 내용!
    여기에 원하는 텍스트를 넣을 수 있어
    ]]></file_code>
            </file>
            <file>
                <file_summary>기존 파일을 새로운 내용으로 업데이트했어</file_summary>
                <file_operation>UPDATE</file_operation>
                <file_path>examples/updated_file.txt</file_path>
                <file_code><![CDATA[
    업데이트된 파일 내용!
    이전 내용보다 훨씬 좋아졌어
    ]]></file_code>
            </file>
            <file>
                <file_summary>필요 없는 오래된 파일을 삭제했어</file_summary>
                <file_operation>DELETE</file_operation>
                <file_path>examples/old_file.txt</file_path>
            </file>
        </changed_files>
    </code_changes>
    ``````

### Summary

*   `PRD` 폴더 내 마일스톤 및 체크리스트 파일 생성 및 업데이트 로직을 추가했습니다.
*   `PRD` 폴더 내 DB 정보 파일 생성 및 업데이트 로직을 추가했습니다.
*   `PRD` 폴더 내 DB 테이블 스키마 파일 생성 및 업데이트 로직을 추가했습니다.
*   `PRD` 폴더 내 파일별 기능 상세 파일 생성 및 업데이트 로직을 추가했습니다.
*   `PRD` 폴더 내 나중에 적용할 것 강화학습 파일 삭제했습니다.
*   `PRD` 폴더 내 전체 PRD 파일 생성 및 업데이트 로직을 추가했습니다.
*   `docs`: PRD 파일 관리 방식을 단일 파일에서 폴더 구조로 변경
*   `docs`: LLM을 위한 파이썬 코딩 지침 추가
*   `docs`: PRD 예시 파일 업데이트 및 형식 구체화

### XML

``````xml
<code_changes>
    <changed_files>
        <file>
            <file_summary>PRD 마일스톤 및 체크리스트 파일 생성 또는 업데이트</file_summary>
            <file_operation>UPDATE</file_operation>
            <file_path>PRD(Product Requirement Document)/0. 1. 마일스톤 및 체크리스트.md</file_path>
            <file_code><![CDATA[
# 0. 1. 마일스톤 및 체크리스트

## 마일스톤

| 마일스톤 | 예상 완료일 | 상태 |
|---|---|---|
| 데이터 수집 및 DB 연동 (실시간 모드 구현) |  |  |
| 시뮬레이션 환경 구현 |  |  |
| 매매 알고리즘 로직 구현 |  |  |
| Streamlit UI 구축 |  |  |
| 검증 및 최적화 |  |  |

## 개발 단계별 체크리스트

### 1. 데이터 수집 및 DB 연동 (실시간 모드)
- [ ] ...
- [ ] ...

### 2. 시뮬레이션 환경 구현
- [ ] ...
- [ ] ...

### 3. 매매 알고리즘 로직
- [ ] ...
- [ ] ...

### 4. Streamlit UI 구축
- [ ] ...
- [ ] ...

### 5. 검증 및 최적화
- [ ] ...
- [ ] ...
]]></file_code>
        </file>
        <file>
            <file_summary>PRD DB 정보 파일 생성 또는 업데이트</file_summary>
            <file_operation>UPDATE</file_operation>
            <file_path>PRD(Product Requirement Document)/1. 1. DB 정보.md</file_path>
            <file_code><![CDATA[
# 1. 1. DB 정보

## 데이터베이스 접속 정보
- **호스트:** ...
- **포트:** ...
- **사용자:** ...
- **데이터베이스명:** ...

## 데이터베이스 스키마

### 데이터베이스: ...

#### 테이블: ...
| 컬럼명          | 데이터 타입       | 제약조건                                                                                     | 설명                                  |
|-----------------|-------------------|----------------------------------------------------------------------------------------------|---------------------------------------|
| ...   | ...           | ...               | ...   |

## 테이블 생성 로직

...

## 데이터 접근 방법

...

## 참고사항

...
]]></file_code>
        </file>
        <file>
            <file_summary>PRD DB 테이블 스키마 파일 생성 또는 업데이트</file_summary>
            <file_operation>UPDATE</file_operation>
            <file_path>PRD(Product Requirement Document)/1. 2. DB table schema.json</file_path>
            <file_code><![CDATA[
{
  "테이블 이름": [
    {
      "column_name": "...",
      "data_type": "...",
      "max_length": ...,
      "default": ...,
      "nullable": ...,
      "comment": ...,
      "constraints": [
        "..."
      ]
    },
    ...
  ],
  ...
}
]]></file_code>
        </file>
        <file>
            <file_summary>PRD 파일별 기능 상세 파일 생성 또는 업데이트</file_summary>
            <file_operation>UPDATE</file_operation>
            <file_path>PRD(Product Requirement Document)/2. 1. 파일별 기능 상세.md</file_path>
            <file_code><![CDATA[
# 2. 1. 파일별 기능 상세

## 파일 이름

### 기능

...

### 사용법

...

## 데이터베이스 구조

...
]]></file_code>
        </file>
        <file>
            <file_summary>PRD 전체 개요 파일 생성 또는 업데이트</file_summary>
            <file_operation>UPDATE</file_operation>
            <file_path>PRD(Product Requirement Document)/0. 0. 전체 PRD.md</file_path>
            <file_code><![CDATA[
# 0. 0. 전체 PRD

## 프로젝트명: ...

## 개요

...

## 주요 목표

...

## 상세 요구사항

### 실시간 모드

...

### 시뮬레이션 모드

...

### 체결 지연(Delay)

...

### Streamlit 웹앱 구현

...

### 비기능적 요구사항

...

### 테스트 및 검증

...
]]></file_code>
        </file>
        <file>
            <file_summary>PRD 나중에 적용할 것 강화학습 파일 삭제</file_summary>
            <file_operation>DELETE</file_operation>
            <file_path>PRD(Product Requirement Document)/99. 나중에 적용할 것 강화학습.md</file_path>
        </file>
    </changed_files>
</code_changes>
``````
