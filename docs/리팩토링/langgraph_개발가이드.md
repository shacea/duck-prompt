**1. 업그레이드 방향성: LangGraph 도입**

LangGraph는 LLM을 사용하여 상태 기반의 복잡한 애플리케이션(에이전트)을 구축하기 위한 라이브러리입니다. 상태(State)를 정의하고, 각 단계를 노드(Node)로 구현하며, 노드 간의 흐름을 엣지(Edge)로 연결하여 전체 워크플로우를 구성합니다.

현재 DuckPrompt의 흐름에 LangGraph를 도입하면 다음과 같은 장점을 가질 수 있습니다:

- **상태 관리**: 프롬프트 생성부터 Gemini 응답 처리, 파일 수정까지 이어지는 일련의 과정을 '상태'로 명확하게 관리할 수 있습니다.
- **모듈성**: 각 기능(Gemini 호출, 응답 처리 등)을 별도의 노드로 분리하여 코드 관리가 용이해지고 재사용성이 높아집니다.
- **확장성**: 추후 더 복잡한 로직(예: Gemini 응답 검증, 사용자 피드백 반영 후 재호출 등)을 추가하기 용이합니다.

**2. LangGraph를 이용한 프로그램 흐름 재구성**

기존 흐름을 LangGraph 기반으로 변경하면 다음과 같은 구조를 생각해볼 수 있습니다.

1.  **UI**: 사용자가 프롬프트를 입력하고 "Gemini로 전송" (가칭) 버튼 클릭.
2.  **LangGraph 시작**: UI에서 생성된 최종 프롬프트를 입력으로 받아 LangGraph 워크플로우 시작.
3.  **`call_gemini` 노드**:
    - 입력: 최종 프롬프트 문자열.
    - 처리: Gemini API를 호출하여 응답(XML + Summary 형식)을 받습니다.
    - 출력: Gemini API 응답 문자열.
4.  **`process_response` 노드**:
    - 입력: Gemini API 응답 문자열.
    - 처리: 응답 문자열을 파싱하여 XML 부분과 Summary 부분으로 분리합니다. (기존 XML 가이드라인에 따라 응답 형식을 가정)
    - 출력: XML 문자열, Summary 문자열.
5.  **UI 업데이트**: LangGraph 워크플로우 실행 완료 후, 결과(XML, Summary)를 받아 UI의 해당 탭에 표시합니다.
6.  **UI**: 사용자가 "파일 수정" 버튼 클릭.
7.  **XML 파서 실행**: UI의 XML 입력 탭 내용을 기반으로 기존 `XmlService`를 사용하여 파일 수정 실행.

**3. 업그레이드를 위한 준비 사항**

- **Gemini API 키**: Google AI Studio 또는 Google Cloud Console에서 Gemini API를 사용할 수 있는 API 키를 발급받아야 합니다.
- **LangGraph 및 관련 라이브러리 설치**:
  ```bash
  pip install langgraph langchain langchain_google_genai google-generativeai
  ```
  - `langgraph`: LangGraph 코어 라이브러리
  - `langchain`: LangGraph가 의존하는 LangChain 코어 기능 포함
  - `langchain_google_genai`: LangChain에서 Gemini API를 쉽게 사용하기 위한 통합 라이브러리
  - `google-generativeai`: Gemini API Python SDK (LangChain 통합 라이브러리가 내부적으로 사용)
- **LangGraph 학습**: 제공해주신 LangGraph 문서를 통해 기본적인 개념(State, Node, Edge, Graph compilation, invoke/stream)을 익혀야 합니다. 특히 상태 관리와 노드 정의 방법을 중점적으로 학습하는 것이 좋습니다.

**4. 코드 변경 예상 부분 및 방법**

LangGraph를 통합하기 위해 기존 코드의 여러 부분을 수정해야 합니다.

**(1) 설정 관리 (`config.yml`, `ConfigService`)**

- `src/config.yml`: `gemini_api_key` 필드를 추가합니다. (이미 추가되어 있네요!)
- `src/core/pydantic_models/config_settings.py`: `ConfigSettings` 모델에 `gemini_api_key` 필드가 있는지 확인합니다. (이미 있습니다!)
- `src/core/services/config_service.py`: `ConfigService`가 `gemini_api_key`를 정상적으로 로드하고 제공하는지 확인합니다. (이미 구현되어 있습니다!)

