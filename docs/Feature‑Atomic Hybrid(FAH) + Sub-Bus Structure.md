# Feature‑Atomic Hybrid(FAH) – **대규모 Slice 대비 기본 설계** 📚

> **목표** : 처음부터 **15 + Slice** 규모를 염두에 두고, _기능별 서브‑Bus_ 구조를 도입한 **Feature 중심 + Atomic 재사용 + Gateway Hub** 아키텍처를 제시합니다.

---

## 1. 핵심 개념 한눈에

| 레이어 | 설계 포인트 | 이유 |
| :--- | :--- | :--- |
| **Feature Slice** | 기능별 디렉터리, 내부 Atoms→Molecules→Organisms | 컨텍스트 최소화·재사용성 극대화 |
| **Gateway Hub** | _기능별 서브‑Command Bus_ + **공용 Event Bus** + **Service Locator** | 거대한 dict → 여러 Bus 인스턴스로 분산 → 로딩·토큰·메모리 최적화 |
| **Shared Atoms** | 공통 유틸 + 도메인 無 의존 | DRY·단위 테스트 쉽다 |

> **서브‑Command Bus 패턴** : 기능(Slice)마다 전용 Bus 모듈(`payments_command_bus.py`, `images_command_bus.py` …)을 두고, `gateway/__init__.py` 에서 _Facade_ 로 묶어 노출합니다.

---

## 2. 기본 폴더 구조 (15 + Slice 대응)

> **BASELINE** : 애초에 15개 이상 기능(Slice)을 예상하고 설계합니다. 모든 기능이 **서브‑Command Bus**를 갖도록 Gateway Hub를 구성합니다.

```tree
project-root/
├── src/
│   ├── gateway/
│   │   ├── __init__.py                # Facade – 서브 Bus·Event·Locator 재-export
│   │   ├── bus/                       # 기능별 서브‑Bus 모듈 폴더
│   │   │   ├── _base.py               # BaseCommandBus 공통 로직
│   │   │   ├── <feature_a>_command_bus.py
│   │   │   ├── <feature_b>_command_bus.py
│   │   │   ├── <feature_c>_command_bus.py
│   │   │   └── __init__.py            # Bus 모듈 자동 수집
│   │   ├── event_bus.py               # 공용 Event Bus
│   │   └── service_locator.py         # 공용 리소스 등록소
│   │
│   ├── features/                      # 기능 슬라이스들
│   │   ├── <feature_a>/
│   │   ├── <feature_b>/
│   │   └── <feature_c>/
│   │       ├── atoms/
│   │       ├── molecules/
│   │       ├── organisms/
│   │       ├── commands.py            # Pydantic Command 정의
│   │       ├── handlers.py            # <feature_c>CommandBus.register()
│   │       ├── tests/                 # Slice-specific tests
│   │       └── README.md
│   │
│   ├── shared/
│   │   └── atoms/                     # 공통 유틸
│   │
│   └── main.py                        # 배치 처리 등 진입점
│
├── tests/                             # Project-level tests (outside src)
├── configs/                           # Configuration files
├── resources/                         # Static resources
├── data/                              # Data files
📄 pyproject.toml
📄 README.md
... (other project files)
```

---

## 3. Gateway Hub 구현 ✨

### 3‑1 서브‑Command Bus 템플릿 (`src/gateway/bus/_base.py`)

