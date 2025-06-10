"""Database connection atom - manages PostgreSQL connection"""
import psycopg2
import logging
from typing import Optional, Dict, Any
from psycopg2.extensions import connection as Connection

logger = logging.getLogger(__name__)

# Database connection configuration (hardcoded as per requirements)
DB_CONFIG = {
    "host": "postgresdb.lab.miraker.me",
    "user": "shacea",
    "password": "alfkzj9389",
    "port": 5333,
    "database": "duck_agent"
}


class DatabaseConnection:
    """Atomic component for database connection management"""
    
    def __init__(self, db_config: Dict[str, Any] = DB_CONFIG):
        self.db_config = db_config
        self.connection: Optional[Connection] = None
        
    def connect(self) -> None:
        """Establishes a connection to the PostgreSQL database"""
        if self.connection and not self.connection.closed:
            return  # Already connected
            
        try:
            logger.info(f"Connecting to database '{self.db_config['database']}' on {self.db_config['host']}...")
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("Database connection successful.")
        except psycopg2.Error as e:
            logger.critical(f"Database connection failed: {e}", exc_info=True)
            self.connection = None
            raise ConnectionError(f"Failed to connect to the database: {e}")
    
    def disconnect(self) -> None:
        """Closes the database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Database connection closed.")
        self.connection = None
    
    def is_connected(self) -> bool:
        """Check if the database connection is active"""
        return bool(self.connection and not self.connection.closed)
    
    def get_connection(self) -> Connection:
        """Get the active database connection"""
        if not self.is_connected():
            self.connect()
        if self.connection is None:
            raise ConnectionError("Failed to establish a database connection.")
        return self.connection
