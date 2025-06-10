"""Configuration management molecule"""
import logging
from typing import Optional, Dict, Any, List
from ..atoms.query_executor import QueryExecutor

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration in the database"""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor

    def update_profile_config(self, profile_name: str, config_data: Dict[str, Any]) -> int:
        """Inserts or updates a profile in the application_config table."""
        logger.info(f"Attempting to insert/update application configuration for profile '{profile_name}'...")

        # Prepare data, handling potential missing keys and types
        allowed_extensions = list(config_data.get('allowed_extensions', []))
        excluded_dirs = list(config_data.get('excluded_dirs', []))
        default_ignore_list = list(config_data.get('default_ignore_list', []))
        gemini_available_models = list(config_data.get('gemini_available_models', []))
        claude_available_models = list(config_data.get('claude_available_models', []))
        gpt_available_models = list(config_data.get('gpt_available_models', []))

        gemini_enable_thinking = bool(config_data.get('gemini_enable_thinking', True))
        gemini_enable_search = bool(config_data.get('gemini_enable_search', True))

        try:
            gemini_temperature = float(config_data.get('gemini_temperature', 0.0))
        except (ValueError, TypeError):
            gemini_temperature = 0.0
        try:
            gemini_thinking_budget = int(config_data.get('gemini_thinking_budget', 24576))
        except (ValueError, TypeError):
            gemini_thinking_budget = 24576

        sql = """
            INSERT INTO application_config (
                profile_name, default_system_prompt, allowed_extensions, excluded_dirs,
                default_ignore_list, gemini_default_model, claude_default_model, gpt_default_model,
                gemini_available_models, claude_available_models, gpt_available_models,
                gemini_temperature, gemini_enable_thinking, gemini_thinking_budget, gemini_enable_search
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (profile_name) DO UPDATE SET
                default_system_prompt = EXCLUDED.default_system_prompt,
                allowed_extensions = EXCLUDED.allowed_extensions,
                excluded_dirs = EXCLUDED.excluded_dirs,
                default_ignore_list = EXCLUDED.default_ignore_list,
                gemini_default_model = EXCLUDED.gemini_default_model,
                claude_default_model = EXCLUDED.claude_default_model,
                gpt_default_model = EXCLUDED.gpt_default_model,
                gemini_available_models = EXCLUDED.gemini_available_models,
                claude_available_models = EXCLUDED.claude_available_models,
                gpt_available_models = EXCLUDED.gpt_available_models,
                gemini_temperature = EXCLUDED.gemini_temperature,
                gemini_enable_thinking = EXCLUDED.gemini_enable_thinking,
                gemini_thinking_budget = EXCLUDED.gemini_thinking_budget,
                gemini_enable_search = EXCLUDED.gemini_enable_search,
                updated_at = NOW();
        """
        params = (
            profile_name,
            config_data.get('default_system_prompt'),
            allowed_extensions,
            excluded_dirs,
            default_ignore_list,
            config_data.get('gemini_default_model'),
            config_data.get('claude_default_model'),
            config_data.get('gpt_default_model'),
            gemini_available_models,
            claude_available_models,
            gpt_available_models,
            gemini_temperature,
            gemini_enable_thinking,
            gemini_thinking_budget,
            gemini_enable_search
        )
        
        result = self.executor.execute(sql, params)
        logger.info(f"Application configuration for profile '{profile_name}' inserted/updated successfully.")
        return result
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """Get all configuration values"""
        query = "SELECT * FROM application_config ORDER BY profile_name"
        results = self.executor.execute(query, fetch_all=True)
        logger.info(f"Retrieved {len(results)} configuration entries")
        return results
    
    def get_model_configs(self) -> List[Dict[str, Any]]:
        """Get model configurations"""
        query = """
            SELECT * FROM model_configs 
            WHERE is_active = true 
            ORDER BY provider, model_name
        """
        results = self.executor.execute(query, fetch_all=True)
        logger.info(f"Retrieved {len(results)} model configurations")
        return results
