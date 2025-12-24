# src/core/database.py
import os
from sqlalchemy import create_all, create_engine
import os
import logging
from typing import Optional, Dict, List, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class Database:
	"""SQLAlchemy-backed Database using PostgreSQL.

	Behavior:
	- Reads `DATABASE_URL` or builds one from `POSTGRES_*` env vars.
	- Provides `initialize()`, `execute_query()`, `execute_update()`,
	  `check_connection()`, and `close()` used by the application and tests.
	"""

	_engine: Optional[Engine] = None
	_SessionLocal = None

	@classmethod
	def _build_database_url(cls) -> str:
		# Prefer explicit DATABASE_URL if provided
		database_url = os.getenv("DATABASE_URL")
		if database_url:
			return database_url

		user = os.getenv("POSTGRES_USER", "postgres")
		password = os.getenv("POSTGRES_PASSWORD", "postgres")
		host = os.getenv("POSTGRES_HOST", "db")
		port = os.getenv("POSTGRES_PORT", "5432")
		db = os.getenv("POSTGRES_DB", "etl_db")

		return f"postgresql://{user}:{password}@{host}:{port}/{db}"

	@classmethod
	def initialize(cls):
		"""Initialize SQLAlchemy engine and session factory."""
		try:
			database_url = cls._build_database_url()
			cls._engine = create_engine(database_url, pool_pre_ping=True)
			cls._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls._engine)
			logger.info(f"Database engine initialized: {database_url}")
		except Exception as e:
			logger.error(f"Failed to initialize database engine: {e}")
			raise

	@classmethod
	def check_connection(cls) -> bool:
		try:
			if cls._engine is None:
				cls.initialize()
			conn = cls._engine.connect()
			conn.close()
			return True
		except Exception as e:
			logger.error(f"Database connection check failed: {e}")
			return False

	@classmethod
	def execute_query(cls, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
		"""Execute a read query and return list of dict rows."""
		try:
			if cls._engine is None:
				cls.initialize()
			with cls._engine.connect() as conn:
				result = conn.execute(text(query), params or {})
				if result.returns_rows:
					rows = [dict(row._mapping) for row in result.fetchall()]
					return rows
				return []
		except Exception as e:
			logger.error(f"Query execution failed: {e}")
			raise

	@classmethod
	def execute_update(cls, query: str, params: Optional[Dict[str, Any]] = None) -> int:
		"""Execute INSERT/UPDATE/DELETE. Returns affected rowcount when possible."""
		try:
			if cls._engine is None:
				cls.initialize()
			with cls._engine.begin() as conn:
				result = conn.execute(text(query), params or {})
				# rowcount may be -1 for some statements; return as-is
				return result.rowcount if result is not None else 0
		except Exception as e:
			logger.error(f"Update execution failed: {e}")
			raise

	@classmethod
	def close(cls):
		if cls._engine:
			cls._engine.dispose()
			cls._engine = None