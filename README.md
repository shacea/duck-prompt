
# DuckPrompt

이 애플리케이션은 PyQt5로 구현된 통합 Prompt Builder입니다. 아래 안내를 따라 편리하게 사용할 수 있어요.

---

## 목차
1. [프로그램 개요](#프로그램-개요)
2. [설치 및 실행](#설치-및-실행)
3. [주요 기능과 사용 방법](#주요-기능과-사용-방법)
   1. [프로젝트 폴더 선택하기](#프로젝트-폴더-선택하기)
   2. [프롬프트 빌더 모드](#프롬프트-빌더-모드)
   3. [메타 프롬프트 빌더 모드](#메타-프롬프트-빌더-모드)
   4. [디렉토리 트리 생성](#디렉토리-트리-생성)
   5. [XML 파서 사용](#xml-파서-사용)
   6. [템플릿/상태 관리](#템플릿상태-관리)
4. [기타 자주 묻는 질문 (FAQ)](#기타-자주-묻는-질문-faq)
5. [문의](#문의)

---

## 프로그램 개요

DuckPrompt는 여러 개의 파일을 선택한 뒤 그 내용을 합쳐서 LLM(Language Model)에 넘기기 위한 “프롬프트”를 손쉽게 생성하도록 도와주는 도구입니다.  
- **코드 강화 빌더 모드**: 체크한 파일 내용 + 시스템 프롬프트 + 사용자 프롬프트를 합쳐 “최종 프롬프트”를 만들어 줍니다.  
- **메타 프롬프트 빌더 모드**: 이미 만들어진 하나의 프롬프트를 또 다른 템플릿(“메타 프롬프트”)로 감싸 새로운 형태의 요청을 만들어 줍니다.

---

## 설치 및 실행

1. **의존성 설치**  
   - Python 3.12 이상 (Miniforge/Conda 환경 권장)
   - `requirements.txt`에 명시된 패키지(`PyQt5`, `pyinstaller`, `PyYAML`, `termcolor`, `tiktoken`, `python-dotenv` 등)를 설치해야 합니다.
   - 콘다 환경을 사용한다면 (예: `duck-prompt`) 아래와 같이 설치할 수 있습니다:
     ```bash
     conda activate duck-prompt
     pip install -r requirements.txt
     ```

2. **빌드(선택 사항)**  
   - `build.bat` 파일을 통해 PyInstaller로 빌드할 수 있습니다.
   - 빌드 후 `dist/DuckPrompt` 폴더에 `DuckPrompt.exe`가 생성됩니다(Windows 기준).
   - 아키텍처에 따라 `app_amd64.spec`, `app_arm64.spec`를 자동 선택합니다.

3. **실행**  
   - 빌드된 실행 파일 사용:  
     - `dist/DuckPrompt/DuckPrompt.exe`를 더블 클릭.
   - 혹은 Python 명령으로 직접 실행:
     ```bash
     conda activate duck-prompt
     python app.py
     ```

---

## 주요 기능과 사용 방법

### 프로젝트 폴더 선택하기
1. 프로그램 실행 후 상단의 **프로젝트 폴더 선택** 버튼을 클릭합니다.
2. 원하는 로컬 폴더를 지정하면, 왼쪽 창(파일 트리)에 해당 폴더 하위 파일들이 나타납니다.
3. 체크박스를 통해 어떤 파일을 프롬프트에 포함할지 선택하세요.  
   - 폴더에 체크하면 해당 폴더의 하위 모든 파일이 자동으로 선택됩니다.
   - 확실한 체크를 위해 폴더를 먼저 확장한 후 체크하시기 바랍니다.

### 프롬프트 빌더 모드
DuckPrompt는 두 가지 모드로 실행됩니다.  
- **코드 강화 빌더 모드**: 일반적인 “시스템 프롬프트 + 사용자 프롬프트 + 선택 파일 내용”을 합쳐줍니다.
- **모드 전환**: 상단 메뉴 “모드”에서 `코드 강화 빌더로 전환`, `메타 프롬프트 빌더로 전환`을 선택할 수 있습니다.

#### 사용 방법
1. **시스템 탭**과 **사용자 탭**에 프롬프트 초안을 작성합니다.
2. 좌측 트리에서 합치고 싶은 파일들을 체크합니다.
3. 상단(또는 단축키 `Ctrl+Enter`)으로 **프롬프트 생성** 버튼을 누르면 우측의 “프롬프트 출력” 탭에 결과가 생깁니다.
4. **클립보드에 복사** 버튼을 눌러 바로 붙여넣기 할 수 있습니다.
5. 복사된 내용을 GPT나 Gemini 등의 LLM에게 붙여넣어 바로 질문할 수 있습니다.
6. 시스템 프롬프트에 XML 프롬프트를 불러온 후 만든 프롬프트라면, LLM의 답변은 XML 형식으로 하도록 되어 있습니다.

### 메타 프롬프트 빌더 모드
1. **메타 프롬프트 템플릿** 탭에 프롬프트를 감쌀 상위 템플릿을 작성합니다.
2. **메타 사용자 입력** 탭에 실제로 사용자에게 요청할 내용을 적습니다.
3. **메타 프롬프트 생성** 버튼을 누르면 “메타 프롬프트 출력” 탭에서 결과를 볼 수 있습니다.
   - 필요 시, 마지막 “최종 프롬프트 생성” 버튼으로 변수를 치환해 완성된 형태를 얻을 수도 있습니다.

### 디렉토리 트리 생성
- 우측 상단의 **트리 생성** 버튼을 누르면, 체크된 파일/폴더를 기준으로 디렉토리 구조를 텍스트 형태로 파악할 수 있습니다.
- “파일 트리” 탭에서 결과를 볼 수 있습니다. LLM에 “디렉토리 구조”를 보여주어야 할 때 유용합니다.

### XML 파서 사용
- XML 프롬프트가 시스템 프롬프트에 불러왔다면, LLM 의 답변은 XML 형식일 것 입니다.
- XML 형식의 LLM 출력 내용을 복사합니다.
- “XML 입력” 탭에 `<code_changes>` 형식의 XML을 입력하고, **XML 파서 실행** 버튼을 클릭하면 해당 내용대로 자동으로 파일 생성/수정/삭제가 일괄 수행됩니다.
- 결과 요약은 팝업으로 확인할 수 있습니다.

### 템플릿/상태 관리
- “리소스 타입 선택”을 **프롬프트**로 두면, 좌측 하단 트리에 System/User 템플릿들이 표시됩니다.
  - 원하는 템플릿을 더블 클릭하여 불러오거나, 새 템플릿을 저장할 수 있습니다.
- **상태**로 전환하면, 현재 프로그램 상태를 파일로 저장하여 작업을 중단했다가 다시 이어서 할 수 있습니다.
  - 버튼을 통해 저장, 불러오기, 백업/복원 등의 동작을 할 수 있습니다.

---

## 기타 자주 묻는 질문 (FAQ)

1. **파일이 많으면 프로그램이 느려지나요?**  
   - 체크박스 기능으로 선택되지 않은 파일은 합쳐지지 않으므로, 필요한 파일만 선택하면 크게 무리 없습니다.
2. **토큰 계산이 잘못될 수도 있나요?**  
   - `tiktoken` 라이브러리를 통해 추정 토큰 수를 계산하지만, 모델(또는 프롬프트) 종류에 따라 오차가 있을 수 있습니다.
3. **.env로 기본 시스템 프롬프트 지정은 어떻게 하나요?**  
   - `.env` 파일에 `DEFAULT_SYSTEM_PROMPT="경로"`를 설정하면 프로그램 실행 시 자동으로 해당 파일 내용이 로드됩니다.
4. **메타 프롬프트 빌더가 필요한 경우는?**  
   - 여러 가지 역할 지시나 규칙이 이미 붙은 프롬프트를 또 다른 템플릿으로 래핑해야 할 때 편리합니다.

---

## 문의

- 사용 중에 궁금한 점이나 버그가 있다면 이슈로 남겨주세요.
- 더 자세한 사항은 PRD(Product Requirement Document) 폴더 내의 파일을 참고해 주세요.
- 감사합니다!