# ETL Data Pipeline System

A lightweight, production-ready ETL system built with FastAPI, PostgreSQL, and Docker.

## Overview

This system demonstrates a complete data ingestion pipeline that:
- Pulls data from **API** and **CSV** sources
- Stores raw data in PostgreSQL
- Normalizes data into a unified schema
- Exposes REST endpoints for data access
- Handles incremental ingestion with checkpoints
- Provides comprehensive health checks and statistics

## Architecture

```
┌─────────────┐
│   API Data  │  ┌──────────────────────────────┐
└─────────────┘  │    ETL Pipeline              │
                 │  ┌──────────────────────────┐│
┌─────────────┐  │  │ 1. Ingest (API + CSV)   ││
│  CSV Data   │──►  │ 2. Store Raw Data       ││
└─────────────┘  │  │ 3. Normalize Schema     ││
                 │  │ 4. Checkpointing        ││
                 │  └──────────────────────────┘│
                 └──────────────────────────────┘
                            │
                            ▼
                 ┌──────────────────────────┐
                 │   PostgreSQL Database    │
                 ├──────────────────────────┤
                 │ • raw_api_data           │
                 │ • raw_csv_data           │
                 │ • normalized_data        │
                 │ • etl_checkpoint         │
                 │ • etl_runs               │
                 └──────────────────────────┘
                            │
                            ▼
                 ┌──────────────────────────┐
                 │   FastAPI Backend        │
                 ├──────────────────────────┤
                 │ GET /data (paginated)    │
                 │ GET /health              │
                 │ GET /stats               │
                 └──────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Make (for running commands)
- Or Python 3.11+ and PostgreSQL (for local development)

### Setup

1. **Clone and enter the directory**
```bash
cd backenddevelopment
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your API key if needed
```

3. **Start the system**
```bash
make up
```

The system will:
- Start PostgreSQL database
- Initialize schema
- Run initial ETL pipeline
- Expose API at `http://localhost:8000`

### Verify It Works

```bash
# Health check
curl http://localhost:8000/health

# Get data
curl http://localhost:8000/data?page=1&page_size=10

# Get statistics
curl http://localhost:8000/stats
```

## Available Commands

```bash
make up          # Start all services
make down        # Stop all services
make test        # Run test suite
make logs        # View application logs
make build       # Build Docker image
make clean       # Remove containers and volumes
make lint        # Check code quality
make shell       # Open bash in app container
make db-shell    # Open PostgreSQL shell
```

## API Endpoints

### `GET /health`
Health check endpoint that returns database connectivity and last ETL status.

**Response:**
```json
{
  "status": "healthy",
  "db_connected": true,
  "last_etl_run": "2024-12-23T10:30:00",
  "etl_status": "success"
}
```

### `GET /data`
Fetch paginated data with optional filtering.

**Parameters:**
- `page` (int, default=1): Page number
- `page_size` (int, default=10, max=100): Records per page
- `source` (string, optional): Filter by source (api, csv)
- `search` (string, optional): Search in name and description

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "source": "api",
      "source_id": "1",
      "name": "Sample Record",
      "value": 100.5,
      "description": "Sample description",
      "created_at": "2024-12-23T10:00:00",
      "updated_at": "2024-12-23T10:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "has_more": true
}
```

### `GET /stats`
Get ETL pipeline statistics and run metadata.

**Response:**
```json
{
  "total_records_processed": 500,
  "total_duration_seconds": 45.2,
  "last_success": "2024-12-23T10:30:00",
  "last_failure": "2024-12-22T15:00:00",
  "last_failure_reason": "Connection timeout",
  "run_count": 10
}
```

## Project Structure

```
backenddevelopment/
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI application
│   ├── etl/
│   │   └── pipeline.py          # ETL orchestration
│   ├── schemas/
│   │   └── models.py            # Pydantic models
│   └── core/
│       ├── config.py            # Configuration
│       ├── database.py          # Database connection pool
│       └── logger.py            # Logging setup
├── tests/
│   ├── test_etl.py              # ETL tests
│   └── test_api.py              # API tests
├── Dockerfile                    # Container image
├── docker-compose.yml            # Multi-container setup
├── Makefile                      # Build automation
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Key Features

