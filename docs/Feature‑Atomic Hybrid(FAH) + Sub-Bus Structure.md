# Feature‑Atomic Hybrid(FAH) – **대규모 Slice 대비 기본 설계** 📚

> **목표** : 처음부터 **15 + Slice** 규모를 염두에 두고, _기능별 서브‑Bus_ 구조를 도입한 **Feature 중심 + Atomic 재사용 + Gateway Hub** 아키텍처를 제시합니다.

---

## 1. 핵심 개념 한눈에

| 레이어            | 설계 포인트                                                          | 이유                                                             |
| ----------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Feature Slice** | 기능별 디렉터리, 내부 Atoms→Molecules→Organisms                      | 컨텍스트 최소화·재사용성 극대화                                  |
| **Gateway Hub**   | _기능별 서브‑Command Bus_ + **공용 Event Bus** + **Service Locator** | 거대한 dict → 여러 Bus 인스턴스로 분산 → 로딩·토큰·메모리 최적화 |
| **Shared Atoms**  | 공통 유틸 + 도메인  無 의존                                          | DRY·단위 테스트 쉽다                                             |

> **서브‑Command Bus 패턴** : 기능(Slice)마다 전용 Bus 모듈(`payments_command_bus.py`, `images_command_bus.py` …)을 두고, `gateway/__init__.py` 에서 _Facade_ 로 묶어 노출합니다.

---

## 2. 기본 폴더 구조 (15 + Slice 대응)

> **BASELINE** : 애초에 15개 이상 기능(Slice)을 예상하고 설계합니다. 모든 기능이 *서브‑Command Bus*를 갖도록 Gateway Hub를 구성합니다.

```tree
project-root/
├── gateway/
│   ├── __init__.py                # Facade – 서브 Bus·Event·Locator 재-export
│   ├── bus/                       # 기능별 서브‑Bus 모듈 폴더
│   │   ├── _base.py               # BaseCommandBus 공통 로직
│   │   ├── <feature_a>_command_bus.py
│   │   ├── <feature_b>_command_bus.py
│   │   ├── <feature_c>_command_bus.py
│   │   └── __init__.py            # Bus 모듈 자동 수집
│   ├── event_bus.py               # 공용 Event Bus
│   └── service_locator.py         # 공용 리소스 등록소
│
├── features/                      # 기능 슬라이스들
│   ├── <feature_a>/
│   ├── <feature_b>/
│   └── <feature_c>/
│       ├── atoms/
│       ├── molecules/
│       ├── organisms/
│       ├── commands.py            # Pydantic Command 정의
│       ├── handlers.py            # <feature_c>CommandBus.register()
│       ├── tests/
│       └── README.md
│
├── shared/
│   └── atoms/                     # 공통 유틸
│
└── main.py                        # CLI·배치·UI 등 진입점
```

---

## 3. Gateway Hub 구현 ✨

### 3‑1 서브‑Command Bus 템플릿 (`gateway/bus/_base.py`)

```python
from typing import Callable, Dict, Type
from pydantic import BaseModel

class Command(BaseModel): ...

class BaseCommandBus:
    _handlers: Dict[Type[Command], Callable] = {}

    @classmethod
    def register(cls, cmd_type: Type[Command]):
        def decorator(fn: Callable):
            cls._handlers[cmd_type] = fn
            return fn
        return decorator

    @classmethod
    def handle(cls, cmd: Command):
        return cls._handlers[type(cmd)](cmd)
```

### 3‑2 서브 Bus 템플릿 (gateway/bus/\<feature_x>\_command_bus.py)

```python
from ._base import BaseCommandBus

class <FeatureX>CommandBus(BaseCommandBus):
    """<Feature X> Slice 전용 Bus"""
```

> **특징** : 기능별 Bus 는 상속만 받으면 끝 – 핸들러는 `<FeatureX>CommandBus.register()` 로 연결합니다.

### 3‑3 Bus Facade (`gateway/__init__.py`)

```python
from importlib import import_module
from pathlib import Path

# 모든 Bus 모듈 자동 import → gw.images_bus.handle(cmd) 식으로 사용 가능
_bus_pkg = Path(__file__).parent / "bus"
for file in _bus_pkg.glob("*_command_bus.py"):
    mod = import_module(f"gateway.bus.{file.stem}")
    globals()[file.stem] = getattr(mod, [n for n in dir(mod) if n.endswith("CommandBus")][0])

from .event_bus import EventBus  # 공용 이벤트 버스
from .service_locator import ServiceLocator
```

- **사용 예** : `import gateway as gw; gw.<feature_x>_command_bus.handle(cmd)`

### 3‑4 Event Bus (`gateway/event_bus.py`)

```python
from collections import defaultdict
from typing import Callable, DefaultDict

class EventBus:
    _subs: DefaultDict[str, list[Callable]] = defaultdict(list)
    @classmethod
    def on(cls, topic: str):
        def deco(fn: Callable):
            cls._subs[topic].append(fn); return fn
        return deco
    @classmethod
    def emit(cls, topic: str, *args, **kw):
        for fn in cls._subs[topic]: fn(*args, **kw)
```

### 3‑5 Service Locator (`gateway/service_locator.py`)

```python
class ServiceLocator:
    _pool = {}
    def provide(key, obj): ServiceLocator._pool[key] = obj
    def get(key): return ServiceLocator._pool[key]
```

---

