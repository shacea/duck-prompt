"""Query executor atom - handles SQL query execution"""
import psycopg2
import logging
from typing import Optional, Any, List, Dict
from psycopg2.extensions import connection as Connection

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Atomic component for executing database queries"""
    
    def __init__(self, connection: Connection):
        self.connection = connection
    
    def execute(
        self, 
        query: str, 
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False,
        return_id: bool = False
    ) -> Optional[Any]:
        """Execute a SQL query and return the result"""
        if not self.connection or self.connection.closed:
            raise ConnectionError("Database connection is not active")
            
        cursor = None
        try:
            cursor = self.connection.cursor()
            logger.debug(f"Executing query: {query} with params: {params}")
            cursor.execute(query, params)
            
            if return_id:
                result = cursor.fetchone()
                self.connection.commit()
                logger.debug(f"Query returned ID: {result[0] if result else None}")
                return result[0] if result else None
            elif fetch_one:
                result = cursor.fetchone()
                if result and cursor.description:
                    colnames = [desc[0] for desc in cursor.description]
                    row_dict = dict(zip(colnames, result))
                    logger.debug(f"Query fetched one row: {row_dict}")
                    return row_dict
                elif result:
                    logger.debug(f"Query fetched one value: {result[0]}")
                    return result[0]
                else:
                    logger.debug("Query fetched no results (fetch_one).")
                    return None
            elif fetch_all:
                if cursor.description:
                    colnames = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    results_list = [dict(zip(colnames, row)) for row in rows]
                    logger.debug(f"Query fetched {len(results_list)} rows.")
                    return results_list
                else:
                    logger.debug("Query fetched no results (fetch_all).")
                    return []
            else:
                affected_rows = cursor.rowcount
                self.connection.commit()
                logger.debug(f"Query executed successfully. Rows affected: {affected_rows}")
                return affected_rows
        except psycopg2.Error as e:
            logger.error(f"Database query failed: {e}\nQuery: {query}\nParams: {params}", exc_info=True)
            if self.connection:
                self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
