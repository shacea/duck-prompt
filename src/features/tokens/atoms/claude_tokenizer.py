"""Claude tokenizer atom - calculates tokens for Anthropic models"""
import logging
import httpx
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class ClaudeTokenizer:
    """Tokenizer for Anthropic Claude models using API"""
    
    def __init__(self):
        self.api_endpoint = "https://api.anthropic.com/v1/tokenize"
        self._api_key: Optional[str] = None
        self._client = httpx.Client(timeout=30.0)
    
    def set_api_key(self, api_key: str):
        """Set API key for Claude tokenization"""
        self._api_key = api_key
    
    def count_tokens(self, text: str, model: str = "claude-3") -> int:
        """Count tokens in text using Claude API"""
        if not text:
            return 0
        
        # If no API key, use fallback estimation
        if not self._api_key:
            logger.warning("No Claude API key available, using fallback estimation")
            return self._estimate_tokens(text)
        
        try:
            response = self._client.post(
                self.api_endpoint,
                headers={
                    "X-API-Key": self._api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "text": text,
                    "model": model
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("token_count", 0)
            else:
                logger.error(f"Claude tokenization API error: {response.status_code}")
                return self._estimate_tokens(text)
                
        except Exception as e:
            logger.error(f"Error calling Claude tokenization API: {e}")
            return self._estimate_tokens(text)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens when API is not available"""
        # Claude uses roughly similar tokenization to GPT
        # Estimate ~4 characters per token
        return len(text) // 4
    
    def get_model_limits(self, model: str) -> Dict[str, int]:
        """Get token limits for Claude models"""
        limits = {
            "claude-3-opus": {"context": 200000, "max_output": 4096},
            "claude-3-sonnet": {"context": 200000, "max_output": 4096},
            "claude-3-haiku": {"context": 200000, "max_output": 4096},
            "claude-2.1": {"context": 200000, "max_output": 4096},
            "claude-2": {"context": 100000, "max_output": 4096},
            "claude-instant": {"context": 100000, "max_output": 4096},
        }
        
        return limits.get(model, {"context": 100000, "max_output": 4096})
    
    def truncate_to_tokens(self, text: str, max_tokens: int, model: str = "claude-3") -> str:
        """Truncate text to fit within token limit"""
        # Since we can't tokenize without API, use character-based approximation
        estimated_chars = max_tokens * 4
        if len(text) <= estimated_chars:
            return text
        
        return text[:estimated_chars]
    
    def __del__(self):
        """Cleanup HTTP client"""
        if hasattr(self, '_client'):
            self._client.close()