```python
from typing import Callable, Dict, Type
from pydantic import BaseModel
import logging

logger_base_bus = logging.getLogger(__name__)

class Command(BaseModel): ...

class BaseCommandBus:
    # 각 서브클래스가 고유 핸들러를 갖도록 __init_subclass__에서 초기화
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._handlers = {}
        logger_base_bus.debug(f"Initialized _handlers for subclass: {cls.__name__}")

    @classmethod
    def register(cls, cmd_type: Type[Command]):
        def decorator(fn: Callable):
            if not hasattr(cls, '_handlers') or not isinstance(cls._handlers, dict):
                logger_base_bus.warning(f"_handlers not properly initialized for {cls.__name__}. Initializing now.")
                cls._handlers = {}
            
            cls._handlers[cmd_type] = fn
            logger_base_bus.info(f"Handler {fn.__name__} registered for command {cmd_type.__name__} in bus {cls.__name__}. Current handlers count: {len(cls._handlers)}")
            return fn
        return decorator

    @classmethod
    async def handle(cls, cmd: Command): # async로 변경
        if not hasattr(cls, '_handlers') or not isinstance(cls._handlers, dict):
             logger_base_bus.error(f"Cannot handle command: _handlers not initialized for {cls.__name__}")
             raise ValueError(f"_handlers not initialized for command bus {cls.__name__}")

        handler = cls._handlers.get(type(cmd))
        if handler:
            return await handler(cmd) # await 추가
        else:
            logger_base_bus.error(f"No handler registered for command type {type(cmd)} in {cls.__name__}. Available handlers: {list(cls._handlers.keys())}")
            raise ValueError(f"No handler registered for command type {type(cmd)} in {cls.__name__}")
```

### 3‑2 서브 Bus 템플릿 (`src/gateway/bus/<feature_x>_command_bus.py`)

```python
from ._base import BaseCommandBus

class <FeatureX>CommandBus(BaseCommandBus):
    """<Feature X> Slice 전용 Bus"""
```

> **특징** : 기능별 Bus 는 상속만 받으면 끝 – 핸들러는 `<FeatureX>CommandBus.register()` 로 연결합니다.

### 3‑3 Bus Facade (`src/gateway/__init__.py`)

```python
from importlib import import_module
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_bus_pkg_path = Path(__file__).parent / "bus"
if _bus_pkg_path.is_dir():
    for file in _bus_pkg_path.glob("*_command_bus.py"):
        module_name = f"src.gateway.bus.{file.stem}" # src. 추가
        try:
            module = import_module(module_name)
            bus_class_name = next((name for name in dir(module) if name.endswith("CommandBus") and name != "BaseCommandBus"), None)
            if bus_class_name:
                bus_instance_name = file.stem 
                globals()[bus_instance_name] = getattr(module, bus_class_name)
                logger.info(f"Successfully loaded and registered Command Bus: {bus_instance_name} (Class: {bus_class_name})")
            else:
                logger.warning(f"Could not find a CommandBus class in module: {module_name}")
        except ImportError as e:
            logger.error(f"Failed to import Command Bus module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error processing Command Bus module {module_name}: {e}")
else:
    logger.warning(f"Command Bus package directory not found: {_bus_pkg_path}")


from .event_bus import EventBus  # 공용 이벤트 버스
from .service_locator import ServiceLocator
```

- **사용 예** : `from src import gateway as gw; await gw.<feature_x>_command_bus.handle(cmd)` (`src` 디렉터리가 `PYTHONPATH`에 포함되어 `src`를 직접 임포트할 수 있어야 함)

### 3‑4 Event Bus (`src/gateway/event_bus.py`)

```python
from collections import defaultdict
from typing import Callable, DefaultDict, Any, Type
import logging

logger = logging.getLogger(__name__)

class Event:
    """이벤트의 기본 클래스로, 특정 이벤트 유형에 대해 서브클래싱할 수 있습니다."""
    pass

class EventBus:
    _subs: DefaultDict[Type[Event], list[Callable]] = defaultdict(list)

    @classmethod
    def on(cls, event_type: Type[Event]): # 파라미터 변경
        def decorator(fn: Callable):
            cls._subs[event_type].append(fn)
            logger.debug(f"Handler {fn.__name__} registered for event {event_type.__name__}")
            return fn
        return decorator

    @classmethod
    def emit(cls, event: Event, *args, **kwargs): # 파라미터 변경
        event_type = type(event)
        if event_type in cls._subs:
            logger.debug(f"Emitting event {event_type.__name__} to {len(cls._subs[event_type])} handlers. Event data: {event}")
            for fn in cls._subs[event_type]:
                try:
                    fn(event, *args, **kwargs) # event 인스턴스 전달
                except Exception as e:
                    logger.error(f"Error in event handler {fn.__name__} for event {event_type.__name__}: {e}", exc_info=True)
        else:
            logger.debug(f"No handlers registered for event {event_type.__name__}")
```

