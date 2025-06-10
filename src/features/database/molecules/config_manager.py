"""Configuration management molecule"""
import logging
from typing import Optional, Dict, Any, List
from ..atoms.query_executor import QueryExecutor

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration in the database"""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    
    def get_config(self, key: str) -> Optional[str]:
        """Get a configuration value by key"""
        query = "SELECT value FROM application_config WHERE key = %s"
        result = self.executor.execute(query, (key,), fetch_one=True)
        if result:
            value = result if isinstance(result, str) else result.get('value')
            logger.info(f"Retrieved config for key '{key}': {value}")
            return value
        else:
            logger.warning(f"No configuration found for key: {key}")
            return None
    
    def save_config(self, key: str, value: str) -> int:
        """Save or update a configuration value"""
        # Check if the config already exists
        existing = self.get_config(key)
        
        if existing is not None:
            # Update existing config
            query = """
                UPDATE application_config 
                SET value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE key = %s
            """
            result = self.executor.execute(query, (value, key))
            logger.info(f"Updated config for key '{key}' with value: {value}")
        else:
            # Insert new config
            query = """
                INSERT INTO application_config (key, value)
                VALUES (%s, %s)
            """
            result = self.executor.execute(query, (key, value))
            logger.info(f"Inserted new config for key '{key}' with value: {value}")
        
        return result
    
    def get_all_configs(self) -> List[Dict[str, Any]]:
        """Get all configuration values"""
        query = "SELECT * FROM application_config ORDER BY key"
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