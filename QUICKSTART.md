# 🚀 Quick Start Guide

## What You Got

A complete, production-ready ETL system that:
- ✅ Ingests data from API + CSV
- ✅ Stores data in PostgreSQL
- ✅ Normalizes with schema validation
- ✅ Prevents duplicate processing with checkpoints
- ✅ Exposes REST API with pagination
- ✅ Tracks ETL run statistics
- ✅ Fully Dockerized and tested

## 5-Minute Setup

### 1. Start Everything
```bash
cd backenddevelopment
make up
```

Wait 30 seconds for database to initialize...

### 2. Verify It Works
```bash
# Health check
curl http://localhost:8000/health

# Get data (paginated)
curl http://localhost:8000/data?page=1&page_size=5

# Get statistics
curl http://localhost:8000/stats
```

### 3. Run Tests
```bash
make test
```

### 4. Stop Everything
```bash
make down
```

## What's Running

| Service | Port | Details |
|---------|------|---------|
| API | 8000 | FastAPI - `/data`, `/health`, `/stats` |
| Database | 5432 | PostgreSQL - Stores all data |

## Project Structure

```
src/
├── api/main.py          ← REST endpoints
├── etl/pipeline.py      ← Data ingestion logic
├── schemas/models.py    ← Data validation
└── core/
    ├── database.py      ← DB connection pool
    └── config.py        ← Configuration
tests/
├── test_etl.py          ← ETL tests
└── test_api.py          ← API tests
```

## Key Features

### P0 - Foundation (✅ Complete)
- [x] API + CSV ingestion
- [x] PostgreSQL storage
- [x] Schema normalization
- [x] Incremental processing
- [x] REST API with filtering
- [x] Health checks & statistics
- [x] Docker + Makefile
- [x] Test suite

### P1 - Growth (📝 Ready to Extend)
- [ ] Add 3rd data source (RSS, webhook, etc)
- [ ] Enhanced checkpoint recovery
- [ ] Advanced statistics
- [ ] More comprehensive tests

### P2 - Differentiator (🚀 Optional)
- [ ] Schema drift detection
- [ ] Failure injection + recovery
- [ ] Rate limiting + backoff
- [ ] Observability layer
- [ ] Cloud deployment
- [ ] Anomaly detection

## Common Tasks

### View Logs
```bash
make logs
```

### Access Database
```bash
make db-shell
```

### Add a New Data Source
Edit `src/etl/pipeline.py` and add:
```python
def ingest_new_source(self):
    # Your ingestion logic
    data = fetch_data()
    self.store_raw_data('new_source', data)
    normalized = self.normalize_data('new_source', data)
    self.store_normalized_data(normalized)
    self.update_checkpoint('new_source', ...)
```

### Modify Data Schema
Edit `src/schemas/models.py` DataRecord class.

### Run Local Development
```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/etl_db
python -m uvicorn src.api.main:app --reload
```

## API Examples

### Get Data with Filtering
```bash
# Filter by source
curl http://localhost:8000/data?source=api

# Search
curl http://localhost:8000/data?search=test

# Pagination
curl http://localhost:8000/data?page=2&page_size=20
```

### Check System Health
```bash
curl -i http://localhost:8000/health
```

### Get Statistics
```bash
curl http://localhost:8000/stats
```

## Testing

Run all tests:
```bash
make test
```

Run specific test:
```bash
docker-compose run --rm app pytest tests/test_api.py::test_health_check_healthy -v
```

## Database

### Tables Created
- `raw_api_data` - Raw API responses
- `raw_csv_data` - Raw CSV records
- `normalized_data` - Unified schema
- `etl_checkpoint` - Resumable progress
- `etl_runs` - Execution metrics

### Sample Queries
```sql
-- View data counts
SELECT source, COUNT(*) FROM normalized_data GROUP BY source;

-- Check last ETL run
SELECT * FROM etl_runs ORDER BY created_at DESC LIMIT 1;

-- View checkpoints
SELECT * FROM etl_checkpoint;
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `docker kill <container>` then `make up` |
| Database won't start | `make clean` then `make up` |
| Tests failing | `make build` then `make test` |
| Can't connect | Check `make logs` |

## Next Steps

1. **Try extending it**: Add RSS feeds or webhooks
2. **Deploy it**: AWS Lambda + EventBridge or Cloud Run
3. **Enhance it**: Add rate limiting, metrics, schema detection
4. **Monitor it**: Integrate with Prometheus or CloudWatch

## Files to Know

| File | Purpose |
|------|---------|
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Multi-container orchestration |
| `Makefile` | Build automation commands |
| `.env` | Environment variables |
| `requirements.txt` | Python dependencies |

## Commands Cheat Sheet

```bash
make up           # Start
make down         # Stop
make logs         # View logs
make test         # Run tests
make clean        # Clean up
make build        # Rebuild image
make shell        # Bash in container
make db-shell     # PostgreSQL shell
```

## Architecture Simplified

```
API Source ─┐
            ├─► ETL Pipeline ──► PostgreSQL ──► FastAPI ──► Your App
CSV Source ─┘
```

Data flows through:
1. **Fetch** from sources
2. **Store** raw data
3. **Normalize** to unified schema
4. **Query** via REST API

---

**Built for Learning & Production**

This system demonstrates:
- Clean architecture patterns
- Database design best practices
- API design principles
- Docker containerization
- Testing strategies
- Production readiness

Happy building! 🎉