### 3‑5 Service Locator (`src/gateway/service_locator.py`)

```python
import logging
from typing import Any, Dict

_internal_logger = logging.getLogger("src.gateway.service_locator")

_module_level_pool: Dict[str, Any] = {} # 모듈 레벨 변수로 변경
_module_level_pool_initialized_log_done = False

if not _module_level_pool_initialized_log_done:
    _internal_logger.debug(f"ServiceLocator module instance created/imported. Initial _module_level_pool id: {id(_module_level_pool)}, content: {list(_module_level_pool.keys()) if _module_level_pool else 'empty'}")
    _module_level_pool_initialized_log_done = True

class ServiceLocator:
    _class_info_logged = False

    @classmethod
    def _log_class_info_once(cls):
        if not cls._class_info_logged:
            _internal_logger.debug(f"ServiceLocator class accessed. id(ServiceLocator class): {id(cls)}")
            cls._class_info_logged = True

    @classmethod
    def provide(cls, key: str, obj: Any) -> None:
        cls._log_class_info_once()
        global _module_level_pool
        _internal_logger.debug(f"[PROVIDE PRE] Key: '{key}', Current _module_level_pool id: {id(_module_level_pool)}, Current _module_level_pool keys: {list(_module_level_pool.keys())}")
        if key in _module_level_pool:
            _internal_logger.warning(f"Service key '{key}' already exists in ServiceLocator. Overwriting.")
        _module_level_pool[key] = obj
        _internal_logger.debug(f"[PROVIDE POST] Service '{key}' (type: {type(obj).__name__}) provided. New _module_level_pool keys: {list(_module_level_pool.keys())}, _module_level_pool id: {id(_module_level_pool)}")

    @classmethod
    def get(cls, key: str) -> Any:
        cls._log_class_info_once()
        global _module_level_pool
        _internal_logger.debug(f"[GET PRE] Key: '{key}', Current _module_level_pool id: {id(_module_level_pool)}, Current _module_level_pool keys: {list(_module_level_pool.keys())}")
        try:
            service = _module_level_pool[key]
            _internal_logger.debug(f"[GET POST] Service '{key}' (type: {type(service).__name__}) retrieved successfully.")
            return service
        except KeyError:
            _internal_logger.error(f"Service key '{key}' not found in ServiceLocator. _module_level_pool id: {id(_module_level_pool)}, Available services: {list(_module_level_pool.keys())}")
            raise KeyError(f"Service '{key}' not found. Available services: {list(_module_level_pool.keys())}")

    @classmethod
    def reset(cls) -> None:
        cls._log_class_info_once()
        global _module_level_pool
        _internal_logger.info(f"[RESET PRE] Current _module_level_pool id: {id(_module_level_pool)}, Current _module_level_pool keys: {list(_module_level_pool.keys())}")
        _module_level_pool.clear()
        _internal_logger.info(f"[RESET POST] ServiceLocator._module_level_pool has been cleared. _module_level_pool id: {id(_module_level_pool)}")
```

---

## 4. Slice‑측 코드 연결 가이드

> **자세한 예시는 ‘부록 A’에서 `images_resize` Slice를 참조하세요.** (주의: `images_resize`는 예시일 뿐, 현재 프로젝트에는 해당 Slice가 없습니다. 실제 프로젝트의 Slice 구조를 참고하세요.)

Slice 폴더 (`src/features/<feature_name>/`)의 `commands.py`와 `handlers.py`에서 다음 순서로 구현합니다:

1. `commands.py` – Pydantic `BaseModel`로 Command 객체 정의.
2. `handlers.py` – 해당 Slice 전용 **Command Bus**에 핸들러 등록. (핸들러는 `async`로 정의)
3. 비즈니스 로직 수행 후 필요 시 **Event Bus**로 이벤트 발행.

