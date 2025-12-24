import sqlite3
from typing import Optional, List, Dict, Any
import logging
import json
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """SQLite database connection for local development without PostgreSQL"""
    
    _connection: Optional[sqlite3.Connection] = None
    
    @classmethod
    def initialize(cls):
        """Initialize SQLite database"""
        try:
            cls._connection = sqlite3.connect('etl_local.db', check_same_thread=False)
            cls._connection.row_factory = sqlite3.Row
            logger.info("SQLite database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get database connection"""
        if cls._connection is None:
            cls.initialize()
        yield cls._connection
    
    @classmethod
    def check_connection(cls) -> bool:
        """Check if database is accessible"""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    @classmethod
    def execute_query(cls, query: str, params: tuple = None) -> list:
        """Execute a query and return results"""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                cursor.close()
                # Convert sqlite3.Row to dict for compatibility
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    @classmethod
    def execute_update(cls, query: str, params: tuple = None) -> int:
        """Execute an update/insert/delete and return affected rows"""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                affected = cursor.rowcount
                conn.commit()
                cursor.close()
            return affected
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            raise
    
    @classmethod
    def close(cls):
        """Close database connection"""
        if cls._connection:
            cls._connection.close()
            cls._connection = None
