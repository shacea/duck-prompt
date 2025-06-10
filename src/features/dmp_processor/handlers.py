import logging
from src.gateway.bus.dmp_processor_command_bus import DmpProcessorCommandBus
from src.gateway import ServiceLocator, Event
from .commands import ApplyDmpPatch
from .organisms.dmp_service import DmpService

logger = logging.getLogger(__name__)

class DmpPatchAppliedEvent(Event):
    """Event emitted after a DMP patch has been applied."""
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message

# Initialize the service and register it with the ServiceLocator
dmp_service = DmpService()
ServiceLocator.provide("dmp_processor", dmp_service)

@DmpProcessorCommandBus.register(ApplyDmpPatch)
async def handle_apply_dmp_patch(cmd: ApplyDmpPatch):
    """Handles the command to apply a DMP patch."""
    service = ServiceLocator.get("dmp_processor")
    success, message = await service.apply_dmp_patch(cmd.patch_text)
    
    # Emit an event to notify other parts of the system if needed
    # For now, the direct return value is sufficient for the controller.
    # EventBus.emit(DmpPatchAppliedEvent(success=success, message=message))
    
    return {"success": success, "message": message}
