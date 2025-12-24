import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import csv
from io import StringIO
from src.core.database import Database
from src.schemas.models import DataRecord

logger = logging.getLogger(__name__)

class ETLPipeline:
    """Main ETL orchestrator"""
    
    def __init__(self):
        self.db = Database
        self.start_time = None
        self.end_time = None
        self.total_records = 0
        self.errors = []
    
    def initialize_schema(self):
        """Create necessary tables if they don't exist"""
        logger.info("Initializing database schema")
        
        # Raw data tables
        self.db.execute_update("""
            CREATE TABLE IF NOT EXISTS raw_api_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT UNIQUE,
                data TEXT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute_update("""
            CREATE TABLE IF NOT EXISTS raw_csv_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT UNIQUE,
                data TEXT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Normalized data table
        self.db.execute_update("""
            CREATE TABLE IF NOT EXISTS normalized_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                source_id TEXT,
                name TEXT,
                value REAL,
                description TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                UNIQUE(source, source_id)
            )
        """)
        
        # Checkpoint table for incremental ingestion
        self.db.execute_update("""
            CREATE TABLE IF NOT EXISTS etl_checkpoint (
                source TEXT PRIMARY KEY,
                last_processed_id TEXT,
                last_processed_at TIMESTAMP,
                total_processed INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ETL run metrics
        self.db.execute_update("""
            CREATE TABLE IF NOT EXISTS etl_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                duration_seconds REAL,
                records_processed INTEGER,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logger.info("Database schema initialized successfully")
    
    def get_last_checkpoint(self, source: str) -> Optional[Dict]:
        """Get last checkpoint for a source"""
        results = self.db.execute_query(
            "SELECT * FROM etl_checkpoint WHERE source = ?",
            (source,)
        )
        return results[0] if results else None
    
    def update_checkpoint(self, source: str, last_id: str, total: int):
        """Update checkpoint after processing"""
        # For SQLite, use INSERT OR REPLACE (UPSERT)
        self.db.execute_update(
            """
            INSERT OR REPLACE INTO etl_checkpoint 
            (source, last_processed_id, last_processed_at, total_processed, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (source, last_id, datetime.now(), total)
        )
    
    def ingest_api_data(self, api_url: str, headers: Dict = None) -> List[Dict]:
        """Fetch data from API"""
        try:
            logger.info(f"Fetching data from API: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Handle both array and dict responses
            if isinstance(data, dict):
                data = data.get('data', []) or [data]
            elif not isinstance(data, list):
                data = [data]
            
            logger.info(f"Retrieved {len(data)} records from API")
            return data
        except Exception as e:
            logger.error(f"API ingestion failed: {e}")
            self.errors.append(f"API ingestion error: {e}")
            return []
    
    def ingest_csv_data(self, csv_url: str) -> List[Dict]:
        """Fetch data from CSV"""
        try:
            logger.info(f"Fetching CSV from: {csv_url}")
            response = requests.get(csv_url, timeout=30)
            response.raise_for_status()
            
            csv_reader = csv.DictReader(StringIO(response.text))
            data = list(csv_reader)
            
            logger.info(f"Retrieved {len(data)} records from CSV")
            return data
        except Exception as e:
            logger.error(f"CSV ingestion failed: {e}")
            self.errors.append(f"CSV ingestion error: {e}")
            return []
    
    def store_raw_data(self, source: str, data: List[Dict]):
        """Store raw data in appropriate raw table"""
        table_name = f"raw_{source}_data"
        processed = 0
        
        for record in data:
            try:
                source_id = str(record.get('id', record.get('ID', hash(str(record)))))
                self.db.execute_update(
                    f"""
                    INSERT OR IGNORE INTO {table_name} (source_id, data)
                    VALUES (?, ?)
                    """,
                    (source_id, str(record))
                )
                processed += 1
            except Exception as e:
                logger.warning(f"Failed to store raw record: {e}")
        
        logger.info(f"Stored {processed} raw records from {source}")
        return processed
    
    def normalize_data(self, source: str, raw_data: List[Dict]) -> List[DataRecord]:
        """Transform raw data to unified schema"""
        normalized = []
        
        for record in raw_data:
            try:
                source_id = str(record.get('id', record.get('ID', record.get('index', 'unknown'))))
                
                normalized_record = DataRecord(
                    source=source,
                    source_id=source_id,
                    name=str(record.get('name', record.get('NAME', record.get('title', 'Unknown')))),
                    value=self._safe_float(record.get('value', record.get('VALUE'))),
                    description=str(record.get('description', record.get('body', ''))),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                normalized.append(normalized_record)
            except Exception as e:
                logger.warning(f"Failed to normalize record from {source}: {e}")
        
        return normalized
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            return float(value) if value else None
        except (ValueError, TypeError):
            return None
    
    def store_normalized_data(self, records: List[DataRecord]) -> int:
        """Store normalized data"""
        processed = 0
        
        for record in records:
            try:
                self.db.execute_update(
                    """
                    INSERT OR REPLACE INTO normalized_data 
                    (source, source_id, name, value, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (record.source, record.source_id, record.name, record.value,
                     record.description, record.created_at, record.updated_at)
                )
                processed += 1
            except Exception as e:
                logger.warning(f"Failed to store normalized record: {e}")
        
        return processed
    
    def record_run(self, success: bool, records_processed: int, error_msg: str = None):
        """Record ETL run metadata"""
        if not self.start_time:
            self.start_time = datetime.now()
        
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        self.db.execute_update(
            """
            INSERT INTO etl_runs 
            (started_at, ended_at, duration_seconds, records_processed, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (self.start_time, self.end_time, duration, records_processed,
             'success' if success else 'failed', error_msg)
        )
        
        logger.info(f"ETL run recorded: status={'success' if success else 'failed'}, "
                   f"duration={duration}s, records={records_processed}")
    
    def run(self, api_url: str, csv_url: str, headers: Dict = None):
        """Execute full ETL pipeline"""
        logger.info("Starting ETL pipeline")
        self.start_time = datetime.now()
        total_processed = 0
        
        try:
            # Initialize schema
            self.initialize_schema()
            
            # API ingestion
            api_data = self.ingest_api_data(api_url, headers)
            if api_data:
                self.store_raw_data('api', api_data)
                normalized_api = self.normalize_data('api', api_data)
                processed = self.store_normalized_data(normalized_api)
                self.update_checkpoint('api', str(len(api_data)), processed)
                total_processed += processed
            
            # CSV ingestion
            csv_data = self.ingest_csv_data(csv_url)
            if csv_data:
                self.store_raw_data('csv', csv_data)
                normalized_csv = self.normalize_data('csv', csv_data)
                processed = self.store_normalized_data(normalized_csv)
                self.update_checkpoint('csv', str(len(csv_data)), processed)
                total_processed += processed
            
            # Record successful run
            self.record_run(True, total_processed)
            logger.info(f"ETL pipeline completed successfully: {total_processed} records processed")
            return True
            
        except Exception as e:
            error_msg = f"ETL pipeline failed: {str(e)}"
            logger.error(error_msg)
            self.record_run(False, total_processed, error_msg)
            return False
