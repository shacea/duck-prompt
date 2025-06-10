"""Shared validators atom - common validation utilities"""
import re
from typing import Optional
from pathlib import Path


class Validators:
    """Common validation utilities"""
    
    @staticmethod
    def is_valid_api_key(api_key: str, service: str) -> bool:
        """Validate API key format for different services"""
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Remove whitespace
        api_key = api_key.strip()
        
        if service == 'google' or service == 'gemini':
            # Gemini API keys typically start with 'AIza' and are 39 characters
            return len(api_key) == 39 and api_key.startswith('AIza')
        
        elif service == 'anthropic' or service == 'claude':
            # Anthropic keys start with 'sk-ant-' 
            return api_key.startswith('sk-ant-') and len(api_key) > 20
        
        elif service == 'openai':
            # OpenAI keys start with 'sk-'
            return api_key.startswith('sk-') and len(api_key) > 20
        
        return False
    
    @staticmethod
    def is_valid_file_path(path: str) -> bool:
        """Check if a path is valid"""
        try:
            Path(path)
            return True
        except Exception:
            return False
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Basic URL validation"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename by removing invalid characters"""
        # Remove invalid characters for filenames
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Ensure it's not empty
        if not filename:
            filename = 'unnamed'
        
        return filename
    
    @staticmethod
    def validate_json_schema(data: dict, schema: dict) -> tuple[bool, Optional[str]]:
        """Basic JSON schema validation (simplified)"""
        # This is a placeholder for more complex validation
        # In production, you'd use jsonschema library
        try:
            # Basic type checking
            for key, expected_type in schema.get('properties', {}).items():
                if key in schema.get('required', []) and key not in data:
                    return False, f"Missing required field: {key}"
                
                if key in data:
                    # Simplified type checking
                    value = data[key]
                    if 'type' in expected_type:
                        if expected_type['type'] == 'string' and not isinstance(value, str):
                            return False, f"Field {key} must be a string"
                        elif expected_type['type'] == 'number' and not isinstance(value, (int, float)):
                            return False, f"Field {key} must be a number"
                        elif expected_type['type'] == 'boolean' and not isinstance(value, bool):
                            return False, f"Field {key} must be a boolean"
                        elif expected_type['type'] == 'array' and not isinstance(value, list):
                            return False, f"Field {key} must be an array"
                        elif expected_type['type'] == 'object' and not isinstance(value, dict):
                            return False, f"Field {key} must be an object"
            
            return True, None
            
        except Exception as e:
            return False, str(e)