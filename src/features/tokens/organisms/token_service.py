"""Token service organism - manages token calculation operations"""
import logging
from typing import Dict, Any, Optional, Tuple
from src.gateway import ServiceLocator, EventBus, Event
from ..atoms.gpt_tokenizer import GPTTokenizer
from ..atoms.claude_tokenizer import ClaudeTokenizer
from ..atoms.gemini_tokenizer import GeminiTokenizer
from ..molecules.cost_calculator import CostCalculator

logger = logging.getLogger(__name__)


# Token calculation events
class TokensCalculatedEvent(Event):
    """Event emitted when tokens are calculated"""
    def __init__(self, model: str, token_count: int):
        self.model = model
        self.token_count = token_count


class CostCalculatedEvent(Event):
    """Event emitted when cost is calculated"""
    def __init__(self, model: str, total_cost: float):
        self.model = model
        self.total_cost = total_cost


class TokenService:
    """High-level token calculation service"""
    
    def __init__(self):
        self.gpt_tokenizer = GPTTokenizer()
        self.claude_tokenizer = ClaudeTokenizer()
        self.gemini_tokenizer = GeminiTokenizer()
        self.cost_calculator = CostCalculator()
        
        # Token usage tracking
        self.usage_stats = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_cost": 0.0,
            "by_model": {}
        }
        
        # API keys are initialized asynchronously when needed
    
    async def _initialize_api_keys(self):
        """Initialize API keys from config service"""
        try:
            config_service = ServiceLocator.get("config")
            if config_service and config_service.get_settings():
                # Get Claude API key
                claude_key = config_service.get_settings().anthropic_api_key
                if claude_key:
                    self.claude_tokenizer.set_api_key(claude_key)
                
                # Get Gemini API key
                gemini_key = await config_service.get_active_gemini_key()
                if gemini_key:
                    self.gemini_tokenizer.set_api_key(gemini_key)
                
        except Exception as e:
            logger.warning(f"Could not initialize API keys: {e}")
    
    async def _init_gemini_key(self, config_service):
        """Initialize Gemini API key asynchronously"""
        gemini_key = await config_service.get_active_gemini_key()
        if gemini_key:
            self.gemini_tokenizer.set_api_key(gemini_key)
    
    def calculate_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Calculate tokens for text using tiktoken regardless of model"""
        if not text:
            return 0
        
        # Always use tiktoken for token calculation
        # Map all models to their closest GPT equivalent for tokenization
        tiktoken_model = self._get_tiktoken_model(model)
        tokens = self.gpt_tokenizer.count_tokens(text, tiktoken_model)
        
        logger.debug(f"Calculated {tokens} tokens for {len(text)} characters using tiktoken model: {tiktoken_model}")
        
        # Emit event
        EventBus.emit(TokensCalculatedEvent(model=model, token_count=tokens))
        
        # Update usage stats
        self._update_usage_stats(model, tokens, 0)
        
        return tokens
    
    def _get_tiktoken_model(self, model: str) -> str:
        """Map any model to appropriate tiktoken model"""
        # Claude and Gemini models use similar tokenization to GPT-4
        if model.startswith("claude") or model.startswith("gemini"):
            return "gpt-4"
        elif model.startswith("gpt"):
            # Return the actual GPT model name
            return model
        else:
            # Default to GPT-4 tokenization
            return "gpt-4"
    
    async def calculate_prompt_tokens(
        self,
        include_files: bool = True,
        include_attachments: bool = True,
        include_system_prompt: bool = True,
        include_user_prompt: bool = True,
        model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """Calculate tokens for complete prompt"""
        try:
            # Get prompt builder service
            prompt_service = ServiceLocator.get("prompt_builder")
            if not prompt_service:
                logger.error("Prompt builder service not available")
                return {"error": "Service not available", "tokens": 0}
            
            # Build prompt
            success, prompt, errors = await prompt_service.build_prompt(
                include_files=include_files,
                include_attachments=include_attachments,
                include_system_prompt=include_system_prompt,
                include_user_prompt=include_user_prompt
            )
            
            if not success:
                return {"error": f"Failed to build prompt: {errors}", "tokens": 0}
            
            # Calculate tokens
            tokens = self.calculate_tokens(prompt, model)
            
            # Get breakdown
            components = prompt_service.get_prompt_components()
            
            return {
                "total_tokens": tokens,
                "model": model,
                "components": components,
                "prompt_length": len(prompt)
            }
            
        except Exception as e:
            logger.error(f"Error calculating prompt tokens: {e}")
            return {"error": str(e), "tokens": 0}
    
    def calculate_file_tokens(self, file_path: str, model: str = "gpt-4") -> Dict[str, Any]:
        """Calculate tokens for a file"""
        try:
            # Get file content
            file_service = ServiceLocator.get("file_system")
            if not file_service:
                return {"error": "File system service not available", "tokens": 0}
            
            content = file_service.get_file_content(file_path)
            if not content:
                return {"error": "Could not read file", "tokens": 0}
            
            # Calculate tokens
            tokens = self.calculate_tokens(content, model)
            
            return {
                "file": file_path,
                "tokens": tokens,
                "model": model,
                "file_size": len(content)
            }
            
        except Exception as e:
            logger.error(f"Error calculating file tokens: {e}")
            return {"error": str(e), "tokens": 0}
    
    def calculate_multimodal_tokens(
        self,
        text_content: str,
        image_count: int = 0,
        video_count: int = 0,
        audio_count: int = 0
    ) -> Dict[str, Any]:
        """Calculate tokens for multimodal content (Gemini)"""
        # Text tokens
        text_tokens = self.gemini_tokenizer.count_tokens(text_content, "gemini-pro-vision")
        
        # Image tokens (258 per image)
        image_tokens = image_count * 258
        
        # Video tokens (258 per second at 1 FPS)
        video_tokens = video_count * 258  # Assuming 1 second per video for simplicity
        
        # Audio not yet supported
        audio_tokens = 0
        
        total_tokens = text_tokens + image_tokens + video_tokens + audio_tokens
        
        return {
            "text_tokens": text_tokens,
            "image_tokens": image_tokens,
            "video_tokens": video_tokens,
            "audio_tokens": audio_tokens,
            "total_tokens": total_tokens,
            "breakdown": {
                "images": image_count,
                "videos": video_count,
                "audio": audio_count
            }
        }
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4",
        image_count: int = 0
    ) -> Dict[str, Any]:
        """Estimate API cost based on tokens"""
        cost_data = self.cost_calculator.calculate_cost(
            prompt_tokens,
            completion_tokens,
            model,
            image_count
        )
        
        # Convert Decimal to float for JSON serialization
        result = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": model,
            "costs": {
                "prompt_cost": float(cost_data["prompt_cost"]),
                "completion_cost": float(cost_data["completion_cost"]),
                "image_cost": float(cost_data["image_cost"]),
                "total_cost": float(cost_data["total_cost"]),
                "currency": cost_data["currency"]
            }
        }
        
        # Emit event
        EventBus.emit(CostCalculatedEvent(
            model=model,
            total_cost=result["costs"]["total_cost"]
        ))
        
        # Update usage stats
        self._update_usage_stats(model, prompt_tokens, completion_tokens)
        self.usage_stats["total_cost"] += result["costs"]["total_cost"]
        
        return result
    
    def get_token_limits(self) -> Dict[str, Dict[str, Any]]:
        """Get token limits for all models"""
        limits = {}
        
        # GPT models
        for model in ["gpt-4", "gpt-4-32k", "gpt-4-turbo", "gpt-3.5-turbo"]:
            limits[model] = self.gpt_tokenizer.get_model_limits(model)
        
        # Claude models
        for model in ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]:
            limits[model] = self.claude_tokenizer.get_model_limits(model)
        
        # Gemini models
        for model in ["gemini-pro", "gemini-pro-vision", "gemini-pro-1.5"]:
            limits[model] = self.gemini_tokenizer.get_model_limits(model)
        
        return limits
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        # Get limits
        if model.startswith("gpt"):
            limits = self.gpt_tokenizer.get_model_limits(model)
        elif model.startswith("claude"):
            limits = self.claude_tokenizer.get_model_limits(model)
        elif model.startswith("gemini"):
            limits = self.gemini_tokenizer.get_model_limits(model)
        else:
            limits = {"context": 4096, "max_output": 2048}
        
        # Get pricing
        pricing = self.cost_calculator.get_model_pricing(model)
        
        return {
            "model": model,
            "limits": limits,
            "pricing": {k: float(v) for k, v in pricing.items()} if pricing else None,
            "provider": self._get_provider(model)
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current token usage statistics"""
        return self.usage_stats.copy()
    
    def _get_provider(self, model: str) -> str:
        """Get provider name for a model"""
        if model.startswith("gpt") or model.startswith("text-"):
            return "OpenAI"
        elif model.startswith("claude"):
            return "Anthropic"
        elif model.startswith("gemini"):
            return "Google"
        else:
            return "Unknown"
    
    def _update_usage_stats(self, model: str, prompt_tokens: int, completion_tokens: int):
        """Update usage statistics"""
        self.usage_stats["total_prompt_tokens"] += prompt_tokens
        self.usage_stats["total_completion_tokens"] += completion_tokens
        
        if model not in self.usage_stats["by_model"]:
            self.usage_stats["by_model"][model] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "requests": 0
            }
        
        self.usage_stats["by_model"][model]["prompt_tokens"] += prompt_tokens
        self.usage_stats["by_model"][model]["completion_tokens"] += completion_tokens
        self.usage_stats["by_model"][model]["requests"] += 1


# Import asyncio for async initialization
import asyncio
