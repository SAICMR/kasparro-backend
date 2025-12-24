# Copilot / AI Agent Instructions

This file gives targeted, actionable guidance for an AI code agent to be productive in this repository.

Summary
- Purpose: ETL service that ingests JSON from an API and a local CSV, normalizes data, stores it in a DB, and exposes a FastAPI surface.
- Runtime: FastAPI + Uvicorn, local default DB is SQLite (fallback) with optional PostgreSQL support.

Big picture (what to know first)
- Orchestrator: `src/etl/pipeline.py` — implements ingestion (API + CSV), normalization, deduplication (canonical_id), and persistence.
- API surface: `src/api/main.py` — FastAPI app, startup triggers non-blocking initial ETL (threading), endpoints: `/health`, `/data`, `/stats`, `/etl/run`, `/data` (POST).
- DB abstraction: `src/core/database.py` (SQLite) and `src/core/database_postgresql.py` (Postgres). Code assumes a `Database` class with `initialize()`, `execute_query()`, `execute_update()`, `check_connection()`, `close()`.
- Config: `src/core/config.py` – environment-driven (`DATABASE_URL`, `API_HOST`, `CSV_PATH`, `API_KEY`, `ETL_INTERVAL`, `LOG_LEVEL`).

Key patterns & gotchas (project-specific)
- SQL parameter style: application code uses `%s` placeholders and Postgres-style SQL (e.g. `ON CONFLICT`). The SQLite `Database` implementation normalizes `%s` → `?` and some conflict syntax. Prefer using `%s` in code to keep portability.
- Pydantic v2 models: `src/schemas/models.py` uses Pydantic v2. Use `from_attributes` config or validate with explicit fields; tests construct `DataRecord` directly.
- Tests mock the DB: unit tests patch `Database` (see `tests/test_api.py` and `tests/test_etl.py`). When updating DB behavior, adjust tests to mock/expect new calls.
- Non-blocking startup: `src/api/main.py` starts an initial ETL in a daemon thread—avoid long-blocking work on startup and be cautious when changing this behavior.
- CSV fallback: If `CSV_PATH` is missing, `ETLPipeline.ingest_csv_data` returns sample data — tests rely on this fallback.

Typical developer workflows
- Install deps: `python -m pip install -r requirements.txt`
- Run locally (dev):
  - Start app: `uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`
  - Environment: set `CSV_PATH`, `API_HOST`, `DATABASE_URL` (optional), `API_KEY`, `LOG_LEVEL`.
- Run tests: `pytest -q` (tests mock external services; they don't require a real DB running).

Integration & external points
- External API: default `API_HOST` is `http://jsonplaceholder.typicode.com` and ETL calls `${API_HOST}/posts` by default.
- Database: default SQLite file `etl_local.db` in repo root. To use Postgres, provide a proper `DATABASE_URL` and consider swapping import to `src.core.database_postgresql` if desired.
- Network calls: `requests` is used directly in `ETLPipeline.ingest_api_data()` (unit tests patch `requests.get`).

When editing code (practical rules)
- Keep SQL portable: continue using `%s` placeholders and Postgres-friendly constructs; let `Database` implementations handle translation.
- Add or change DB schema in `ETLPipeline.initialize_schema()` so both DB implementations remain compatible (data types are generic; avoid DB-specific DDL where possible).
- When adding endpoints, follow existing response models in `src/schemas/models.py` and update tests in `tests/` to patch `Database` accordingly.
- Logging: call `setup_logging(LOG_LEVEL)` at process entry (see `src/api/main.py`). Use structured messages similar to existing code.

Quick references (files to open first)
- `src/etl/pipeline.py` — ETL flow, normalization, dedupe, SQL usage
- `src/api/main.py` — FastAPI endpoints, startup/shutdown, trigger patterns
- `src/core/database.py` and `src/core/database_postgresql.py` — DB portability layer
- `src/schemas/models.py` — Pydantic models used across API and ETL
- `tests/` — unit tests show how components are mocked and expected behavior

If something is unclear
- Ask which runtime to target (SQLite vs Postgres) — SQL and schema choices depend on it.
- Point to a failing test or a stack trace; unit tests are a reliable safety net because they mock external integrations.

Next step: please review for missing details (CI commands, deployment steps, or other integration keys) and I will iterate.