## 4. Slice‑측 코드 연결 가이드

> **자세한 예시는 ‘부록 A’에서 `images_resize` Slice를 참조하세요.**

Slice 폴더의 `commands.py`와 `handlers.py`에서 다음 순서로 구현합니다:

1. `commands.py` – Pydantic `BaseModel`로 Command 객체 정의.
2. `handlers.py` – 해당 Slice 전용 **Command Bus**에 핸들러 등록.
3. 비즈니스 로직 수행 후 필요 시 **Event Bus**로 이벤트 발행.

---

## 5. 테스트 전략 🧪 (대규모용) 테스트 전략 🧪 (대규모용) 테스트 전략 🧪 (대규모용)

| 레벨  | 도구       | 포인트                               |
| ----- | ---------- | ------------------------------------ |
| Atom  | pytest     | 순수 함수 단위                       |
| Slice | pytest‑cov | 서브 Bus → 핸들러 → Event 연동       |
| Bus   | pytest     | Bus 모듈 자동 로딩, 핸들러 중복 확인 |

---

## 6. CI 체크리스트 ✅

- Bus 모듈 추가 시 **linter**로 `*CommandBus` 클래스 여부 검증.
- `pytest‑cov` 로 Slice 커버리지 > 80 % 유지.
- `mkdocs` 로 `/docs` 자동 배포.

---

> 이렇게 처음부터 **기능별 서브‑Bus** 기반으로 설계하면, Slice 수가 급증해도 Bus 당 핸들러 수가 제한되어 유지보수·토큰·메모리 측면 모두 유리합니다!

---

---

## 부록 A. `images_resize` Slice 구조 예시 🖼️

> 아래 예시는 _썸네일 변환_ 기능이 FAH 구조에 어떻게 배치될 수 있는지 **구조와 핵심 코드 스니펫**만 보여줍니다.

### A.0 디렉터리 구조

```tree
features/
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

### A.1 `ImagesResizeCommandBus`  `gateway/bus/images_resize_command_bus.py`

```python
from ._base import BaseCommandBus

class ImagesResizeCommandBus(BaseCommandBus):
    """images_resize Slice 전용 Bus"""
```

> **설명** : 이 파일은 `BaseCommandBus`를 상속해 **`images_resize` Slice 전용 명령 라우터**를 정의합니다. `register()` 데코레이터로 핸들러를 등록하고, `handle()` 메서드로 전달된 `ResizeImage` 명령을 올바른 핸들러에 위임합니다.

### A.2 Gateway Facade 호출 예 `main.py` Gateway Facade 호출 예  `main.py`

```python
import gateway as gw
from features.images_resize.commands import ResizeImage

cmd = ResizeImage(id="cat001", width=128, height=128)
result = gw.images_resize_command_bus.handle(cmd)
print(result)
```

> **설명** : `gateway` 모듈을 **단일 Facade**로 불러와 `images_resize_command_bus`를 사용합니다. ① `ResizeImage` 명령 객체 생성 → ② 해당 Bus `handle()` 호출 → ③ 등록된 핸들러 실행 후 결과를 반환하는 전체 흐름을 보여 줍니다.

### A.3 Event Bus 리스너 `features/analytics/handlers.py` Event Bus 리스너  `features/analytics/handlers.py`

```python
from gateway.event_bus import EventBus

@EventBus.on("image.resized")
def collect_metrics(id: str):
    # 썸네일 생성 통계 업데이트
    print(f"Thumbnail ready for image {id}")
```

> **설명** : `EventBus.on()` 데코레이터로 **`image.resized` 이벤트**를 구독하고, 썸네일 생성이 완료될 때마다 간단한 통계 출력을 수행하는 예입니다. 핵심 로직과 통계 로직을 분리해 모듈 간 의존을 최소화합니다.

### A.4 Service Locator 초기화 `main.py` Service Locator 초기화  `main.py`

```python
from gateway.service_locator import ServiceLocator
from infrastructure.local_storage import LocalDiskStorage

ServiceLocator.provide("storage", LocalDiskStorage("./data"))
```

> **설명** : `ServiceLocator`에 로컬 스토리지 구현체를 등록합니다. 핸들러는 키 `"storage"`로 스토리지를 조회하므로, 나중에 S3·MinIO 구현체로 교체할 때 **이 한 줄만 바꾸면** 됩니다.

### A.5 핸들러 등록 `features/images_resize/handlers.py` 핸들러 등록  `features/images_resize/handlers.py`

```python
from gateway.bus.images_resize_command_bus import ImagesResizeCommandBus
from gateway.event_bus import EventBus
from gateway.service_locator import ServiceLocator
from .commands import ResizeImage

@ImagesResizeCommandBus.register(ResizeImage)
def handle_resize(cmd: ResizeImage):
    storage = ServiceLocator.get("storage")
    img = storage.load(cmd.id)
    thumb = img.resize((cmd.width, cmd.height))
    storage.save(cmd.id, thumb)
    EventBus.emit("image.resized", id=cmd.id)
```

> **설명** : 핸들러는 ① `ServiceLocator`에서 스토리지 인스턴스 획득 → ② 원본 이미지 로드 → ③ 리사이즈 수행 → ④ 저장 → ⑤ `EventBus.emit()`으로 후속 작업을 알리는 **순수 함수** 구현입니다. 의존성이 명확하므로 단위 테스트와 AI 코드 이해가 용이합니다.
