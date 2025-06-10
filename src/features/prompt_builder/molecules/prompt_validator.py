"""Prompt validator molecule - validates prompt components"""
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class PromptValidator:
    """Validates prompt components and final prompts"""
    
    def __init__(self):
        self.max_prompt_length = 1_000_000  # 1M characters
        self.max_file_size = 100_000  # 100K per file
        self.max_attachment_size = 10_000_000  # 10MB
        self.supported_image_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    
    def validate_system_prompt(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """Validate system prompt"""
        if not prompt:
            return True, None  # Empty is allowed
        
        if len(prompt) > self.max_prompt_length:
            return False, f"System prompt too long: {len(prompt)} characters (max: {self.max_prompt_length})"
        
        # Check for common issues
        if prompt.count('{{') != prompt.count('}}'):
            return False, "Unmatched template variables in system prompt"
        
        return True, None
    
    def validate_user_prompt(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """Validate user prompt"""
        if not prompt:
            return False, "User prompt cannot be empty"
        
        if len(prompt) > self.max_prompt_length:
            return False, f"User prompt too long: {len(prompt)} characters (max: {self.max_prompt_length})"
        
        return True, None
    
    def validate_file_content(self, file_info: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """Validate file content for inclusion"""
        file_path = file_info.get('path', 'Unknown')
        content = file_info.get('content', '')
        
        if not content:
            return False, f"File {file_path} has no content"
        
        if len(content) > self.max_file_size:
            return False, f"File {file_path} too large: {len(content)} characters (max: {self.max_file_size})"
        
        # Check if file appears to be binary
        if '\x00' in content:
            return False, f"File {file_path} appears to be binary"
        
        return True, None
    
    def validate_attachment(self, attachment: Dict[str, any]) -> Tuple[bool, Optional[str]]:
        """Validate attachment"""
        name = attachment.get('name', 'Unknown')
        file_type = attachment.get('type', 'Unknown')
        size = attachment.get('size', 0)
        
        if size > self.max_attachment_size:
            return False, f"Attachment {name} too large: {size} bytes (max: {self.max_attachment_size})"
        
        # Validate image attachments
        if file_type.startswith('image/'):
            if file_type not in self.supported_image_types:
                return False, f"Unsupported image type: {file_type}"
        
        return True, None
    
    def validate_complete_prompt(
        self,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        file_contents: Optional[List[Dict[str, str]]] = None,
        attachments: Optional[List[Dict[str, any]]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate complete prompt with all components"""
        errors = []
        total_size = 0
        
        # Validate system prompt
        if system_prompt:
            valid, error = self.validate_system_prompt(system_prompt)
            if not valid:
                errors.append(error)
            total_size += len(system_prompt)
        
        # Validate user prompt
        if user_prompt:
            valid, error = self.validate_user_prompt(user_prompt)
            if not valid:
                errors.append(error)
            total_size += len(user_prompt)
        
        # Validate file contents
        if file_contents:
            for file_info in file_contents:
                valid, error = self.validate_file_content(file_info)
                if not valid:
                    errors.append(error)
                else:
                    total_size += len(file_info.get('content', ''))
        
        # Validate attachments
        if attachments:
            for attachment in attachments:
                valid, error = self.validate_attachment(attachment)
                if not valid:
                    errors.append(error)
        
        # Check total size
        if total_size > self.max_prompt_length:
            errors.append(f"Total prompt size too large: {total_size} characters (max: {self.max_prompt_length})")
        
        return len(errors) == 0, errors
    
    def get_prompt_stats(
        self,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        file_contents: Optional[List[Dict[str, str]]] = None,
        attachments: Optional[List[Dict[str, any]]] = None
    ) -> Dict[str, any]:
        """Get statistics about the prompt"""
        stats = {
            'system_prompt_length': len(system_prompt) if system_prompt else 0,
            'user_prompt_length': len(user_prompt) if user_prompt else 0,
            'file_count': len(file_contents) if file_contents else 0,
            'attachment_count': len(attachments) if attachments else 0,
            'total_file_size': 0,
            'total_attachment_size': 0,
            'estimated_tokens': 0
        }
        
        if file_contents:
            stats['total_file_size'] = sum(len(f.get('content', '')) for f in file_contents)
        
        if attachments:
            stats['total_attachment_size'] = sum(a.get('size', 0) for a in attachments)
        
        # Estimate tokens (rough: 4 chars = 1 token)
        total_chars = (
            stats['system_prompt_length'] + 
            stats['user_prompt_length'] + 
            stats['total_file_size']
        )
        stats['estimated_tokens'] = total_chars // 4
        
        return stats