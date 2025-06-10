"""API key management molecule"""
import logging
from typing import Optional, Dict, Any
from ..atoms.query_executor import QueryExecutor

logger = logging.getLogger(__name__)


class ApiKeyManager:
    """Manages API keys in the database"""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    
    def get_api_key(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get an API key for a specific service"""
        query = "SELECT * FROM api_keys WHERE service_name = %s"
        result = self.executor.execute(query, (service_name,), fetch_one=True)
        if result:
            logger.info(f"Retrieved API key for service: {service_name}")
        else:
            logger.warning(f"No API key found for service: {service_name}")
        return result
    
    def get_active_api_key(self, service_name: str) -> Optional[str]:
        """Get the active API key for a specific service"""
        query = "SELECT api_key FROM api_keys WHERE service_name = %s AND is_active = true"
        result = self.executor.execute(query, (service_name,), fetch_one=True)
        if result:
            logger.info(f"Retrieved active API key for service: {service_name}")
            return result if isinstance(result, str) else result.get('api_key')
        else:
            logger.warning(f"No active API key found for service: {service_name}")
            return None
    
    def save_api_key(self, service_name: str, api_key: str, is_active: bool = True) -> int:
        """Save or update an API key"""
        # Check if the API key already exists
        existing = self.get_api_key(service_name)
        
        if existing:
            # Update existing key
            query = """
                UPDATE api_keys 
                SET api_key = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
                WHERE service_name = %s
            """
            result = self.executor.execute(query, (api_key, is_active, service_name))
            logger.info(f"Updated API key for service: {service_name}")
        else:
            # Insert new key
            query = """
                INSERT INTO api_keys (service_name, api_key, is_active)
                VALUES (%s, %s, %s)
            """
            result = self.executor.execute(query, (service_name, api_key, is_active))
            logger.info(f"Inserted new API key for service: {service_name}")
        
        return result