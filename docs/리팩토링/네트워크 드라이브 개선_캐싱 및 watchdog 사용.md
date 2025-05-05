# 네트워크 드라이브 성능 개선을 위한 리팩토링 가이드

**목표:** 네트워크 드라이브에 위치한 프로젝트 폴더를 사용할 때 발생하는 UI 렉 및 로딩 지연 문제를 해결하여 사용자 경험을 향상합니다.

**핵심 전략:**

1. **디렉토리 구조 캐싱:** 실제 파일 시스템 대신 메모리에 캐싱된 디렉토리 구조를 기반으로 파일 탐색기 UI를 표시합니다.
2. **백그라운드 스캔:** 초기 로딩 및 새로고침 시 디렉토리 스캔 작업을 백그라운드 스레드에서 수행하여 UI 멈춤 현상을 방지합니다.
3. **점진적 로딩 (Progressive Loading):** 초기 스캔 시 지정된 깊이까지만 로드하고, 사용자가 폴더를 확장할 때 필요한 하위 구조를 비동기적으로 로드하여 초기 로딩 시간을 단축합니다.
4. **실시간 변경 감지 (`watchdog`):** 파일 시스템 변경 사항을 감지하여 캐시를 자동으로 업데이트합니다. (네트워크 드라이브 불안정성 고려)
5. **수동 새로고침:** 사용자가 원할 때 캐시를 강제로 갱신할 수 있는 기능을 제공합니다.
6. **로딩 상태 표시:** 캐싱 및 스캔 작업 진행 상태를 사용자에게 시각적으로 표시합니다.

**주요 변경 대상 컴포넌트:**

- **`DirectoryCacheService` (신규):** 디렉토리 구조(경로, 이름, 타입 등)를 저장하고 관리하는 인메모리 캐시 서비스. 스레드 안전성 보장 필요.
- **`DirectoryScannerWorker` (신규):** 백그라운드 스레드(`QThread`/`QObject`)에서 파일 시스템을 스캔하고 `DirectoryCacheService`를 업데이트하는 워커. 진행 상태 시그널 포함.
- **`WatchdogMonitorService` (신규):** 백그라운드 스레드(`QThread`/`QObject`)에서 `watchdog` 라이브러리를 사용하여 파일 시스템 변경을 감지하고 캐시 업데이트 필요 시그널을 발생시키는 서비스. 네트워크 드라이브 오류 처리 강화 필요.
- **`CachedFileSystemModel` (수정/대체):** 기존 `FilteredFileSystemModel`을 캐시 기반으로 동작하도록 수정하거나 대체.
- **`CachedCheckableProxyModel` (수정):** 기존 `CheckableProxyModel`이 캐시 기반 모델과 상호작용하도록 수정. 필터링 로직도 캐시 활용 검토.
- **`FileTreeController` (수정):** 캐시 서비스, 스캐너, 왓치독 서비스 관리 및 UI 상호작용 로직 수정.
- **`MainWindow` (수정):** 신규 서비스 초기화/관리, UI 요소(새로고침 버튼, 상태 표시줄) 추가 및 시그널 연결.

**리팩토링 단계:**

**1단계: 디렉토리 캐시 서비스 구현 (`DirectoryCacheService`)**

- **목적:** 스캔된 디렉토리 정보를 메모리에 저장하고 빠르게 조회/수정하는 기능 제공.
- **데이터 구조:** 트리 형태의 자료구조 사용 (예: nested dictionaries, 사용자 정의 Node 클래스). 각 노드는 경로, 이름, 타입(파일/디렉토리), (선택적) 수정 시간 등의 정보를 포함.
- **주요 메서드:**
  - `get_node(path)`: 특정 경로의 노드 정보 반환.
  - `get_children(path)`: 특정 경로의 자식 노드 목록 반환.
  - `add_node(path, info)`: 새 노드 추가.
  - `remove_node(path)`: 노드 및 하위 노드 제거.
  - `update_node(path, info)`: 노드 정보 업데이트.
  - `clear()`: 캐시 전체 비우기.
  - `is_cached(path)`: 특정 경로가 캐시에 있는지 확인.
- **스레드 안전성:** 여러 스레드(UI, 스캐너, 왓치독)에서 동시에 접근할 수 있으므로, `threading.Lock` 또는 `QMutex`를 사용하여 주요 메서드 접근 제어.

**2단계: 백그라운드 디렉토리 스캐너 구현 (`DirectoryScannerWorker`)**

