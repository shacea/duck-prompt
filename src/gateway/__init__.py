"""
Gateway module - Central hub for FAH architecture
Provides access to:
- Feature-specific command buses
- Global event bus
- Service locator
"""

from importlib import import_module
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Auto-discover and load all command buses
_bus_pkg_path = Path(__file__).parent / "bus"
if _bus_pkg_path.is_dir():
    for file in _bus_pkg_path.glob("*_command_bus.py"):
        module_name = f"src.gateway.bus.{file.stem}"
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

# Export common gateway components
from .bus.event_bus import EventBus, Event
from .bus.service_locator import ServiceLocator

__all__ = ['EventBus', 'Event', 'ServiceLocator']