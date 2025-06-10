from typing import Callable, Dict, Type
from pydantic import BaseModel
import logging

logger_base_bus = logging.getLogger(__name__)

class Command(BaseModel): 
    """Base command class for all commands in the system"""
    pass

class BaseCommandBus:
    """Base class for feature-specific command buses"""
    
    # Each subclass gets its own _handlers dict initialized
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._handlers = {}
        logger_base_bus.debug(f"Initialized _handlers for subclass: {cls.__name__}")

    @classmethod
    def register(cls, cmd_type: Type[Command]):
        """Decorator to register command handlers"""
        def decorator(fn: Callable):
            if not hasattr(cls, '_handlers') or not isinstance(cls._handlers, dict):
                logger_base_bus.warning(f"_handlers not properly initialized for {cls.__name__}. Initializing now.")
                cls._handlers = {}
            
            cls._handlers[cmd_type] = fn
            logger_base_bus.info(f"Handler {fn.__name__} registered for command {cmd_type.__name__} in bus {cls.__name__}. Current handlers count: {len(cls._handlers)}")
            return fn
        return decorator

    @classmethod
    async def handle(cls, cmd: Command):
        """Handle a command by dispatching to the appropriate handler"""
        if not hasattr(cls, '_handlers') or not isinstance(cls._handlers, dict):
            logger_base_bus.error(f"Cannot handle command: _handlers not initialized for {cls.__name__}")
            raise ValueError(f"_handlers not initialized for command bus {cls.__name__}")

        handler = cls._handlers.get(type(cmd))
        if handler:
            return await handler(cmd)
        else:
            logger_base_bus.error(f"No handler registered for command type {type(cmd)} in {cls.__name__}. Available handlers: {list(cls._handlers.keys())}")
            raise ValueError(f"No handler registered for command type {type(cmd)} in {cls.__name__}")