---

## 5. 테스트 전략 🧪 (대규모용)

| 레벨 | 도구 | 포인트 |
| :--- | :--- | :--- |
| Atom | pytest | 순수 함수 단위 |
| Slice | pytest‑cov | 서브 Bus → 핸들러 → Event 연동 |
| Bus | pytest | Bus 모듈 자동 로딩, 핸들러 중복 확인 |

---

## 6. CI 체크리스트 ✅

- Bus 모듈 추가 시 **linter**로 `*CommandBus` 클래스 여부 검증.
- `pytest‑cov` 로 Slice 커버리지 > 80 % 유지.
- `mkdocs` 로 `/docs` 자동 배포.

---

> 이렇게 처음부터 **기능별 서브‑Bus** 기반으로 설계하면, Slice 수가 급증해도 Bus 당 핸들러 수가 제한되어 유지보수·토큰·메모리 측면 모두 유리합니다!

---

---

## 부록 A. `images_resize` Slice 구조 예시 🖼️

> 아래 예시는 _썸네일 변환_ 기능이 FAH 구조에 어떻게 배치될 수 있는지 **구조와 핵심 코드 스니펫**만 보여줍니다. 모든 경로는 `src` 폴더를 기준으로 합니다. (주의: `images_resize`는 예시일 뿐, 현재 프로젝트에는 해당 Slice가 없습니다.)

### A.0 디렉터리 구조

```tree
src/
└── features/
    └── images_resize/
        ├── atoms/
        │   └── image_io.py            # 이미지 입·출력 유틸
        ├── molecules/
        │   └── resizer.py             # 리사이즈 로직
        ├── organisms/
        │   └── thumbnail_workflow.py  # 썸네일 파이프라인
        ├── commands.py                # ResizeImage Command
        ├── handlers.py                # Bus 핸들러 등록
        ├── tests/
        └── README.md
```

### A.1 `ImagesResizeCommandBus` (`src/gateway/bus/images_resize_command_bus.py`)

```python
from ._base import BaseCommandBus

class ImagesResizeCommandBus(BaseCommandBus):
    """images_resize Slice 전용 Bus"""
```

> **설명** : 이 파일은 `BaseCommandBus`를 상속해 **`images_resize` Slice 전용 명령 라우터**를 정의합니다. `register()` 데코레이터로 핸들러를 등록하고, `handle()` 메서드로 전달된 `ResizeImage` 명령을 올바른 핸들러에 위임합니다.

### A.2 Gateway Facade 호출 예 (`src/main.py`)

```python
from src import gateway as gw # src가 PYTHONPATH에 있다면 가능
from src.features.images_resize.commands import ResizeImage # src가 PYTHONPATH에 있다면 가능 (예시 경로)
import asyncio # asyncio 추가

async def main(): # async main 함수로 변경
    cmd = ResizeImage(id="cat001", width=128, height=128)
    result = await gw.images_resize_command_bus.handle(cmd) # await 추가
    print(result)

if __name__ == "__main__":
    asyncio.run(main()) # asyncio.run으로 실행
```

> **설명** : `gateway` 모듈을 **단일 Facade**로 불러와 `images_resize_command_bus`를 사용합니다. ① `ResizeImage` 명령 객체 생성 → ② 해당 Bus `handle()` 호출 (비동기) → ③ 등록된 핸들러 실행 후 결과를 반환하는 전체 흐름을 보여 줍니다. (`src` 폴더가 `PYTHONPATH`에 포함되어 있다고 가정합니다.)

### A.3 Event Bus 리스너 (`src/features/analytics/handlers.py`)

