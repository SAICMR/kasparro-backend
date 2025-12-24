import psycopg2
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, Dict, List
import logging
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

class Database:
    """PostgreSQL database connection pool"""
    
    _pool: Optional[SimpleConnectionPool] = None
    
    @classmethod
    def initialize(cls):
        """Initialize PostgreSQL connection pool"""
        try:
            database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/etl_db")
            
            # Parse connection string
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "")
            
            # Extract credentials and host
            if "@" in database_url:
                creds, host_db = database_url.split("@")
                user, password = creds.split(":")
                if ":" in host_db:
                    host, db_and_port = host_db.split("/")
                    port = 5432
                    if ":" in host:
                        host, port = host.split(":")
                        port = int(port)
                    database = db_and_port
                else:
                    host, database = host_db.split("/")
                    port = 5432
            else:
                raise ValueError("Invalid DATABASE_URL format")
            
            # Create connection pool
            cls._pool = SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
            logger.info(f"PostgreSQL connection pool initialized: {host}:{port}/{database}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get database connection from pool"""
        if cls._pool is None:
            cls.initialize()
        
        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)
    
    @classmethod
    def check_connection(cls) -> bool:
        """Check if database is accessible"""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    @classmethod
    def execute_query(cls, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results"""
        try:
            with cls.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                results = cursor.fetchall()
                cursor.close()
                
                # Convert to list of dicts
                return [dict(zip(columns, row)) for row in results]
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
            conn.rollback()
            raise
    
    @classmethod
    def close(cls):
        """Close all connections"""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
