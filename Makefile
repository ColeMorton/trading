# Trading Application Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev build test clean docker-build docker-up docker-down docker-logs setup-db migrate backup restore

# Default target
help:
	@echo "Trading Application - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install dependencies using Poetry"
	@echo "  dev         - Start development server"
	@echo "  test        - Run test suite"
	@echo "  clean       - Clean temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up   - Start all services with Docker Compose"
	@echo "  docker-down - Stop all services"
	@echo "  docker-logs - View service logs"
	@echo ""
	@echo "Database:"
	@echo "  setup-db    - Complete database setup (schema + migration)"
	@echo "  test-db     - Test database setup and connectivity"
	@echo "  migrate     - Run data migration only"
	@echo "  backup      - Create database backup"
	@echo "  restore     - Restore from backup (requires BACKUP_FILE)"
	@echo ""
	@echo "Local Development (without Docker):"
	@echo "  check-deps  - Check required dependencies"
	@echo "  install-db  - Install PostgreSQL and Redis locally"
	@echo "  start-local - Start local PostgreSQL and Redis services"
	@echo "  dev-local   - Start API server with local database"
	@echo ""
	@echo "Examples:"
	@echo "  make check-deps     # Check what's needed"
	@echo "  make install-db     # Install databases locally"
	@echo "  make dev-local      # Start without Docker"
	@echo "  make docker-up      # Or use Docker (requires installation)"

# Development commands
install:
	poetry install

dev:
	poetry run python -m app.api.run --reload

test:
	poetry run pytest

test-db:
	poetry run python scripts/test_database_setup.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage

# Docker commands
check-docker:
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ docker-compose is not installed. It should come with Docker Desktop."; exit 1; }
	@echo "✅ Docker and docker-compose are available"

docker-build: check-docker
	docker-compose build

docker-up: check-docker
	docker-compose up -d
	@echo "Services starting..."
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"
	@echo "PgAdmin: http://localhost:5050 (profile: admin)"

docker-down: check-docker
	docker-compose down

docker-logs: check-docker
	docker-compose logs -f

docker-clean: check-docker
	docker-compose down -v
	docker system prune -f

# Local development commands (without Docker)
check-deps:
	@echo "Checking system dependencies..."
	@command -v python3 >/dev/null 2>&1 && echo "✅ Python 3 is installed" || echo "❌ Python 3 is required"
	@command -v poetry >/dev/null 2>&1 && echo "✅ Poetry is installed" || echo "❌ Poetry is required - install from https://python-poetry.org"
	@command -v psql >/dev/null 2>&1 && echo "✅ PostgreSQL client is installed" || echo "⚠️  PostgreSQL client not found - install with 'make install-db'"
	@command -v redis-cli >/dev/null 2>&1 && echo "✅ Redis client is installed" || echo "⚠️  Redis client not found - install with 'make install-db'"
	@command -v brew >/dev/null 2>&1 && echo "✅ Homebrew is available" || echo "⚠️  Homebrew recommended for easy installation"

install-db:
	@echo "Installing PostgreSQL and Redis locally..."
	@if command -v brew >/dev/null 2>&1; then \
		echo "Using Homebrew to install databases..."; \
		brew install postgresql@15 redis; \
		echo "✅ Databases installed"; \
	else \
		echo "❌ Homebrew not found. Please install manually:"; \
		echo "PostgreSQL: https://www.postgresql.org/download/"; \
		echo "Redis: https://redis.io/download"; \
	fi

start-local:
	@echo "Starting local database services..."
	@if command -v brew >/dev/null 2>&1; then \
		echo "Starting PostgreSQL..."; \
		brew services start postgresql@15 || echo "⚠️  PostgreSQL service start failed"; \
		echo "Starting Redis..."; \
		brew services start redis || echo "⚠️  Redis service start failed"; \
		echo "✅ Local services started"; \
	else \
		echo "❌ Please start PostgreSQL and Redis manually"; \
	fi

stop-local:
	@echo "Stopping local database services..."
	@if command -v brew >/dev/null 2>&1; then \
		brew services stop postgresql@15; \
		brew services stop redis; \
		echo "✅ Local services stopped"; \
	else \
		echo "❌ Please stop PostgreSQL and Redis manually"; \
	fi

dev-local: start-local
	@echo "Starting API server with local database..."
	@echo "Make sure your .env file points to local services:"
	@echo "DATABASE_URL=postgresql://$(USER)@localhost:5432/trading_db"
	@echo "REDIS_URL=redis://localhost:6379"
	poetry run python -m app.api.run --reload

# Database commands
setup-db:
	poetry run python scripts/setup_database.py

migrate:
	poetry run python app/database/migrations.py

backup:
	poetry run python app/database/backup.py create

restore:
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "Error: BACKUP_FILE is required"; \
		echo "Usage: make restore BACKUP_FILE=path/to/backup.tar.gz"; \
		exit 1; \
	fi
	poetry run python app/database/backup.py restore $(BACKUP_FILE) --force

list-backups:
	poetry run python app/database/backup.py list

cleanup-backups:
	poetry run python app/database/backup.py cleanup

# Prisma commands
prisma-generate:
	poetry run python -m prisma generate

prisma-push:
	poetry run python -m prisma db push

prisma-studio:
	poetry run python -m prisma studio

# Combined workflows
fresh-start: docker-clean docker-build docker-up setup-db
	@echo "Fresh environment setup complete!"

quick-test: docker-up test-db
	@echo "Quick validation complete!"

# Production commands
build-prod:
	docker-compose -f docker-compose.prod.yml build

deploy-prod:
	docker-compose -f docker-compose.prod.yml up -d

# Health checks
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "API: DOWN"
	@curl -f http://localhost:8000/health/database || echo "Database: DOWN"
	@curl -f http://localhost:3000/health || echo "Frontend: DOWN"

# Monitoring
logs-api:
	docker-compose logs -f api

logs-db:
	docker-compose logs -f postgres

logs-redis:
	docker-compose logs -f redis

logs-frontend:
	docker-compose logs -f frontend