```python
from src.gateway.event_bus import EventBus, Event # src. 추가, Event 클래스 임포트
# from src.features.images_resize.events import ImageResizedEvent # 실제 이벤트 클래스 임포트 가정 (예시 경로)

# class ImageResizedEvent(Event): # 예시 이벤트 정의
#     def __init__(self, id: str):
#         self.id = id

# @EventBus.on(ImageResizedEvent) # 실제 이벤트 클래스 사용
def collect_metrics(event: Event): # 파라미터 변경 (event: ImageResizedEvent)
    # 썸네일 생성 통계 업데이트
    # print(f"Thumbnail ready for image {event.id}")
    print(f"Thumbnail ready for image {getattr(event, 'id', 'unknown')}") # getattr로 안전하게 접근
```

> **설명** : `EventBus.on()` 데코레이터로 **특정 이벤트 타입(`ImageResizedEvent` 등)**을 구독하고, 썸네일 생성이 완료될 때마다 간단한 통계 출력을 수행하는 예입니다. 핵심 로직과 통계 로직을 분리해 모듈 간 의존을 최소화합니다.

### A.4 Service Locator 초기화 (`src/main.py`)

```python
from src.gateway.service_locator import ServiceLocator # src. 추가
# from src.infrastructure.local_storage import LocalDiskStorage # src/infrastructure에 있다고 가정 (예시 경로)

# class LocalDiskStorage: # 예시 스토리지 클래스
#     def __init__(self, path): self.path = path
#     def load(self, id): print(f"Loading {id} from {self.path}"); return f"Image data for {id}"
#     def save(self, id, data): print(f"Saving {data} for {id} to {self.path}")

# ServiceLocator.provide("storage", LocalDiskStorage("./data")) # 경로는 프로젝트 루트 기준일 수 있음
```

> **설명** : `ServiceLocator`에 로컬 스토리지 구현체를 등록합니다. 핸들러는 키 `"storage"`로 스토리지를 조회하므로, 나중에 S3·MinIO 구현체로 교체할 때 **이 한 줄만 바꾸면** 됩니다. (`infrastructure` 패키지가 `src` 내에 위치한다고 가정합니다.)

### A.5 핸들러 등록 (`src/features/images_resize/handlers.py`)

```python
from src.gateway.bus.images_resize_command_bus import ImagesResizeCommandBus # src. 추가 (예시 경로)
from src.gateway.event_bus import EventBus, Event # src. 추가, Event 클래스 임포트
from src.gateway.service_locator import ServiceLocator # src. 추가
from .commands import ResizeImage # 현재 디렉터리 내 commands 모듈이므로 .commands 사용
import asyncio # 예시를 위해 추가

# class ImageResizedEvent(Event): # 예시 이벤트 정의
#     def __init__(self, id: str):
#         self.id = id

# class MockImage: # 예시 이미지 클래스
#     def resize(self, size): return f"Resized image to {size}"

@ImagesResizeCommandBus.register(ResizeImage)
async def handle_resize(cmd: ResizeImage): # async로 변경
    storage = ServiceLocator.get("storage")
    # img_data = storage.load(cmd.id) # 실제 로직에서는 이미지 객체 반환 가정
    # img = MockImage() # 예시 이미지 객체
    # thumb = img.resize((cmd.width, cmd.height))
    # storage.save(cmd.id, thumb)
    # EventBus.emit(ImageResizedEvent(id=cmd.id)) # 실제 이벤트 객체 사용
    # return f"Thumbnail for {cmd.id} processed." # 결과 반환 예시
    await asyncio.sleep(0.1) # 비동기 작업 예시
    print(f"Resizing image {cmd.id} to {cmd.width}x{cmd.height} using {storage}")
    EventBus.emit(Event()) # 간단한 이벤트 발생 예시
    return f"Image {cmd.id} resize requested."
```

> **설명** : 핸들러는 ① `ServiceLocator`에서 스토리지 인스턴스 획득 → ② 원본 이미지 로드 → ③ 리사이즈 수행 → ④ 저장 → ⑤ `EventBus.emit()`으로 후속 작업을 알리는 **비동기 순수 함수** 구현입니다. 의존성이 명확하므로 단위 테스트와 AI 코드 이해가 용이합니다.
