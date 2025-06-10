"""Prompt service organism - manages prompt building operations"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from src.gateway import ServiceLocator, EventBus, Event
from ..atoms.prompt_formatter import PromptFormatter
from ..molecules.prompt_validator import PromptValidator

logger = logging.getLogger(__name__)


# Prompt events
class PromptBuiltEvent(Event):
    """Event emitted when prompt is built"""
    def __init__(self, mode: str, total_length: int):
        self.mode = mode
        self.total_length = total_length


class PromptValidationFailedEvent(Event):
    """Event emitted when prompt validation fails"""
    def __init__(self, errors: List[str]):
        self.errors = errors


class PromptService:
    """High-level prompt building service"""
    
    def __init__(self):
        self.formatter = PromptFormatter()
        self.validator = PromptValidator()
        
        self.system_prompt: str = ""
        self.user_prompt: str = ""
        self.current_mode: str = "enhanced"
        
        # Cache for file contents and attachments
        self._file_contents_cache: List[Dict[str, str]] = []
        self._attachments_cache: List[Dict[str, Any]] = []
    
    def set_system_prompt(self, content: str) -> bool:
        """Set system prompt content"""
        valid, error = self.validator.validate_system_prompt(content)
        if not valid:
            logger.error(f"Invalid system prompt: {error}")
            return False
        
        self.system_prompt = content
        logger.info(f"System prompt set: {len(content)} characters")
        return True
    
    def get_system_prompt(self) -> str:
        """Get current system prompt"""
        return self.system_prompt
    
    def set_user_prompt(self, content: str) -> bool:
        """Set user prompt content"""
        valid, error = self.validator.validate_user_prompt(content)
        if not valid:
            logger.error(f"Invalid user prompt: {error}")
            return False
        
        self.user_prompt = content
        logger.info(f"User prompt set: {len(content)} characters")
        return True
    
    def get_user_prompt(self) -> str:
        """Get current user prompt"""
        return self.user_prompt
    
    def set_mode(self, mode: str) -> bool:
        """Set prompt building mode"""
        if mode not in ["enhanced", "metaprompt"]:
            logger.error(f"Invalid mode: {mode}")
            return False
        
        self.current_mode = mode
        logger.info(f"Prompt mode set to: {mode}")
        return True
    
    def get_mode(self) -> str:
        """Get current prompt mode"""
        return self.current_mode
    
    async def build_prompt(
        self,
        include_files: bool = True,
        include_attachments: bool = True,
        include_system_prompt: bool = True,
        include_user_prompt: bool = True
    ) -> Tuple[bool, str, List[str]]:
        """Build the final prompt"""
        errors = []
        
        # Gather components
        system = self.system_prompt if include_system_prompt else None
        user = self.user_prompt if include_user_prompt else None
        
        # Get file contents if requested
        file_contents = []
        if include_files:
            file_contents = await self._get_file_contents()
        
        # Get attachments if requested
        attachments = []
        if include_attachments:
            attachments = await self._get_attachments()
        
        # Validate complete prompt
        valid, validation_errors = self.validator.validate_complete_prompt(
            system, user, file_contents, attachments
        )
        
        if not valid:
            errors.extend(validation_errors)
            EventBus.emit(PromptValidationFailedEvent(errors=errors))
            return False, "", errors
        
        # Build prompt based on mode
        if self.current_mode == "enhanced":
            prompt = self.formatter.build_enhanced_prompt(
                system_prompt=system,
                user_prompt=user,
                file_contents=file_contents,
                attachments=attachments
            )
        else:  # metaprompt mode
            # Build base content
            base_content = self.formatter.build_enhanced_prompt(
                system_prompt=None,  # Don't include system in base
                user_prompt=user,
                file_contents=file_contents,
                attachments=attachments
            )
            
            # Apply metaprompt template
            template = system or "{{CONTENT}}"  # Use system as template
            prompt = self.formatter.build_metaprompt(template, base_content)
        
        # Emit success event
        EventBus.emit(PromptBuiltEvent(mode=self.current_mode, total_length=len(prompt)))
        
        logger.info(f"Prompt built successfully: {len(prompt)} characters")
        return True, prompt, []
    
    async def get_prompt_preview(self, max_length: int = 1000) -> str:
        """Get a preview of the prompt"""
        success, prompt, errors = await self.build_prompt()
        
        if not success:
            return f"Error building prompt: {', '.join(errors)}"
        
        return self.formatter.truncate_prompt(prompt, max_length)
    
    def get_prompt_components(self) -> Dict[str, Any]:
        """Get all prompt components"""
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "mode": self.current_mode,
            "file_count": len(self._file_contents_cache),
            "attachment_count": len(self._attachments_cache)
        }
    
    def clear_prompts(self, clear_system: bool = False, clear_user: bool = True):
        """Clear prompt contents"""
        if clear_system:
            self.system_prompt = ""
            logger.info("System prompt cleared")
        
        if clear_user:
            self.user_prompt = ""
            logger.info("User prompt cleared")
    
    def get_prompt_stats(self) -> Dict[str, Any]:
        """Get statistics about the current prompt"""
        return self.validator.get_prompt_stats(
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt,
            file_contents=self._file_contents_cache,
            attachments=self._attachments_cache
        )
    
    async def _get_file_contents(self) -> List[Dict[str, str]]:
        """Get contents of checked files"""
        try:
            # Get file system service
            file_service = ServiceLocator.get("file_system")
            if not file_service:
                logger.warning("File system service not available")
                return []
            
            # Get checked files
            checked_files = file_service.get_checked_files()
            
            # Read file contents
            file_contents = []
            for file_path in checked_files:
                content = file_service.get_file_content(file_path)
                if content:
                    file_contents.append({
                        'path': file_path,
                        'content': content
                    })
            
            self._file_contents_cache = file_contents
            return file_contents
            
        except Exception as e:
            logger.error(f"Error getting file contents: {e}")
            return []
    
    async def _get_attachments(self) -> List[Dict[str, Any]]:
        """Get attachment information"""
        try:
            # Get attachment service when implemented
            # For now, return cached attachments
            return self._attachments_cache
            
        except Exception as e:
            logger.error(f"Error getting attachments: {e}")
            return []


# Import asyncio for preview method
import asyncio