- **목적:** UI 스레드를 차단하지 않고 파일 시스템 스캔 수행.
- **기능:**
  - **초기 점진적 스캔:** 프로젝트 폴더 선택 시 지정된 초기 깊이(예: 1 또는 2)까지 스캔하여 캐시에 저장.
  - **하위 폴더 스캔:** 사용자가 트리에서 폴더를 확장할 때 해당 폴더의 하위 내용을 비동기적으로 스캔하여 캐시에 추가.
  - **전체 새로고침 스캔:** 수동 새로고침 요청 시 캐시를 비우고 전체 구조를 다시 스캔.
- **구현:** `QThread`와 `QObject` 워커 클래스 사용.
- **시그널:**
  - `scan_started()`: 스캔 시작 시그널.
  - `progress_updated(current_depth, items_scanned)`: 스캔 진행 상태 업데이트 시그널.
  - `scan_complete(success: bool, root_path: str)`: 스캔 완료 시그널 (성공 여부, 스캔 루트 경로 포함).
  - `error_occurred(message: str)`: 오류 발생 시그널.
- **상호작용:** `MainWindow` 또는 `FileTreeController`로부터 스캔 요청(루트 경로, 스캔 타입)을 받고, 스캔 결과를 `DirectoryCacheService`에 업데이트하며, 진행 상태/결과를 시그널로 UI에 알림.

**3단계: 파일 시스템 감시 서비스 구현 (`WatchdogMonitorService`)**

- **목적:** `watchdog`을 사용하여 파일 시스템 변경 사항 실시간 감지.
- **기능:**
  - 지정된 경로에 대한 모니터링 시작/중지.
  - 파일/폴더 생성, 삭제, 이동, 이름 변경 이벤트 처리.
- **구현:** `QThread`와 `QObject` 워커 클래스 사용. `watchdog.observers.Observer` 및 `watchdog.events.FileSystemEventHandler` 상속/활용.
- **시그널:**
  - `cache_needs_update(event_type: str, path1: str, path2: Optional[str] = None)`: 감지된 이벤트를 기반으로 캐시 업데이트 필요 시그널 (예: 'created', 'deleted', 'moved').
  - `error_occurred(message: str)`: `watchdog` 모니터링 중 오류 발생 시그널 (특히 네트워크 드라이브).
- **상호작용:** `MainWindow` 또는 `FileTreeController`에서 모니터링 시작/중지 요청. 감지된 이벤트를 캐시 업데이트 시그널로 변환하여 전달.
- **주의:** 네트워크 드라이브(SMB/CIFS 등)에서 `watchdog` 이벤트 감지의 불안정성(누락, 지연) 및 오류 발생 가능성에 대비한 견고한 오류 처리 로직 필요. (예: 오류 발생 시 자동 재시작 시도, 사용자에게 알림, 수동 새로고침 유도)

**4단계: UI 모델 수정 (`CachedFileSystemModel`, `CachedCheckableProxyModel`)**

- **목적:** 파일 탐색기 모델이 실제 파일 시스템 대신 `DirectoryCacheService`를 데이터 소스로 사용하도록 변경.
- **`CachedFileSystemModel` (수정 또는 대체):**
  - `rowCount`, `index`, `parent`, `hasChildren`, `fileInfo`, `filePath` 등 파일 시스템 정보를 반환하는 메서드를 캐시 조회 로직으로 수정.
  - `setRootPathFiltered`: 캐시 스캔 시작을 트리거하도록 수정 (백그라운드 스캐너 호출).
  - 캐시 업데이트 시그널(`DirectoryCacheService` 또는 관련 컨트롤러에서 발생)을 받아 `layoutChanged` 등 적절한 모델 업데이트 시그널을 발생시켜 UI 갱신.
- **`CachedCheckableProxyModel` (수정):**
  - `setSourceModel`: `CachedFileSystemModel`을 받도록 수정.
  - `filterAcceptsRow`: `fs_service.should_ignore` 호출 시 캐시된 파일 타입 정보를 사용하거나, 필요한 정보만 확인하도록 최적화. (여전히 `ignore` 패턴 확인은 필요)
  - `data`, `setData`: 캐시 기반 소스 모델과 상호작용하도록 수정. 파일 경로 획득 등에서 캐시 활용 검토.
  - 체크 상태 변경 시 `checked_files_dict` 관리 로직 유지.

**5단계: 서비스 통합 및 관리 (`MainWindow`, `FileTreeController`)**