**(2) LangGraph 상태 정의**

LangGraph 워크플로우에서 관리할 상태를 정의합니다. `TypedDict`를 사용하는 것이 일반적입니다.

```python
# src/core/langgraph_state.py (새 파일 또는 적절한 위치)
from typing import TypedDict, List
from langchain_core.messages import BaseMessage # 또는 AnyMessage

class GeminiGraphState(TypedDict):
    """
    LangGraph 상태 정의
    """
    input_prompt: str             # Gemini API에 전달될 최종 프롬프트
    gemini_response: str          # Gemini API의 원시 응답
    xml_output: str               # 파싱된 XML 부분
    summary_output: str           # 파싱된 Summary 부분
    error_message: str | None = None # 오류 발생 시 메시지 저장 (선택적)
```

**(3) LangGraph 노드 구현**

각 단계에 해당하는 함수(노드)를 구현합니다.

```python
# src/core/services/gemini_service.py (새 파일 또는 적절한 위치)
import google.generativeai as genai
from langgraph.graph import StateGraph, END, START
from core.langgraph_state import GeminiGraphState
from core.services.config_service import ConfigService
import os

# ConfigService 인스턴스화 (실제 사용 시에는 주입받는 방식 고려)
# config_service = ConfigService()
# settings = config_service.get_settings()
# API_KEY = settings.gemini_api_key
# genai.configure(api_key=API_KEY)

# --- LangGraph 노드 함수 ---

def call_gemini(state: GeminiGraphState, config_service: ConfigService) -> GeminiGraphState:
    """
    Gemini API를 호출하는 노드
    """
    print("--- Calling Gemini API ---")
    prompt = state['input_prompt']
    settings = config_service.get_settings()
    api_key = settings.gemini_api_key
    model_name = settings.gemini_default_model # 설정에서 모델명 가져오기

    if not api_key:
        print("Gemini API Key not found in config.")
        return {"error_message": "Gemini API Key not configured."}

    try:
        genai.configure(api_key=api_key) # 매번 호출 시 configure 필요할 수 있음
        model = genai.GenerativeModel(model_name)
        # TODO: Gemini API 호출 시 필요한 추가 설정 (safety_settings 등) 고려
        response = model.generate_content(prompt)

        # 오류 처리 확인 (response.prompt_feedback 등)
        if not response.candidates:
             # 또는 response.prompt_feedback.block_reason 확인
             error_msg = f"Gemini API call failed. Reason: {response.prompt_feedback}"
             print(error_msg)
             return {"gemini_response": "", "error_message": error_msg}

        # 성공 시
        gemini_response_text = response.text
        print("--- Gemini Response Received ---")
        return {"gemini_response": gemini_response_text, "error_message": None}

    except Exception as e:
        error_msg = f"Error calling Gemini API: {str(e)}"
        print(error_msg)
        return {"gemini_response": "", "error_message": error_msg}


def process_response(state: GeminiGraphState) -> GeminiGraphState:
    """
    Gemini 응답을 XML과 Summary로 파싱하는 노드
    """
    print("--- Processing Gemini Response ---")
    gemini_response = state['gemini_response']
    xml_output = ""
    summary_output = ""

    # 파싱 로직 구현 (기존 XML 가이드라인 기반)
    # 예시: '<summary>' 태그를 기준으로 분리
    try:
        if "<summary>" in gemini_response:
            parts = gemini_response.split("<summary>", 1)
            xml_output = parts[0].strip()
            # </summary> 태그 제거 등 추가 처리 필요 시 구현
            summary_part = parts[1]
            if "</summary>" in summary_part:
                 summary_output = summary_part.split("</summary>", 1)[0].strip()
            else:
                 summary_output = summary_part.strip() # 태그가 없는 경우
        else:
            # Summary 태그가 없는 경우, 전체를 XML로 간주하거나 다른 규칙 적용
            xml_output = gemini_response.strip()
            summary_output = "Summary not found in response."

        print("--- Response Processed ---")
        return {"xml_output": xml_output, "summary_output": summary_output}

    except Exception as e:
        error_msg = f"Error processing response: {str(e)}"
        print(error_msg)
        # 오류 발생 시 상태 업데이트 또는 다른 처리
        return {"xml_output": gemini_response, "summary_output": "", "error_message": error_msg}

```

