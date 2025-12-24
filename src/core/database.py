import os
import logging
import sqlite3
from typing import Optional, Dict, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """SQLite database for local development (Docker fallback)"""
    
    _connection: Optional[sqlite3.Connection] = None
    
    @classmethod
    def initialize(cls):
        """Initialize SQLite database for local development"""
        try:
            db_path = os.path.join(os.getcwd(), "etl_local.db")
            cls._connection = sqlite3.connect(db_path, check_same_thread=False)
            cls._connection.row_factory = sqlite3.Row
            logger.info(f"SQLite database initialized at {db_path}")
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
    def execute_query(cls, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results"""
        try:
            # Convert PostgreSQL %s to SQLite ?
            query = query.replace('%s', '?')
            # Convert ILIKE to LIKE for SQLite (case insensitive already in SQLite)
            query = query.replace('ILIKE', 'LIKE')
            
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                cursor.close()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    @classmethod
    def execute_update(cls, query: str, params: tuple = None) -> int:
        """Execute an update/insert/delete and return affected rows"""
        try:
            # Convert PostgreSQL %s to SQLite ?
            query = query.replace('%s', '?')
            # Convert ON CONFLICT to SQLite syntax
            query = query.replace('ON CONFLICT (source, source_id) DO UPDATE SET', 'ON CONFLICT(source, source_id) DO UPDATE SET')
            query = query.replace('ON CONFLICT (source) DO UPDATE SET', 'ON CONFLICT(source) DO UPDATE SET')
            
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
        """Close all connections"""
        if cls._connection:
            cls._connection.close()
            cls._connection = None