- **`MainWindow`:**
  - `DirectoryCacheService`, `DirectoryScannerWorker`, `WatchdogMonitorService` 인스턴스 생성 및 관리.
  - 어플리케이션 시작/종료 시 서비스 초기화 및 정리.
  - 스캐너/왓치독 워커 스레드 관리 (시작, 중지, 시그널 연결).
  - 스캐너/왓치독 시그널을 받아 상태 표시줄 업데이트 및 모델 갱신 트리거.
- **`FileTreeController`:**
  - `select_project_folder`: 초기 백그라운드 스캔 시작 요청. 왓치독 모니터링 시작 요청.
  - `refresh_tree` (이름 변경 고려: `refresh_tree_from_cache`): UI 모델이 캐시를 다시 읽도록 갱신 (모델 시그널 사용).
  - `refresh_tree_manual` (신규): 수동 새로고침 버튼과 연결. 캐시 비우고 전체 백그라운드 스캔 요청.
  - `rename_item`, `delete_item`: 파일 시스템 작업 수행 _후_ 캐시 직접 업데이트 또는 왓치독/스캐너에 해당 경로 재검증 요청. (직접 업데이트 시 경쟁 조건 주의)

**6단계: UI 변경 사항 적용**

- **`MainWindow` (`main_window_setup_ui.py`):**
  - **새로고침 버튼 추가:** 파일 탐색기 영역 또는 상단 버튼 영역에 '새로고침' 버튼 추가.
  - **로딩 상태 표시줄 추가:** 상태 표시줄(`QStatusBar`)에 로딩 상태(`Scanning...`, `Loading depth 3...`, `Monitoring...`, `Idle`)를 표시할 `QLabel` 추가.
- **시그널 연결 (`main_window_setup_signals.py`):**
  - 새로고침 버튼의 `clicked` 시그널을 `FileTreeController.refresh_tree_manual` 슬롯에 연결.
  - 백그라운드 스캐너/왓치독의 `progress_updated`, `scan_complete`, `error_occurred`, `cache_needs_update` 시그널을 `MainWindow` 또는 `FileTreeController`의 상태 업데이트 및 모델 갱신 슬롯에 연결.

**7단계: 코드 수정 및 테스트**

- 위 단계에 따라 관련 Python 파일(`*.py`) 수정.
- **테스트:**
  - **로컬 드라이브:** 기본 기능 정상 동작 확인.
  - **네트워크 드라이브 (필수):** 실제 네트워크 드라이브 환경에서 테스트.
    - 대용량/깊은 폴더 구조 로딩 성능 측정.
    - UI 반응성 확인 (스캔 중 UI 멈춤 없는지).
    - 파일/폴더 생성, 삭제, 이름 변경 시 `watchdog` 감지 및 캐시/UI 업데이트 확인 (지연/누락 가능성 인지).
    - 수동 새로고침 기능 정상 동작 확인.
    - 로딩 상태 표시 정확성 확인.
    - 네트워크 연결 끊김 등 오류 상황 테스트.

**고려 사항 및 도전 과제:**

- **`watchdog` 안정성:** 네트워크 드라이브 종류 및 환경에 따른 `watchdog` 동작 차이 및 불안정성. 이벤트 누락/지연 시 수동 새로고침 기능이 중요.
- **캐시 동기화:** 파일 시스템 변경(외부 프로그램에 의한 변경 포함)과 캐시 간의 불일치 가능성. `watchdog` 이벤트 처리 및 수동 새로고침으로 완화.
- **경쟁 조건 (Race Condition):** 여러 스레드(UI, 스캐너, 왓치독)가 캐시를 동시에 수정하려 할 때 발생 가능. `DirectoryCacheService` 내 뮤텍스/락 구현 필수.
- **성능 튜닝:** 초기 스캔 깊이, 스캔 방식(깊이 우선 vs 너비 우선), 캐시 업데이트 빈도 등을 조절하여 성능 최적화.
- **오류 처리:** 네트워크 오류, 파일 접근 권한 오류 등에 대한 견고한 예외 처리.
- **복잡성 증가:** 비동기 처리, 스레드 관리, 캐시 동기화 등으로 코드 복잡성 증가.

**기대 효과:**

- 네트워크 드라이브 사용 시 파일 탐색기의 UI 반응성 대폭 향상.
- 대용량 프로젝트 폴더의 초기 로딩 시간 단축.
- 백그라운드 작업으로 인한 UI 멈춤 현상 제거.
- 로딩 상태 시각적 피드백으로 사용자 경험 개선.
