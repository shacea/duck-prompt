"""Gemini tokenizer atom - calculates tokens for Google models"""
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiTokenizer:
    """Tokenizer for Google Gemini models"""
    
    def __init__(self):
        self._model_cache = {}
        self._api_key: Optional[str] = None
    
    def set_api_key(self, api_key: str):
        """Set API key for Gemini"""
        self._api_key = api_key
        genai.configure(api_key=api_key)
    
    def count_tokens(self, text: str, model: str = "gemini-pro") -> int:
        """Count tokens in text using Gemini API"""
        if not text:
            return 0
        
        if not self._api_key:
            logger.warning("No Gemini API key available, using fallback estimation")
            return self._estimate_tokens(text)
        
        try:
            # Get or create model instance
            if model not in self._model_cache:
                self._model_cache[model] = genai.GenerativeModel(model)
            
            model_instance = self._model_cache[model]
            
            # Count tokens
            token_count = model_instance.count_tokens(text)
            return token_count.total_tokens
            
        except Exception as e:
            logger.error(f"Error counting Gemini tokens: {e}")
            return self._estimate_tokens(text)
    
    def count_multimodal_tokens(
        self,
        text: str,
        images: Optional[List[Any]] = None,
        model: str = "gemini-pro-vision"
    ) -> Dict[str, int]:
        """Count tokens for multimodal content"""
        if not self._api_key:
            logger.warning("No Gemini API key available, using fallback estimation")
            text_tokens = self._estimate_tokens(text)
            image_tokens = len(images) * 258 if images else 0  # ~258 tokens per image
            return {
                "text_tokens": text_tokens,
                "image_tokens": image_tokens,
                "total_tokens": text_tokens + image_tokens
            }
        
        try:
            # Get or create model instance
            if model not in self._model_cache:
                self._model_cache[model] = genai.GenerativeModel(model)
            
            model_instance = self._model_cache[model]
            
            # Build content list
            content = [text]
            if images:
                content.extend(images)
            
            # Count tokens
            token_count = model_instance.count_tokens(content)
            
            # Estimate breakdown (Gemini doesn't provide detailed breakdown)
            text_tokens = self._estimate_tokens(text)
            total = token_count.total_tokens
            image_tokens = max(0, total - text_tokens)
            
            return {
                "text_tokens": text_tokens,
                "image_tokens": image_tokens,
                "total_tokens": total
            }
            
        except Exception as e:
            logger.error(f"Error counting multimodal tokens: {e}")
            text_tokens = self._estimate_tokens(text)
            image_tokens = len(images) * 258 if images else 0
            return {
                "text_tokens": text_tokens,
                "image_tokens": image_tokens,
                "total_tokens": text_tokens + image_tokens
            }
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens when API is not available"""
        # Gemini uses roughly similar tokenization
        # Estimate ~4 characters per token
        return len(text) // 4
    
    def get_model_limits(self, model: str) -> Dict[str, Any]:
        """Get token limits for Gemini models"""
        limits = {
            "gemini-pro": {
                "context": 32768,
                "max_output": 8192,
                "supports_images": False,
                "supports_video": False
            },
            "gemini-pro-vision": {
                "context": 16384,
                "max_output": 2048,
                "supports_images": True,
                "supports_video": True,
                "max_images": 16,
                "max_video_length": 1  # minutes
            },
            "gemini-pro-1.5": {
                "context": 1048576,  # 1M tokens
                "max_output": 8192,
                "supports_images": True,
                "supports_video": True
            }
        }
        
        return limits.get(model, {
            "context": 32768,
            "max_output": 2048,
            "supports_images": False,
            "supports_video": False
        })
    
    def estimate_image_tokens(self, image_size: tuple[int, int]) -> int:
        """Estimate tokens for an image based on size"""
        # Gemini uses approximately 258 tokens per image
        # regardless of size (as of current models)
        return 258
    
    def estimate_video_tokens(self, duration_seconds: int, fps: int = 1) -> int:
        """Estimate tokens for video content"""
        # Gemini samples video at 1 FPS by default
        # Each frame counts as an image (~258 tokens)
        frames = duration_seconds * fps
        return frames * 258


# Import for type hints
from typing import List