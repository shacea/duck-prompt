"""Token calculation feature commands"""
from typing import Optional, List, Dict, Any
from src.gateway.bus._base import Command


class CalculateTokens(Command):
    """Command to calculate tokens for text"""
    text: str
    model: str = "gpt-4"  # gpt-4, claude, gemini


class CalculatePromptTokens(Command):
    """Command to calculate tokens for complete prompt"""
    include_files: bool = True
    include_attachments: bool = True
    include_system_prompt: bool = True
    include_user_prompt: bool = True
    model: str = "gpt-4"


class CalculateFileTokens(Command):
    """Command to calculate tokens for a file"""
    file_path: str
    model: str = "gpt-4"


class CalculateMultimodalTokens(Command):
    """Command to calculate tokens for multimodal content (Gemini)"""
    text_content: str
    image_count: int = 0
    video_count: int = 0
    audio_count: int = 0


class GetTokenUsage(Command):
    """Command to get current token usage statistics"""
    pass


class GetTokenLimits(Command):
    """Command to get token limits for different models"""
    pass


class EstimateCost(Command):
    """Command to estimate API cost based on tokens"""
    prompt_tokens: int
    completion_tokens: int
    model: str = "gpt-4"


class GetModelInfo(Command):
    """Command to get model information including token limits"""
    model: str