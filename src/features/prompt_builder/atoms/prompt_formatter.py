"""Prompt formatter atom - formats prompt components"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PromptFormatter:
    """Formats prompt components into final prompt"""
    
    def __init__(self):
        self.file_separator = "\n\n" + "="*60 + "\n\n"
        self.section_separator = "\n\n"
    
    def format_file_content(self, file_path: str, content: str) -> str:
        """Format a single file's content for inclusion in prompt"""
        header = f"File: {file_path}"
        separator = "-" * len(header)
        
        return f"{header}\n{separator}\n{content}"
    
    def format_attachment(self, attachment_info: Dict[str, Any]) -> str:
        """Format an attachment for inclusion in prompt"""
        name = attachment_info.get('name', 'Unnamed')
        file_type = attachment_info.get('type', 'Unknown')
        size = attachment_info.get('size', 0)
        
        header = f"Attachment: {name} (Type: {file_type}, Size: {size} bytes)"
        
        # For image attachments, just include metadata
        if file_type.startswith('image/'):
            return f"{header}\n[Image content will be sent as multimodal input]"
        
        # For text attachments, include content if available
        content = attachment_info.get('content', '')
        if content:
            return f"{header}\n{content}"
        
        return header
    
    def build_enhanced_prompt(
        self,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        file_contents: Optional[List[Dict[str, str]]] = None,
        directory_tree: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build an enhanced prompt with all components in a specific order."""
        sections = []
        
        # 1. System Prompt
        if system_prompt:
            sections.append(f"=== SYSTEM PROMPT ===\n{system_prompt}")
        
        # 2. User Prompt
        if user_prompt:
            sections.append(f"=== USER PROMPT ===\n{user_prompt}")
            
        # 3. File Contents
        if file_contents:
            file_section = "=== FILE CONTENTS ===\n"
            formatted_files = [
                self.format_file_content(f.get('path', 'Unknown'), f.get('content', ''))
                for f in file_contents
            ]
            file_section += self.file_separator.join(formatted_files)
            sections.append(file_section)
        
        # 4. Directory Tree
        if directory_tree:
            sections.append(f"=== DIRECTORY TREE ===\n{directory_tree}")
            
        # 5. Attachments (last)
        if attachments:
            attachment_section = "=== ATTACHMENTS ===\n"
            formatted_attachments = [self.format_attachment(a) for a in attachments]
            attachment_section += self.section_separator.join(formatted_attachments)
            sections.append(attachment_section)
        
        # Join all sections
        final_prompt = self.section_separator.join(sections)
        
        logger.debug(f"Built enhanced prompt with {len(sections)} sections")
        return final_prompt
    
    def build_metaprompt(
        self,
        template: str,
        content: str,
        variables: Optional[Dict[str, str]] = None
    ) -> str:
        """Build a metaprompt using a template"""
        # Replace variables in template
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                template = template.replace(placeholder, value)
        
        # Replace main content placeholder
        template = template.replace("{{CONTENT}}", content)
        
        logger.debug("Built metaprompt from template")
        return template
    
    def truncate_prompt(self, prompt: str, max_length: int) -> str:
        """Truncate prompt to maximum length"""
        if len(prompt) <= max_length:
            return prompt
        
        # Truncate and add ellipsis
        truncated = prompt[:max_length - 3] + "..."
        logger.warning(f"Prompt truncated from {len(prompt)} to {max_length} characters")
        
        return truncated
    
    def estimate_token_count(self, text: str) -> int:
        """Rough estimation of token count"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
