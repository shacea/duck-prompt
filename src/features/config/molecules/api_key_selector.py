"""API key selector molecule - manages API key selection logic"""
import logging
import random
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ApiKeySelector:
    """Manages selection of API keys with fallback and retry logic"""
    
    def __init__(self):
        self._user_selected_key_id: Optional[int] = None
        self._last_used_key: Optional[str] = None
        self._failed_keys: set = set()
    
    def set_user_selected_key(self, key_id: int) -> None:
        """Set user-selected API key preference"""
        self._user_selected_key_id = key_id
        logger.info(f"User selected Gemini key ID: {key_id}")
    
    def get_user_selected_key_id(self) -> Optional[int]:
        """Get user-selected key ID"""
        return self._user_selected_key_id
    
    def select_key(self, available_keys: List[Dict[str, Any]]) -> Optional[str]:
        """Select an API key based on user preference or randomly"""
        if not available_keys:
            logger.warning("No available API keys to select from")
            return None
        
        # Try user-selected key first
        if self._user_selected_key_id:
            for key_data in available_keys:
                if key_data.get('id') == self._user_selected_key_id:
                    selected_key = key_data.get('api_key')
                    if selected_key and selected_key not in self._failed_keys:
                        logger.info(f"Using user-selected Gemini key ID: {self._user_selected_key_id}")
                        return selected_key
            logger.warning(f"User-selected key ID {self._user_selected_key_id} not found or failed")
        
        # Filter out failed keys
        valid_keys = [
            k for k in available_keys 
            if k.get('api_key') and k.get('api_key') not in self._failed_keys
        ]
        
        if not valid_keys:
            logger.error("All API keys have failed")
            return None
        
        # Random selection from valid keys
        selected_key_data = random.choice(valid_keys)
        selected_key = selected_key_data.get('api_key')
        logger.info(f"Randomly selected Gemini key ID: {selected_key_data.get('id')}")
        
        return selected_key
    
    def mark_key_failed(self, key: str) -> None:
        """Mark a key as failed"""
        self._failed_keys.add(key)
        logger.warning(f"Marked API key as failed: {key[:10]}...")
    
    def mark_key_successful(self, key: str) -> None:
        """Mark a key as successful and remember it"""
        self._last_used_key = key
        self._failed_keys.discard(key)
        logger.info(f"API key used successfully: {key[:10]}...")
    
    def get_last_used_key(self) -> Optional[str]:
        """Get the last successfully used key"""
        return self._last_used_key
    
    def reset_failed_keys(self) -> None:
        """Reset the failed keys set"""
        self._failed_keys.clear()
        logger.info("Reset all failed API keys")