**(4) LangGraph 그래프 빌드 및 컴파일**

정의된 상태와 노드를 사용하여 그래프를 구성합니다.

```python
# src/core/services/gemini_service.py 또는 main_window.py 등 적절한 위치

from functools import partial

def build_gemini_graph(config_service: ConfigService) -> StateGraph:
    """
    Gemini API 호출 및 처리 LangGraph를 빌드합니다.
    ConfigService를 주입받아 노드에서 사용합니다.
    """
    workflow = StateGraph(GeminiGraphState)

    # ConfigService를 노드 함수에 바인딩
    bound_call_gemini = partial(call_gemini, config_service=config_service)

    # 노드 추가
    workflow.add_node("call_gemini", bound_call_gemini)
    workflow.add_node("process_response", process_response)

    # 엣지 연결
    workflow.add_edge(START, "call_gemini")
    workflow.add_edge("call_gemini", "process_response")
    workflow.add_edge("process_response", END)

    # 컴파일
    app = workflow.compile()
    return app

# MainWindow 초기화 시 또는 필요 시 그래프 빌드
# self.gemini_graph = build_gemini_graph(self.config_service)
```

**(5) PyQt5 UI 수정 (`main_window.py`, `main_window_setup_ui.py`, `main_window_setup_signals.py`)**

- **UI 요소 추가 (`main_window_setup_ui.py`)**:
  - `build_tabs`에 "Summary" 탭 (`QTextEdit`) 추가.
  - 기존 "프롬프트 생성" 버튼 옆이나 적절한 위치에 "Gemini로 전송" 버튼 (`QPushButton`) 추가.
- **시그널 연결 (`main_window_setup_signals.py`)**:
  - 새로 추가된 "Gemini로 전송" 버튼의 `clicked` 시그널을 `MainWindow`의 새 메서드(예: `send_prompt_to_gemini`)에 연결합니다.
