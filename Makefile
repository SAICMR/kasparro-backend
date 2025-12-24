.PHONY: help up down test logs build clean lint

help:
	@echo "Available commands:"
	@echo "  make up       - Start Docker containers"
	@echo "  make down     - Stop Docker containers"
	@echo "  make test     - Run test suite"
	@echo "  make logs     - View app logs"
	@echo "  make build    - Build Docker image"
	@echo "  make clean    - Clean up Docker resources"
	@echo "  make lint     - Run linting checks"

up:
	docker-compose up -d
	@echo "✓ Services started. API available at http://localhost:8000"
	@echo "✓ Health check: curl http://localhost:8000/health"

down:
	docker-compose down

logs:
	docker-compose logs -f app

build:
	docker-compose build

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

test:
	docker-compose run --rm app python -m pytest tests/ -v --tb=short

lint:
	docker-compose run --rm app python -m flake8 src/ tests/ --max-line-length=120 || true

shell:
	docker-compose run --rm app /bin/bash

db-shell:
	docker-compose exec db psql -U postgres -d etl_db
