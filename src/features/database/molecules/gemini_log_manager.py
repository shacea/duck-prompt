"""Gemini API log management molecule"""
import logging
from typing import Optional, Dict, Any, List
from ..atoms.query_executor import QueryExecutor

logger = logging.getLogger(__name__)


class GeminiLogManager:
    """Manages Gemini API logs in the database"""
    
    def __init__(self, query_executor: QueryExecutor):
        self.executor = query_executor
    
    def save_log(
        self,
        model_name: str,
        prompt_tokens: int,
        response_tokens: int,
        total_tokens: int,
        response_text: Optional[str] = None,
        response_summary: Optional[str] = None
    ) -> int:
        """Save a Gemini API log entry"""
        query = """
            INSERT INTO gemini_logs (
                model_name, prompt_tokens, response_tokens, total_tokens,
                response_text, response_summary
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            model_name,
            prompt_tokens,
            response_tokens,
            total_tokens,
            response_text,
            response_summary
        )
        
        log_id = self.executor.execute(query, params, return_id=True)
        logger.info(f"Saved Gemini log entry with ID: {log_id}")
        return log_id
    
    def get_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve Gemini logs with pagination"""
        query = """
            SELECT * FROM gemini_logs 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        results = self.executor.execute(query, (limit, offset), fetch_all=True)
        logger.info(f"Retrieved {len(results)} Gemini log entries")
        return results
    
    def get_total_usage(self) -> Dict[str, Any]:
        """Get total token usage"""
        query = """
            SELECT 
                COUNT(*) as total_requests,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(response_tokens) as total_response_tokens,
                SUM(total_tokens) as total_tokens
            FROM gemini_logs
        """
        result = self.executor.execute(query, fetch_one=True)
        return result or {}
