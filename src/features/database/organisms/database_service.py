"""Database service organism - combines all database operations"""
import logging
from typing import Optional, Dict, Any, List
from ..atoms.db_connection import DatabaseConnection
from ..atoms.query_executor import QueryExecutor
from ..molecules.api_key_manager import ApiKeyManager
from ..molecules.config_manager import ConfigManager
from ..molecules.gemini_log_manager import GeminiLogManager

logger = logging.getLogger(__name__)


class DatabaseService:
    """High-level database service combining all database operations"""
    
    def __init__(self):
        self.db_connection = DatabaseConnection()
        self.query_executor: Optional[QueryExecutor] = None
        self.api_key_manager: Optional[ApiKeyManager] = None
        self.config_manager: Optional[ConfigManager] = None
        self.gemini_log_manager: Optional[GeminiLogManager] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the database connection and managers"""
        try:
            self.db_connection.connect()
            connection = self.db_connection.get_connection()
            self.query_executor = QueryExecutor(connection)
            self.api_key_manager = ApiKeyManager(self.query_executor)
            self.config_manager = ConfigManager(self.query_executor)
            self.gemini_log_manager = GeminiLogManager(self.query_executor)
            logger.info("Database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    def connect(self) -> None:
        """Connect to the database"""
        self.db_connection.connect()
        self._initialize()
    
    def disconnect(self) -> None:
        """Disconnect from the database"""
        self.db_connection.disconnect()
        self.query_executor = None
        self.api_key_manager = None
        self.config_manager = None
        self.gemini_log_manager = None
    
    def is_connected(self) -> bool:
        """Check if the database is connected"""
        return self.db_connection.is_connected()
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False,
        return_id: bool = False
    ) -> Optional[Any]:
        """Execute a raw SQL query"""
        if not self.query_executor:
            raise ConnectionError("Database service not initialized")
        return self.query_executor.execute(query, params, fetch_one, fetch_all, return_id)
    
    def get_ignored_patterns(self) -> List[str]:
        """Get ignored file patterns from the database"""
        query = "SELECT pattern FROM gitignore_patterns ORDER BY pattern"
        results = self.execute_query(query, fetch_all=True)
        return [r['pattern'] for r in results] if results else []
    
    def save_ignored_patterns(self, patterns: List[str]) -> None:
        """Save ignored file patterns to the database"""
        # Clear existing patterns
        self.execute_query("DELETE FROM gitignore_patterns")
        
        # Insert new patterns
        for pattern in patterns:
            if pattern.strip():
                query = "INSERT INTO gitignore_patterns (pattern) VALUES (%s)"
                self.execute_query(query, (pattern.strip(),))
        
        logger.info(f"Saved {len(patterns)} ignored patterns to database")