- **`MainWindow` 클래스 수정 (`main_window.py`)**:

  - `__init__`에서 LangGraph `app`을 빌드하고 멤버 변수로 저장합니다.
    ```python
    from core.services.gemini_service import build_gemini_graph
    # ... inside __init__ ...
    self.gemini_graph = build_gemini_graph(self.config_service)
    ```
  - **스레딩 구현**: Gemini API 호출은 시간이 걸릴 수 있으므로 UI 멈춤 현상을 방지하기 위해 별도 스레드에서 LangGraph를 실행해야 합니다. `QThread`를 사용합니다.

    ```python
    # main_window.py 내부에 Worker 클래스 정의
    from PyQt5.QtCore import QThread, pyqtSignal, QObject

    class GeminiWorker(QObject):
        finished = pyqtSignal(str, str) # XML, Summary 결과 전달
        error = pyqtSignal(str)         # 오류 메시지 전달

        def __init__(self, graph_app, prompt):
            super().__init__()
            self.graph_app = graph_app
            self.prompt = prompt

        def run(self):
            try:
                # LangGraph 실행 (상태 초기화 및 입력 전달)
                # 입력 상태는 LangGraph 상태 정의와 일치해야 함
                initial_state = {"input_prompt": self.prompt}
                final_state = self.graph_app.invoke(initial_state)

                if final_state.get("error_message"):
                    self.error.emit(final_state["error_message"])
                else:
                    xml_result = final_state.get("xml_output", "")
                    summary_result = final_state.get("summary_output", "")
                    self.finished.emit(xml_result, summary_result)
            except Exception as e:
                self.error.emit(f"LangGraph execution error: {str(e)}")

    # MainWindow 클래스 내부에 메서드 추가/수정
    class MainWindow(QMainWindow):
        # ... existing code ...

        def __init__(self, mode="Code Enhancer Prompt Builder"):
             super().__init__()
             # ... existing init code ...
             self.gemini_graph = build_gemini_graph(self.config_service)
             self.gemini_thread = None # 스레드 관리를 위한 변수
             self.gemini_worker = None # 워커 관리를 위한 변수
             # ... rest of init ...

        def send_prompt_to_gemini(self):
            """ "Gemini로 전송" 버튼 클릭 시 실행될 메서드 """
            if not hasattr(self, 'prompt_output_tab'):
                QMessageBox.warning(self, "오류", "프롬프트 출력 탭을 찾을 수 없습니다.")
                return

            prompt_text = self.prompt_output_tab.toPlainText()
            if not prompt_text.strip():
                QMessageBox.warning(self, "경고", "Gemini에 전송할 프롬프트 내용이 없습니다.")
                return

            # 버튼 비활성화 및 상태 메시지 업데이트
            self.send_to_gemini_btn.setEnabled(False) # 새 버튼 이름으로 변경 필요
            self.status_bar.showMessage("Gemini API 호출 중...")
            QApplication.processEvents() # UI 업데이트 강제

            # 스레드 생성 및 시작
            self.gemini_thread = QThread()
            self.gemini_worker = GeminiWorker(self.gemini_graph, prompt_text)
            self.gemini_worker.moveToThread(self.gemini_thread)

            # 시그널 연결
            self.gemini_thread.started.connect(self.gemini_worker.run)
            self.gemini_worker.finished.connect(self.handle_gemini_response)
            self.gemini_worker.error.connect(self.handle_gemini_error)
            # 스레드 종료 시 정리
            self.gemini_worker.finished.connect(self.gemini_thread.quit)
            self.gemini_worker.finished.connect(self.gemini_worker.deleteLater)
            self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)

            self.gemini_thread.start()

        def handle_gemini_response(self, xml_result, summary_result):
            """ Gemini 응답 처리 슬롯 """
            if hasattr(self, 'xml_input_tab'):
                self.xml_input_tab.setPlainText(xml_result)
            if hasattr(self, 'summary_tab'): # 새로 추가한 Summary 탭 이름 확인 필요
                self.summary_tab.setPlainText(summary_result)
                # Summary 탭으로 자동 전환 (선택적)
                self.build_tabs.setCurrentWidget(self.summary_tab)

            self.status_bar.showMessage("Gemini 응답 처리 완료.")
            self.send_to_gemini_btn.setEnabled(True) # 버튼 다시 활성화

        def handle_gemini_error(self, error_msg):
            """ Gemini 오류 처리 슬롯 """
            QMessageBox.critical(self, "Gemini API 오류", f"오류 발생:\n{error_msg}")
            self.status_bar.showMessage("Gemini API 호출 오류.")
            self.send_to_gemini_btn.setEnabled(True) # 버튼 다시 활성화

    ```

  - **XML 파서 실행 버튼**: 기존 `run_xml_parser` 메서드(아마도 `XmlController` 내부에 있을)가 `xml_input_tab`의 내용을 읽어서 처리하도록 되어 있는지 확인합니다. (별도 수정이 필요 없을 수 있습니다.)

**(6) 오류 처리 및 사용자 경험**

- Gemini API 호출 중 발생할 수 있는 오류(네트워크 오류, API 키 오류, 할당량 초과 등)를 `call_gemini` 노드 내에서 적절히 처리하고, 그 결과를 상태에 반영하여 UI에 피드백을 줄 수 있도록 합니다 (`error_message` 상태 필드 활용).
- API 호출 중에는 "Gemini로 전송" 버튼을 비활성화하고 상태 표시줄에 진행 상황을 표시하여 사용자 경험을 개선합니다.

**5. 추가 고려 사항**

- **스트리밍**: LangGraph는 `stream` 메서드를 지원하여 Gemini API의 응답을 실시간으로 받아 UI에 표시할 수 있습니다. 이를 구현하면 사용자 경험을 크게 향상시킬 수 있지만, PyQt 스레딩 및 시그널 처리가 더 복잡해질 수 있습니다.
- **LangSmith**: 개발 및 디버깅을 위해 LangSmith 연동을 고려해볼 수 있습니다. LangGraph 실행 과정을 추적하고 분석하는 데 도움이 됩니다. (`os.environ["LANGCHAIN_TRACING_V2"] = "true"` 등 환경 변수 설정 필요)
- **XML 파싱 견고성**: `<summary>` 태그 외에 다른 방식으로 XML과 Summary가 구분될 가능성도 고려하여 `process_response` 노드의 파싱 로직을 더 견고하게 만들 수 있습니다. (예: 정규식 사용, LLM에게 특정 구분자 사용 요청 등)
- **모델 선택**: `config.yml`이나 UI를 통해 사용할 Gemini 모델(예: `gemini-1.5-pro-latest`, `gemini-1.5-flash-latest`)을 선택할 수 있도록 확장할 수 있습니다.
