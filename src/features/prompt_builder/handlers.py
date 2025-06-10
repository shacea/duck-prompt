"""Prompt builder feature command handlers"""
import logging
from src.gateway.bus.prompt_builder_command_bus import PromptBuilderCommandBus
from src.gateway import EventBus, ServiceLocator
from .commands import (
    SetSystemPrompt, GetSystemPrompt, SetUserPrompt, GetUserPrompt,
    BuildPrompt, GetPromptComponents, ValidatePrompt, GetPromptPreview,
    ClearPrompts, SetPromptMode, GetPromptMode, ApplyTemplate
)
from .organisms.prompt_service import PromptService

logger = logging.getLogger(__name__)


# Initialize prompt service and register with ServiceLocator
prompt_service = PromptService()
ServiceLocator.provide("prompt_builder", prompt_service)


@PromptBuilderCommandBus.register(SetSystemPrompt)
async def handle_set_system_prompt(cmd: SetSystemPrompt):
    """Set system prompt content"""
    service = ServiceLocator.get("prompt_builder")
    success = service.set_system_prompt(cmd.content)
    return {"success": success, "length": len(cmd.content)}


@PromptBuilderCommandBus.register(GetSystemPrompt)
async def handle_get_system_prompt(cmd: GetSystemPrompt):
    """Get current system prompt"""
    service = ServiceLocator.get("prompt_builder")
    content = service.get_system_prompt()
    return {"content": content, "length": len(content)}


@PromptBuilderCommandBus.register(SetUserPrompt)
async def handle_set_user_prompt(cmd: SetUserPrompt):
    """Set user prompt content"""
    service = ServiceLocator.get("prompt_builder")
    success = service.set_user_prompt(cmd.content)
    return {"success": success, "length": len(cmd.content)}


@PromptBuilderCommandBus.register(GetUserPrompt)
async def handle_get_user_prompt(cmd: GetUserPrompt):
    """Get current user prompt"""
    service = ServiceLocator.get("prompt_builder")
    content = service.get_user_prompt()
    return {"content": content, "length": len(content)}


@PromptBuilderCommandBus.register(BuildPrompt)
async def handle_build_prompt(cmd: BuildPrompt):
    """Build the final prompt"""
    service = ServiceLocator.get("prompt_builder")
    
    # Set mode if different
    if cmd.mode != service.get_mode():
        service.set_mode(cmd.mode)
    
    success, prompt, errors = await service.build_prompt(
        include_files=cmd.include_files,
        include_attachments=cmd.include_attachments,
        include_system_prompt=cmd.include_system_prompt,
        include_user_prompt=cmd.include_user_prompt,
        files_to_include=cmd.files_to_include,
        directory_tree=cmd.directory_tree
    )
    
    return {
        "success": success,
        "prompt": prompt if success else None,
        "errors": errors,
        "length": len(prompt) if success else 0
    }


@PromptBuilderCommandBus.register(GetPromptComponents)
async def handle_get_prompt_components(cmd: GetPromptComponents):
    """Get all prompt components"""
    service = ServiceLocator.get("prompt_builder")
    components = service.get_prompt_components()
    return components


@PromptBuilderCommandBus.register(ValidatePrompt)
async def handle_validate_prompt(cmd: ValidatePrompt):
    """Validate prompt components"""
    service = ServiceLocator.get("prompt_builder")
    
    # Build prompt to validate
    success, _, errors = await service.build_prompt()
    
    # Get stats
    stats = service.get_prompt_stats()
    
    return {
        "valid": success,
        "errors": errors,
        "stats": stats
    }


@PromptBuilderCommandBus.register(GetPromptPreview)
async def handle_get_prompt_preview(cmd: GetPromptPreview):
    """Get a preview of the built prompt"""
    service = ServiceLocator.get("prompt_builder")
    preview = await service.get_prompt_preview(cmd.max_length)
    
    return {
        "preview": preview,
        "truncated": len(preview) >= cmd.max_length
    }


@PromptBuilderCommandBus.register(ClearPrompts)
async def handle_clear_prompts(cmd: ClearPrompts):
    """Clear prompt contents"""
    service = ServiceLocator.get("prompt_builder")
    service.clear_prompts(
        clear_system=cmd.clear_system,
        clear_user=cmd.clear_user
    )
    
    return {
        "cleared_system": cmd.clear_system,
        "cleared_user": cmd.clear_user
    }


@PromptBuilderCommandBus.register(SetPromptMode)
async def handle_set_prompt_mode(cmd: SetPromptMode):
    """Set prompt building mode"""
    service = ServiceLocator.get("prompt_builder")
    success = service.set_mode(cmd.mode)
    
    return {
        "success": success,
        "mode": cmd.mode if success else service.get_mode()
    }


@PromptBuilderCommandBus.register(GetPromptMode)
async def handle_get_prompt_mode(cmd: GetPromptMode):
    """Get current prompt mode"""
    service = ServiceLocator.get("prompt_builder")
    mode = service.get_mode()
    return {"mode": mode}


@PromptBuilderCommandBus.register(ApplyTemplate)
async def handle_apply_template(cmd: ApplyTemplate):
    """Apply a template to prompts"""
    # This would integrate with the templates feature
    # For now, return a placeholder response
    logger.warning("Template application not yet implemented")
    
    return {
        "success": False,
        "error": "Template feature not yet implemented",
        "template": cmd.template_name,
        "target": cmd.target
    }
