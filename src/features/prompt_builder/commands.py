"""Prompt builder feature commands"""
from typing import Optional, List, Dict, Any
from src.gateway.bus._base import Command


class SetSystemPrompt(Command):
    """Command to set system prompt content"""
    content: str


class GetSystemPrompt(Command):
    """Command to get current system prompt"""
    pass


class SetUserPrompt(Command):
    """Command to set user prompt content"""
    content: str


class GetUserPrompt(Command):
    """Command to get current user prompt"""
    pass


class BuildPrompt(Command):
    """Command to build the final prompt"""
    include_files: bool = True
    include_attachments: bool = True
    include_system_prompt: bool = True
    include_user_prompt: bool = True
    mode: str = "enhanced"  # "enhanced" or "metaprompt"
    files_to_include: Optional[List[str]] = None # Specify files to include
    directory_tree: Optional[str] = None # Override for directory tree


class GetPromptComponents(Command):
    """Command to get all prompt components"""
    pass


class ValidatePrompt(Command):
    """Command to validate prompt components"""
    pass


class GetPromptPreview(Command):
    """Command to get a preview of the built prompt"""
    max_length: int = 1000


class ClearPrompts(Command):
    """Command to clear all prompts"""
    clear_system: bool = False
    clear_user: bool = True


class SetPromptMode(Command):
    """Command to set prompt building mode"""
    mode: str  # "enhanced" or "metaprompt"


class GetPromptMode(Command):
    """Command to get current prompt mode"""
    pass


class ApplyTemplate(Command):
    """Command to apply a template to prompts"""
    template_name: str
    target: str  # "system" or "user"
