"""Token calculation feature command handlers"""
import logging
from src.gateway.bus.tokens_command_bus import TokensCommandBus
from src.gateway import EventBus, ServiceLocator
from .commands import (
    CalculateTokens, CalculatePromptTokens, CalculateFileTokens,
    CalculateMultimodalTokens, GetTokenUsage, GetTokenLimits,
    EstimateCost, GetModelInfo
)
from .organisms.token_service import TokenService

logger = logging.getLogger(__name__)


# Initialize token service and register with ServiceLocator
token_service = TokenService()
ServiceLocator.provide("tokens", token_service)


@TokensCommandBus.register(CalculateTokens)
async def handle_calculate_tokens(cmd: CalculateTokens):
    """Calculate tokens for text"""
    service = ServiceLocator.get("tokens")
    tokens = service.calculate_tokens(cmd.text, cmd.model)
    
    return {
        "text_length": len(cmd.text),
        "tokens": tokens,
        "model": cmd.model,
        "ratio": tokens / len(cmd.text) if cmd.text else 0
    }


@TokensCommandBus.register(CalculatePromptTokens)
async def handle_calculate_prompt_tokens(cmd: CalculatePromptTokens):
    """Calculate tokens for complete prompt"""
    service = ServiceLocator.get("tokens")
    result = await service.calculate_prompt_tokens(
        include_files=cmd.include_files,
        include_attachments=cmd.include_attachments,
        include_system_prompt=cmd.include_system_prompt,
        include_user_prompt=cmd.include_user_prompt,
        model=cmd.model
    )
    
    return result


@TokensCommandBus.register(CalculateFileTokens)
async def handle_calculate_file_tokens(cmd: CalculateFileTokens):
    """Calculate tokens for a file"""
    service = ServiceLocator.get("tokens")
    result = service.calculate_file_tokens(cmd.file_path, cmd.model)
    
    return result


@TokensCommandBus.register(CalculateMultimodalTokens)
async def handle_calculate_multimodal_tokens(cmd: CalculateMultimodalTokens):
    """Calculate tokens for multimodal content"""
    service = ServiceLocator.get("tokens")
    result = service.calculate_multimodal_tokens(
        text_content=cmd.text_content,
        image_count=cmd.image_count,
        video_count=cmd.video_count,
        audio_count=cmd.audio_count
    )
    
    return result


@TokensCommandBus.register(GetTokenUsage)
async def handle_get_token_usage(cmd: GetTokenUsage):
    """Get current token usage statistics"""
    service = ServiceLocator.get("tokens")
    stats = service.get_usage_stats()
    
    return stats


@TokensCommandBus.register(GetTokenLimits)
async def handle_get_token_limits(cmd: GetTokenLimits):
    """Get token limits for different models"""
    service = ServiceLocator.get("tokens")
    limits = service.get_token_limits()
    
    return {"limits": limits}


@TokensCommandBus.register(EstimateCost)
async def handle_estimate_cost(cmd: EstimateCost):
    """Estimate API cost based on tokens"""
    service = ServiceLocator.get("tokens")
    result = service.estimate_cost(
        prompt_tokens=cmd.prompt_tokens,
        completion_tokens=cmd.completion_tokens,
        model=cmd.model
    )
    
    return result


@TokensCommandBus.register(GetModelInfo)
async def handle_get_model_info(cmd: GetModelInfo):
    """Get model information including token limits"""
    service = ServiceLocator.get("tokens")
    info = service.get_model_info(cmd.model)
    
    return info
