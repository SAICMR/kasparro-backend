from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DataRecord(BaseModel):
    """Unified schema for all ingested data"""
    id: Optional[int] = None
    source: str
    source_id: str
    name: str
    value: Optional[float] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    """Standard paginated response format"""
    data: List[DataRecord]
    total: int
    page: int
    page_size: int
    has_more: bool

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    db_connected: bool
    last_etl_run: Optional[datetime]
    etl_status: str

class StatsResponse(BaseModel):
    """ETL statistics response"""
    total_records_processed: int
    total_duration_seconds: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    last_failure_reason: Optional[str]
    run_count: int

class ETLCheckpoint(BaseModel):
    """Checkpoint for resumable ETL"""
    source: str
    last_processed_id: str
    last_processed_at: datetime
    total_processed: int


class CreateDataRequest(BaseModel):
    """Payload for creating a new normalized data record"""
    source: str = Field(..., description="Data source identifier (api/csv)")
    source_id: str = Field(..., description="Unique id from the source")
    name: str
    value: Optional[float] = None
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "source": "api",
                "source_id": "123",
                "name": "Example record",
                "value": 1.23,
                "description": "Optional description"
            }
        }
