from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import threading
from typing import Optional
import uuid

from src.core.database import Database
from src.core.config import LOG_LEVEL, API_HOST, CSV_URL, API_KEY
from src.core.logger import setup_logging
from src.schemas.models import DataRecord, PaginatedResponse, HealthResponse, StatsResponse
from src.schemas.models import CreateDataRequest
from src.etl.pipeline import ETLPipeline

# Setup logging
setup_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="ETL Data API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ETL instance
etl_pipeline = ETLPipeline()

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    logger.info("Starting up application")
    Database.initialize()
    etl_pipeline.initialize_schema()
    
    # Run initial ETL
    logger.info("Running initial ETL pipeline")
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    etl_pipeline.run(f"{API_HOST}/posts", CSV_URL, headers)

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")
    Database.close()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns DB connectivity and last ETL status
    """
    db_connected = Database.check_connection()
    
    # Get last ETL run
    last_run = Database.execute_query(
        "SELECT * FROM etl_runs ORDER BY created_at DESC LIMIT 1"
    )
    
    etl_status = "unknown"
    last_run_time = None
    if last_run:
        etl_status = last_run[0]['status']
        last_run_time = last_run[0]['ended_at']
    
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        db_connected=db_connected,
        last_etl_run=last_run_time,
        etl_status=etl_status
    )

@app.get("/data", response_model=PaginatedResponse)
async def get_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Fetch paginated data with optional filtering
    Returns: paginated records with metadata
    """
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] GET /data - page={page}, page_size={page_size}, source={source}, search={search}")
    
    try:
        # Build query
        where_clauses = []
        params = []
        
        if source:
            where_clauses.append("source = ?")
            params.append(source)
        
        if search:
            where_clauses.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM normalized_data {where_clause}"
        count_result = Database.execute_query(count_query, tuple(params))
        total = count_result[0]['total'] if count_result else 0
        
        # Get paginated data
        offset = (page - 1) * page_size
        data_query = f"""
            SELECT * FROM normalized_data 
            {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        results = Database.execute_query(data_query, tuple(params))
        
        # Convert to Pydantic models
        data_records = [DataRecord(**record) for record in results]
        
        has_more = (page * page_size) < total
        
        logger.info(f"[{request_id}] Returning {len(data_records)} records")
        
        return PaginatedResponse(
            data=data_records,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
    
    except Exception as e:
        logger.error(f"[{request_id}] Error fetching data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get ETL statistics and run metadata
    """
    try:
        # Get aggregated stats
        stats_result = Database.execute_query("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN status = 'success' THEN records_processed ELSE 0 END) as total_processed,
                SUM(duration_seconds) as total_duration
            FROM etl_runs
        """)
        
        # Get last success/failure
        last_runs = Database.execute_query("""
            SELECT status, ended_at, error_message 
            FROM etl_runs 
            ORDER BY ended_at DESC 
            LIMIT 2
        """)
        
        total_records = stats_result[0]['total_records'] if stats_result else 0
        total_processed = stats_result[0]['total_processed'] or 0
        total_duration = float(stats_result[0]['total_duration'] or 0)
        
        last_success = None
        last_failure = None
        last_failure_reason = None
        
        for run in last_runs:
            if run['status'] == 'success' and not last_success:
                last_success = run['ended_at']
            elif run['status'] == 'failed' and not last_failure:
                last_failure = run['ended_at']
                last_failure_reason = run['error_message']
        
        return StatsResponse(
            total_records_processed=int(total_processed),
            total_duration_seconds=total_duration,
            last_success=last_success,
            last_failure=last_failure,
            last_failure_reason=last_failure_reason,
            run_count=total_records
        )
    
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/etl/run")
async def trigger_etl(background: BackgroundTasks):
    """Trigger the ETL pipeline asynchronously (manual run)."""
    run_id = str(uuid.uuid4())
    logger.info(f"Manual ETL trigger requested: {run_id}")

    def _run():
        try:
            headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
            etl_pipeline.run(f"{API_HOST}/posts", CSV_URL, headers)
            logger.info(f"Manual ETL {run_id} completed")
        except Exception as e:
            logger.error(f"Manual ETL {run_id} failed: {e}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"run_id": run_id, "status": "started"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ETL Data API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "GET /data": "Fetch paginated data",
            "GET /stats": "ETL statistics"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.post("/data", response_model=DataRecord)
async def create_data(record: CreateDataRequest):
    """Create or upsert a normalized data record"""
    try:
        now = datetime.now()
        # Use INSERT OR REPLACE to honor UNIQUE(source, source_id)
        insert_query = """
            INSERT OR REPLACE INTO normalized_data
            (id, source, source_id, name, value, description, created_at, updated_at)
            VALUES (
                (SELECT id FROM normalized_data WHERE source = ? AND source_id = ?),
                ?, ?, ?, ?, ?, ?, ?
            )
        """

        params = (
            record.source,
            record.source_id,
            record.source,
            record.source_id,
            record.name,
            record.value,
            record.description or "",
            now,
            now,
        )

        self_db = Database
        self_db.execute_update(insert_query, params)

        # Return the created/updated record
        res = Database.execute_query(
            "SELECT * FROM normalized_data WHERE source = ? AND source_id = ?",
            (record.source, record.source_id)
        )
        if not res:
            raise HTTPException(status_code=500, detail="Failed to create record")
        return DataRecord(**res[0])
    except Exception as e:
        logger.error(f"Error creating data record: {e}")
        raise HTTPException(status_code=500, detail=str(e))
