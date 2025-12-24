# 🔧 Developer Guide & Common Commands

## Table of Contents
1. [Development Setup](#development-setup)
2. [Common Commands](#common-commands)
3. [API Usage Examples](#api-usage-examples)
4. [Database Queries](#database-queries)
5. [Testing Guide](#testing-guide)
6. [Docker Commands](#docker-commands)
7. [Troubleshooting](#troubleshooting)

---

## Development Setup

### First Time Setup

```bash
# Clone/enter the project
cd c:\Users\saide\OneDrive\Desktop\backenddevelopment

# Copy environment file
cp .env.example .env

# Edit .env with your values
# Add API key if needed
```

### Start Development

```bash
# Start all services
make up

# Wait for database to initialize (30 seconds)

# Verify it's running
curl http://localhost:8000/health
```

### Stop Everything

```bash
make down
```

---

## Common Commands

### Makefile Commands

```bash
make up              # Start all services
make down            # Stop all services
make logs            # View app logs
make test            # Run test suite
make build           # Rebuild Docker image
make clean           # Remove containers and volumes
make lint            # Check code style
make shell           # Open bash in container
make db-shell        # Open PostgreSQL shell
```

### Container Commands

```bash
# List running containers
docker ps

# View container logs
docker logs -f etl_app

# Execute command in container
docker exec etl_app python cli.py stats

# Stop container
docker stop etl_app

# Remove container
docker rm etl_app
```

### Database Commands

```bash
# Open database shell
make db-shell

# Or with direct command
docker-compose exec db psql -U postgres -d etl_db

# Then in PostgreSQL:
\dt                              # List tables
SELECT * FROM normalized_data;   # View data
SELECT COUNT(*) FROM normalized_data;  # Count records
```

---

## API Usage Examples

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Get first page of data
curl http://localhost:8000/data?page=1&page_size=10

# Filter by source
curl http://localhost:8000/data?source=api

# Search in data
curl http://localhost:8000/data?search=test

# Pagination - get 3rd page with 20 items per page
curl http://localhost:8000/data?page=3&page_size=20

# Get statistics
curl http://localhost:8000/stats
```

### PowerShell Examples

```powershell
# Health check
(Invoke-WebRequest http://localhost:8000/health).Content | ConvertFrom-Json

# Get data
(Invoke-WebRequest http://localhost:8000/data?page=1).Content | ConvertFrom-Json

# Pretty print
Invoke-WebRequest http://localhost:8000/stats | Select -ExpandProperty Content | ConvertFrom-Json | Format-Table
```

### Python Examples

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(json.dumps(response.json(), indent=2))

# Get data
response = requests.get(f"{BASE_URL}/data?page=1&page_size=10")
data = response.json()
print(f"Total records: {data['total']}")
print(f"Current page: {data['page']}")

# Get stats
response = requests.get(f"{BASE_URL}/stats")
stats = response.json()
print(f"Total processed: {stats['total_records_processed']}")
```

### JavaScript Examples

```javascript
const BASE_URL = "http://localhost:8000";

// Fetch data
fetch(`${BASE_URL}/data?page=1&page_size=10`)
  .then(res => res.json())
  .then(data => {
    console.log(`Found ${data.total} records`);
    console.log(data.data);
  });

// Get stats
fetch(`${BASE_URL}/stats`)
  .then(res => res.json())
  .then(stats => console.log(stats));

// Check health
fetch(`${BASE_URL}/health`)
  .then(res => res.json())
  .then(health => console.log(`Status: ${health.status}`));
```

---

## Database Queries

### Common Queries

```sql
-- Count records by source
SELECT source, COUNT(*) as count 
FROM normalized_data 
GROUP BY source;

-- Latest records
SELECT * FROM normalized_data 
ORDER BY updated_at DESC 
LIMIT 10;

-- Records containing a word
SELECT * FROM normalized_data 
WHERE name ILIKE '%search_term%'
LIMIT 20;

-- Recent ETL runs
SELECT * FROM etl_runs 
ORDER BY created_at DESC 
LIMIT 5;

-- ETL success rate
SELECT 
  status,
  COUNT(*) as runs,
  AVG(duration_seconds) as avg_duration
FROM etl_runs
GROUP BY status;

-- Current checkpoint status
SELECT * FROM etl_checkpoint;

-- Data volume by source
SELECT 
  source,
  COUNT(*) as records,
  AVG(value) as avg_value,
  MIN(value) as min_value,
  MAX(value) as max_value
FROM normalized_data
GROUP BY source;

-- Slowest ETL runs
SELECT 
  started_at,
  ended_at,
  duration_seconds,
  records_processed,
  status
FROM etl_runs
ORDER BY duration_seconds DESC
LIMIT 10;

-- Failed runs with error messages
SELECT 
  started_at,
  error_message,
  records_processed
FROM etl_runs
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

### Data Maintenance

```sql
-- Clean old data (keep last 30 days)
DELETE FROM normalized_data 
WHERE created_at < CURRENT_DATE - INTERVAL '30 days';

-- Reset checkpoint for source
DELETE FROM etl_checkpoint WHERE source = 'api';

-- Clear old ETL runs (keep last 100)
DELETE FROM etl_runs 
WHERE id NOT IN (
  SELECT id FROM etl_runs 
  ORDER BY created_at DESC 
  LIMIT 100
);

-- Vacuum (optimize storage)
VACUUM ANALYZE normalized_data;
```

---

## Testing Guide

### Run All Tests

```bash
make test
```

### Run Specific Test File

```bash
docker-compose run --rm app pytest tests/test_etl.py -v
docker-compose run --rm app pytest tests/test_api.py -v
docker-compose run --rm app pytest tests/test_integration.py -v
```

### Run Specific Test

```bash
docker-compose run --rm app pytest tests/test_etl.py::test_normalize_api_data -v
```

### Run with Coverage

```bash
docker-compose run --rm app pytest tests/ --cov=src --cov-report=html
```

### Run Tests in Watch Mode

```bash
docker-compose run --rm app pytest tests/ -v --tb=short -x
```

### Run Only Unit Tests

```bash
docker-compose run --rm app pytest tests/ -m "not integration" -v
```

### Run Only Integration Tests

```bash
docker-compose run --rm app pytest tests/test_integration.py -v
```

---

## Docker Commands

### Build Image

```bash
# Build with default name
docker build -t etl-app:latest .

# Build with custom tag
docker build -t etl-app:v1.0.0 .
```

### Run Container

```bash
# Run container from image
docker run -d -p 8000:8000 -e DATABASE_URL=... etl-app:latest

# Run with shell
docker run -it etl-app:latest /bin/bash

# Run with volume mount
docker run -v $(pwd):/app -p 8000:8000 etl-app:latest
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# Start with logging
docker-compose up

# Stop services
docker-compose down

# Remove volumes too
docker-compose down -v

# Rebuild images
docker-compose build

# View logs
docker-compose logs -f

# Run command in container
docker-compose exec app python cli.py stats

# Run one-off command
docker-compose run --rm app python -c "import requests; print('OK')"
```

### Registry Operations

```bash
# Tag image for registry
docker tag etl-app:latest myregistry.azurecr.io/etl-app:latest

# Push to registry
docker push myregistry.azurecr.io/etl-app:latest

# Pull from registry
docker pull myregistry.azurecr.io/etl-app:latest
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
make logs

# Check container status
docker ps -a

# Inspect container
docker inspect etl_app

# Check database connectivity
docker-compose exec app python -c "from src.core.database import Database; print(Database.check_connection())"
```

### Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <PID> /F

# Kill process (Unix)
lsof -ti:8000 | xargs kill -9
```

### Database Issues

```bash
# Check database connectivity
docker-compose exec db pg_isready

# Check database size
docker-compose exec db psql -U postgres -d etl_db -c "SELECT pg_size_pretty(pg_database_size('etl_db'));"

# Check connections
docker-compose exec db psql -U postgres -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Fix corrupted indexes
docker-compose exec db psql -U postgres -d etl_db -c "REINDEX DATABASE etl_db;"
```

### Memory Issues

```bash
# Check container memory usage
docker stats etl_app

# Increase container memory limit
# Edit docker-compose.yml:
# services:
#   app:
#     deploy:
#       resources:
#         limits:
#           memory: 2G
```

### Connection Pool Issues

```bash
# Check pool status
docker-compose exec app python -c "from src.core.database import Database; print(Database._pool)"

# Increase pool size in src/core/config.py
DB_POOL_MAX_SIZE = 50  # Increase from 20
```

---

## Development Workflow

### 1. Make Code Changes

Edit files in `src/` directory

### 2. Reload Application

```bash
# If using docker-compose with --reload flag, changes auto-reload
# Otherwise, restart container:
docker-compose restart app
```

### 3. Run Tests

```bash
make test
```

### 4. View Logs

```bash
make logs
```

### 5. Test Changes

```bash
curl http://localhost:8000/data
```

### 6. Commit Changes

```bash
git add .
git commit -m "description of changes"
git push
```

---

## Performance Tuning

### Database Connection Pool

```python
# In src/core/config.py
DB_POOL_MIN_SIZE = 5      # Increase for more concurrent requests
DB_POOL_MAX_SIZE = 20     # Increase if pool exhaustion errors
```

### API Workers

```bash
# In docker-compose.yml, increase workers
uvicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Database Indexes

```sql
-- Add index on frequently queried columns
CREATE INDEX idx_normalized_data_source ON normalized_data(source);
CREATE INDEX idx_normalized_data_created ON normalized_data(created_at);
CREATE INDEX idx_normalized_data_name ON normalized_data(name);
```

### Query Optimization

```sql
-- Use EXPLAIN to analyze queries
EXPLAIN ANALYZE
SELECT * FROM normalized_data 
WHERE source = 'api' AND name ILIKE '%test%'
LIMIT 10;
```

---

## Monitoring & Debugging

### View All Metrics

```bash
docker-compose run --rm app python cli.py stats
```

### View ETL Runs

```bash
docker-compose exec db psql -U postgres -d etl_db \
  -c "SELECT * FROM etl_runs ORDER BY created_at DESC LIMIT 10;"
```

### Monitor in Real-Time

```bash
# Terminal 1: View logs
make logs

# Terminal 2: Run tests or make requests
curl http://localhost:8000/data

# Terminal 3: Check database
make db-shell
```

### Debug API Requests

```python
# Add this to src/api/main.py for debugging
import logging
logger = logging.getLogger(__name__)

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
```

---

## Useful Scripts

### Backup Database

```bash
docker-compose exec db pg_dump -U postgres etl_db > backup.sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U postgres -d etl_db < backup.sql
```

### Clear All Data

```bash
make down
make clean
make up
```

### Full Health Check

```bash
#!/bin/bash
echo "API Health:"
curl http://localhost:8000/health
echo -e "\n\nDatabase Tables:"
docker-compose exec db psql -U postgres -d etl_db -c "\dt"
echo -e "\n\nData Count:"
docker-compose exec db psql -U postgres -d etl_db -c "SELECT source, COUNT(*) FROM normalized_data GROUP BY source;"
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Container won't start | Check logs: `make logs` |
| Database connection fails | Verify DB is healthy: `docker-compose ps` |
| Port in use | Kill process using port: `lsof -ti:8000 \| xargs kill -9` |
| Tests fail | Rebuild: `make clean && make build && make test` |
| Slow API | Check connection pool, add indexes |
| High memory | Reduce worker count, increase container limit |
| Data not appearing | Check ETL logs, verify checkpoints |

---

## References

- FastAPI Docs: https://fastapi.tiangolo.com
- PostgreSQL Docs: https://www.postgresql.org/docs
- Docker Docs: https://docs.docker.com
- Pytest Docs: https://docs.pytest.org
- Pydantic Docs: https://docs.pydantic.dev

---

Happy coding! 🚀
