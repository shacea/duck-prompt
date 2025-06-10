"""GPT tokenizer atom - calculates tokens for OpenAI models"""
import logging
from typing import Optional
import tiktoken

logger = logging.getLogger(__name__)


class GPTTokenizer:
    """Tokenizer for OpenAI GPT models"""
    
    def __init__(self):
        self._encodings = {}
        self._model_to_encoding = {
            "gpt-4": "cl100k_base",
            "gpt-4-32k": "cl100k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-4-turbo-preview": "cl100k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "gpt-3.5-turbo-16k": "cl100k_base",
            "text-davinci-003": "p50k_base",
            "text-davinci-002": "p50k_base",
        }
    
    def get_encoding(self, model: str) -> Optional[tiktoken.Encoding]:
        """Get encoding for a specific model"""
        encoding_name = self._model_to_encoding.get(model, "cl100k_base")
        
        if encoding_name not in self._encodings:
            try:
                self._encodings[encoding_name] = tiktoken.get_encoding(encoding_name)
                logger.debug(f"Loaded encoding {encoding_name} for model {model}")
            except Exception as e:
                logger.error(f"Failed to load encoding {encoding_name}: {e}")
                return None
        
        return self._encodings[encoding_name]
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text for a specific model"""
        if not text:
            return 0
        
        encoding = self.get_encoding(model)
        if not encoding:
            # Fallback to character-based estimation
            logger.warning(f"Using fallback token estimation for model {model}")
            return len(text) // 4
        
        try:
            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int, model: str = "gpt-4") -> str:
        """Truncate text to fit within token limit"""
        if not text:
            return text
        
        encoding = self.get_encoding(model)
        if not encoding:
            # Fallback to character-based truncation
            max_chars = max_tokens * 4
            return text[:max_chars]
        
        try:
            tokens = encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate tokens and decode back to text
            truncated_tokens = tokens[:max_tokens]
            return encoding.decode(truncated_tokens)
        except Exception as e:
            logger.error(f"Error truncating text: {e}")
            max_chars = max_tokens * 4
            return text[:max_chars]
    
    def get_model_limits(self, model: str) -> Dict[str, int]:
        """Get token limits for a model"""
        limits = {
            "gpt-4": {"context": 8192, "max_output": 4096},
            "gpt-4-32k": {"context": 32768, "max_output": 4096},
            "gpt-4-turbo": {"context": 128000, "max_output": 4096},
            "gpt-4-turbo-preview": {"context": 128000, "max_output": 4096},
            "gpt-3.5-turbo": {"context": 4096, "max_output": 4096},
            "gpt-3.5-turbo-16k": {"context": 16384, "max_output": 4096},
            "text-davinci-003": {"context": 4097, "max_output": 4000},
        }
        
        return limits.get(model, {"context": 4096, "max_output": 2048})


# Import for type hints
from typing import Dict