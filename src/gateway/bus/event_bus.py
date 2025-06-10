from collections import defaultdict
from typing import Callable, DefaultDict, Any, Type
import logging

logger = logging.getLogger(__name__)

class Event:
    """Base event class for all events in the system"""
    pass

class EventBus:
    """Global event bus for cross-feature communication"""
    _subs: DefaultDict[Type[Event], list[Callable]] = defaultdict(list)

    @classmethod
    def on(cls, event_type: Type[Event]):
        """Decorator to register event handlers"""
        def decorator(fn: Callable):
            cls._subs[event_type].append(fn)
            logger.debug(f"Handler {fn.__name__} registered for event {event_type.__name__}")
            return fn
        return decorator

    @classmethod
    def emit(cls, event: Event, *args, **kwargs):
        """Emit an event to all registered handlers"""
        event_type = type(event)
        if event_type in cls._subs:
            logger.debug(f"Emitting event {event_type.__name__} to {len(cls._subs[event_type])} handlers. Event data: {event}")
            for fn in cls._subs[event_type]:
                try:
                    fn(event, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in event handler {fn.__name__} for event {event_type.__name__}: {e}", exc_info=True)
        else:
            logger.debug(f"No handlers registered for event {event_type.__name__}")