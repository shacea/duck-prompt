"""API key management molecule"""
import logging
from typing import Optional, Dict, Any
from ..atoms.query_executor import QueryExecutor

logger = logging.getLogger(__name__)


class ApiKeyManager:
    """Manages API keys in the database"""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    
    def get_api_key(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get an API key for a specific provider"""
        query = "SELECT * FROM api_keys WHERE provider = %s"
        result = self.executor.execute(query, (provider,), fetch_one=True)
        if result:
            logger.info(f"Retrieved API key for provider: {provider}")
        else:
            logger.warning(f"No API key found for provider: {provider}")
        return result
    
    def get_active_api_key(self, provider: str) -> Optional[str]:
        """Get the active API key for a specific provider"""
        query = "SELECT api_key FROM api_keys WHERE provider = %s AND is_active = true"
        result = self.executor.execute(query, (provider,), fetch_one=True)
        if result:
            logger.info(f"Retrieved active API key for provider: {provider}")
            return result if isinstance(result, str) else result.get('api_key')
        else:
            logger.warning(f"No active API key found for provider: {provider}")
            return None
    
    def save_api_key(self, provider: str, api_key: str, is_active: bool = True) -> int:
        """Save or update an API key"""
        # Check if the API key already exists
        existing = self.get_api_key(provider)
        
        if existing:
            # Update existing key
            query = """
                UPDATE api_keys 
                SET api_key = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
                WHERE provider = %s
            """
            result = self.executor.execute(query, (api_key, is_active, provider))
            logger.info(f"Updated API key for provider: {provider}")
        else:
            # Insert new key
            query = """
                INSERT INTO api_keys (provider, api_key, is_active)
                VALUES (%s, %s, %s)
            """
            result = self.executor.execute(query, (provider, api_key, is_active))
            logger.info(f"Inserted new API key for provider: {provider}")
        
        return result
