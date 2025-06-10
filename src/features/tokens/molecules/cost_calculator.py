"""Cost calculator molecule - calculates API costs based on tokens"""
import logging
from typing import Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculates API costs for different models"""
    
    def __init__(self):
        # Prices per 1K tokens (in USD)
        self.pricing = {
            # OpenAI GPT-4
            "gpt-4": {
                "prompt": Decimal("0.03"),
                "completion": Decimal("0.06")
            },
            "gpt-4-32k": {
                "prompt": Decimal("0.06"),
                "completion": Decimal("0.12")
            },
            "gpt-4-turbo": {
                "prompt": Decimal("0.01"),
                "completion": Decimal("0.03")
            },
            "gpt-4-turbo-preview": {
                "prompt": Decimal("0.01"),
                "completion": Decimal("0.03")
            },
            # OpenAI GPT-3.5
            "gpt-3.5-turbo": {
                "prompt": Decimal("0.0005"),
                "completion": Decimal("0.0015")
            },
            "gpt-3.5-turbo-16k": {
                "prompt": Decimal("0.001"),
                "completion": Decimal("0.002")
            },
            # Anthropic Claude
            "claude-3-opus": {
                "prompt": Decimal("0.015"),
                "completion": Decimal("0.075")
            },
            "claude-3-sonnet": {
                "prompt": Decimal("0.003"),
                "completion": Decimal("0.015")
            },
            "claude-3-haiku": {
                "prompt": Decimal("0.00025"),
                "completion": Decimal("0.00125")
            },
            # Google Gemini
            "gemini-pro": {
                "prompt": Decimal("0.0005"),
                "completion": Decimal("0.0015")
            },
            "gemini-pro-vision": {
                "prompt": Decimal("0.0005"),
                "completion": Decimal("0.0015"),
                "image": Decimal("0.002")  # per image
            },
            "gemini-pro-1.5": {
                "prompt": Decimal("0.00125"),
                "completion": Decimal("0.005")
            }
        }
    
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        image_count: int = 0
    ) -> Dict[str, Decimal]:
        """Calculate cost for API usage"""
        if model not in self.pricing:
            logger.warning(f"Unknown model {model}, using default pricing")
            pricing = {
                "prompt": Decimal("0.001"),
                "completion": Decimal("0.002")
            }
        else:
            pricing = self.pricing[model]
        
        # Calculate text costs
        prompt_cost = (Decimal(prompt_tokens) / 1000) * pricing["prompt"]
        completion_cost = (Decimal(completion_tokens) / 1000) * pricing["completion"]
        
        # Calculate image costs if applicable
        image_cost = Decimal("0")
        if image_count > 0 and "image" in pricing:
            image_cost = Decimal(image_count) * pricing["image"]
        
        total_cost = prompt_cost + completion_cost + image_cost
        
        return {
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "image_cost": image_cost,
            "total_cost": total_cost,
            "currency": "USD"
        }
    
    def estimate_monthly_cost(
        self,
        daily_requests: int,
        avg_prompt_tokens: int,
        avg_completion_tokens: int,
        model: str,
        avg_images_per_request: int = 0
    ) -> Dict[str, Decimal]:
        """Estimate monthly API costs"""
        # Calculate daily cost
        daily_cost = self.calculate_cost(
            prompt_tokens=daily_requests * avg_prompt_tokens,
            completion_tokens=daily_requests * avg_completion_tokens,
            model=model,
            image_count=daily_requests * avg_images_per_request
        )
        
        # Multiply by 30 for monthly estimate
        monthly_cost = {}
        for key, value in daily_cost.items():
            if key == "currency":
                monthly_cost[key] = value
            else:
                monthly_cost[key] = value * 30
        
        return monthly_cost
    
    def get_model_pricing(self, model: str) -> Optional[Dict[str, Decimal]]:
        """Get pricing information for a model"""
        return self.pricing.get(model)
    
    def compare_models(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        models: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Decimal]]:
        """Compare costs across different models"""
        if models is None:
            models = list(self.pricing.keys())
        
        comparison = {}
        for model in models:
            if model in self.pricing:
                cost = self.calculate_cost(prompt_tokens, completion_tokens, model)
                comparison[model] = cost
        
        # Sort by total cost
        sorted_comparison = dict(
            sorted(comparison.items(), key=lambda x: x[1]["total_cost"])
        )
        
        return sorted_comparison
    
    def format_cost(self, cost: Decimal, include_currency: bool = True) -> str:
        """Format cost for display"""
        formatted = f"${cost:.4f}"
        if include_currency:
            formatted += " USD"
        return formatted


# Import for type hints
from typing import List