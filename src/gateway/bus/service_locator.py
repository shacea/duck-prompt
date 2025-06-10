import logging
from typing import Any, Dict

_internal_logger = logging.getLogger("src.gateway.service_locator")

# Module-level pool for services
_module_level_pool: Dict[str, Any] = {}
_module_level_pool_initialized_log_done = False

if not _module_level_pool_initialized_log_done:
    _internal_logger.debug(f"ServiceLocator module instance created/imported. Initial _module_level_pool id: {id(_module_level_pool)}, content: {list(_module_level_pool.keys()) if _module_level_pool else 'empty'}")
    _module_level_pool_initialized_log_done = True

class ServiceLocator:
    """Service locator pattern for dependency injection"""
    _class_info_logged = False

    @classmethod
    def _log_class_info_once(cls):
        if not cls._class_info_logged:
            _internal_logger.debug(f"ServiceLocator class accessed. id(ServiceLocator class): {id(cls)}")
            cls._class_info_logged = True

    @classmethod
    def provide(cls, key: str, obj: Any) -> None:
        """Register a service with the locator"""
        cls._log_class_info_once()
        global _module_level_pool
        _internal_logger.debug(f"[PROVIDE PRE] Key: '{key}', Current _module_level_pool id: {id(_module_level_pool)}, Current _module_level_pool keys: {list(_module_level_pool.keys())}")
        if key in _module_level_pool:
            _internal_logger.warning(f"Service key '{key}' already exists in ServiceLocator. Overwriting.")
        _module_level_pool[key] = obj
        _internal_logger.debug(f"[PROVIDE POST] Service '{key}' (type: {type(obj).__name__}) provided. New _module_level_pool keys: {list(_module_level_pool.keys())}, _module_level_pool id: {id(_module_level_pool)}")

    @classmethod
    def get(cls, key: str) -> Any:
        """Retrieve a service from the locator"""
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
        """Clear all registered services"""
        cls._log_class_info_once()
        global _module_level_pool
        _internal_logger.info(f"[RESET PRE] Current _module_level_pool id: {id(_module_level_pool)}, Current _module_level_pool keys: {list(_module_level_pool.keys())}")
        _module_level_pool.clear()
        _internal_logger.info(f"[RESET POST] ServiceLocator._module_level_pool has been cleared. _module_level_pool id: {id(_module_level_pool)}")