### ✅ P0 - Foundation Layer

- **Data Ingestion**: Pulls from API (JSONPlaceholder) and CSV sources
- **Raw Storage**: Stores unmodified data in `raw_*_data` tables
- **Schema Normalization**: Unified `DataRecord` schema with Pydantic validation
- **Incremental Ingestion**: Checkpoint system prevents reprocessing
- **Secure Auth**: Environment variable-based API key management
- **Backend API**: 
  - `GET /data` with pagination and filtering
  - `GET /health` with DB and ETL status
- **Dockerized System**: Single `make up` command
- **Tests**: Coverage for ETL logic and API endpoints

### ✅ P1 - Growth Layer (Expandable)

- **Third Data Source**: Easily extensible to add RSS, webhooks, or additional CSVs
- **Improved Checkpointing**: Per-source checkpoint tracking with resume capability
- **Statistics Endpoint**: `/stats` provides comprehensive run metadata
- **Enhanced Tests**: Incremental ingestion, failure scenarios, schema validation
- **Clean Architecture**: Separation of concerns across modules

## Configuration

Edit `.env` to configure:

```
API_KEY=your-api-key           # For authenticated API sources
DATABASE_URL=postgresql://...  # Database connection string
ETL_INTERVAL=3600             # ETL run interval in seconds
LOG_LEVEL=INFO                # Logging level
API_HOST=http://...           # Primary API endpoint
CSV_URL=https://...           # CSV data source
```

## Development

### Running Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/etl_db

# Run app
python -m uvicorn src.api.main:app --reload

# Run tests
pytest tests/ -v
```

### Database Inspection

```bash
# Open database shell
make db-shell

# View normalized data
SELECT COUNT(*) FROM normalized_data;
SELECT * FROM normalized_data LIMIT 10;

# View ETL runs
SELECT * FROM etl_runs ORDER BY created_at DESC;

# View checkpoints
SELECT * FROM etl_checkpoint;
```

## Testing

Run the test suite:

```bash
make test
```

Tests cover:
- ETL data normalization
- API data ingestion
- CSV parsing
- Safe type conversions
- API endpoints
- Error handling
- Database operations

## Error Handling

The system handles:
- **Connection Errors**: Retries and logs failures
- **Data Validation**: Pydantic schema enforcement
- **Duplicate Data**: UPSERT operations prevent duplicates
- **Missing Fields**: Graceful handling with defaults
- **Type Conversion**: Safe float and datetime parsing

## Monitoring

View logs in real-time:
```bash
make logs
```

Key log events:
- ETL pipeline start/completion
- Data ingestion counts
- Checkpoint updates
- API request metrics
- Database operations

## Security Considerations

- **API Keys**: Stored in environment variables, never hardcoded
- **Database**: Uses connection pooling
- **SQL Injection**: Parameterized queries throughout
- **CORS**: Enabled for cross-origin requests
- **Health Checks**: Built-in Docker health monitoring

## Performance Notes

- Connection pooling (min: 5, max: 20)
- Batch inserts via UPSERT
- Indexed tables for fast queries
- Pagination limits query size
- Checkpoint system minimizes reprocessing

## Next Steps (P2 - Differentiator Layer)

To extend this system further:

1. **Schema Drift Detection**: Monitor source schema changes
2. **Failure Injection**: Test recovery mechanisms
3. **Rate Limiting**: Per-source request throttling
4. **Observability**: Prometheus metrics, structured logs
5. **CI/CD**: GitHub Actions pipeline
6. **Anomaly Detection**: Compare ETL runs and flag outliers
7. **Cloud Deployment**: AWS/GCP/Azure scheduled jobs

## Troubleshooting

**Port 5432 already in use:**
```bash
docker ps  # Find container
docker kill <container_id>
make up
```

**Database connection error:**
```bash
make down
make clean
make up  # Fresh start
```

**Tests failing:**
```bash
make clean
make build
make test
```

**View all logs:**
```bash
docker-compose logs -f
```

## License

MIT

## Support

For issues or questions, check:
1. Docker logs: `make logs`
2. Database: `make db-shell`
3. API docs: `http://localhost:8000/docs` (interactive Swagger UI)

---

Built with FastAPI, PostgreSQL, and Docker. Ready for production deployment.
