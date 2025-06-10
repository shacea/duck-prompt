from src.gateway.bus._base import Command

class ApplyDmpPatch(Command):
    """Command to apply a DMP patch to the workspace."""
    patch_text: str
