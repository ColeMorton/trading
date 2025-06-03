# Trading Application Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev build test clean docker-build docker-up docker-down docker-logs setup-db migrate backup restore frontend-install frontend-dev frontend-build frontend-codegen frontend-test test-fullstack dev-fullstack lint-help lint-black lint-isort lint-flake8 lint-mypy lint-pylint lint-bandit lint-vulture format-black format-isort lint-python format-python security-scan find-dead-code lint-all pre-commit-install pre-commit-run

# Default target
help:
	@echo "Trading Application - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install dependencies using Poetry"
	@echo "  dev         - Start development server"
	@echo "  test        - Run test suite"
	@echo "  clean       - Clean temporary files"
	@echo "  lint-help   - Show all linting commands"
	@echo "  lint-all    - Run all linters and formatters"
	@echo ""
	@echo "Frontend:"
	@echo "  frontend-install - Install frontend dependencies"
	@echo "  frontend-dev     - Start frontend development server"
	@echo "  frontend-build   - Build frontend for production"
	@echo "  frontend-codegen - Generate GraphQL types"
	@echo "  frontend-test    - Run frontend E2E tests (requires dev servers)"
	@echo "  test-fullstack   - Run E2E tests with automatic server startup"
	@echo "  dev-fullstack    - Start both backend and frontend"
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
	@echo "  make check-deps         # Check what's needed"
	@echo "  make install-db         # Install databases locally"
	@echo "  make frontend-install   # Install frontend dependencies"
	@echo "  make dev-fullstack      # Start both backend and frontend"
	@echo "  make docker-up          # Or use Docker (requires installation)"

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

# Frontend commands
frontend-check-deps:
	@echo "Checking frontend dependencies..."
	@command -v node >/dev/null 2>&1 && echo "✅ Node.js is installed" || echo "❌ Node.js is required - install from https://nodejs.org"
	@command -v npm >/dev/null 2>&1 && echo "✅ npm is installed" || echo "❌ npm is required (comes with Node.js)"
	@test -f app/frontend/sensylate/package.json && echo "✅ Frontend package.json found" || echo "❌ Frontend package.json not found"

frontend-install: frontend-check-deps
	@echo "Installing frontend dependencies..."
	cd app/frontend/sensylate && npm install
	@echo "✅ Frontend dependencies installed"

frontend-codegen:
	@echo "Generating GraphQL types..."
	cd app/frontend/sensylate && npm run codegen
	@echo "✅ GraphQL types generated"

frontend-dev:
	@echo "Starting frontend development server..."
	@echo "Frontend will be available at: http://localhost:5173"
	cd app/frontend/sensylate && npm run dev

frontend-build:
	@echo "Building frontend for production..."
	cd app/frontend/sensylate && npm run build
	@echo "✅ Frontend build complete"

frontend-build-pwa:
	@echo "Building frontend PWA for production..."
	cd app/frontend/sensylate && npm run build:pwa
	@echo "✅ Frontend PWA build complete"

frontend-test:
	@echo "Running frontend E2E tests..."
	@echo "⚠️  Prerequisites: Both backend and frontend servers must be running"
	@echo "   Backend: http://localhost:8000 (make dev-local)"
	@echo "   Frontend: http://localhost:5173 (make frontend-dev)"
	@echo ""
	@echo "Checking server availability..."
	@curl -f http://localhost:8000/health >/dev/null 2>&1 || { echo "❌ Backend not running. Start with 'make dev-local'"; exit 1; }
	@curl -f http://localhost:5173 >/dev/null 2>&1 || { echo "❌ Frontend not running. Start with 'make frontend-dev'"; exit 1; }
	@echo "✅ Both servers are running, proceeding with tests..."
	cd app/frontend/sensylate && npm run test:e2e
	@echo "✅ Frontend tests complete"

frontend-lint:
	@echo "Running frontend linting..."
	cd app/frontend/sensylate && npm run lint
	@echo "✅ Frontend linting complete"

frontend-clean:
	@echo "Cleaning frontend build artifacts..."
	cd app/frontend/sensylate && rm -rf dist node_modules/.vite
	@echo "✅ Frontend cleaned"

# Full-stack development
dev-fullstack: start-local frontend-install
	@echo "Starting full-stack development environment..."
	@echo "Backend API: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "GraphQL Playground: http://localhost:8000/graphql"
	@echo ""
	@echo "Starting backend in background..."
	poetry run python -m app.api.run --reload &
	@echo "Waiting for backend to start..."
	@sleep 3
	@echo "Starting frontend..."
	cd app/frontend/sensylate && npm run dev

# Setup commands for new developers
setup-frontend: frontend-install frontend-codegen
	@echo "✅ Frontend setup complete!"
	@echo "Run 'make frontend-dev' to start development server"

setup-fullstack: install setup-db frontend-install frontend-codegen
	@echo "✅ Full-stack setup complete!"
	@echo "Run 'make dev-fullstack' to start both backend and frontend"

# Complete test workflow with server startup
test-fullstack:
	@echo "Running full-stack tests with automatic server startup..."
	@echo "Starting backend server..."
	poetry run python -m app.api.run --reload &
	@echo "Waiting for backend to start..."
	@sleep 5
	@echo "Starting frontend server..."
	cd app/frontend/sensylate && npm run dev &
	@echo "Waiting for frontend to start..."
	@sleep 5
	@echo "Running tests..."
	cd app/frontend/sensylate && npm run test:e2e
	@echo "Stopping servers..."
	@pkill -f "app.api.run" || true
	@pkill -f "vite" || true
	@echo "✅ Full-stack tests complete!"

# Linting and code quality commands
lint-help:
	@echo "Linting and Code Quality Commands:"
	@echo ""
	@echo "Individual Linters (check only):"
	@echo "  lint-black   - Check code formatting with Black"
	@echo "  lint-isort   - Check import sorting with isort"
	@echo "  lint-flake8  - Check code style with Flake8"
	@echo "  lint-mypy    - Check type hints with mypy"
	@echo "  lint-pylint  - Check code quality with pylint"
	@echo "  lint-bandit  - Security vulnerability scanning"
	@echo "  lint-vulture - Find dead code"
	@echo ""
	@echo "Code Formatters (auto-fix):"
	@echo "  format-black - Auto-format code with Black"
	@echo "  format-isort - Auto-sort imports with isort"
	@echo ""
	@echo "Aggregate Commands:"
	@echo "  lint-python    - Run all Python linters (check only)"
	@echo "  format-python  - Auto-format all Python code"
	@echo "  security-scan  - Run security scanning with bandit"
	@echo "  find-dead-code - Find unused code with vulture"
	@echo "  lint-all       - Run all linters and formatters"
	@echo ""
	@echo "Pre-commit Hooks:"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  pre-commit-run     - Run pre-commit hooks manually"
	@echo ""
	@echo "Examples:"
	@echo "  make lint-python       # Check all code quality issues"
	@echo "  make format-python     # Auto-fix formatting issues"
	@echo "  make lint-all          # Complete code quality check"

# Individual Python linters (check only)
lint-black:
	@echo "Checking code formatting with Black..."
	poetry run black --check --diff app tests
	@echo "✅ Black check complete"

lint-isort:
	@echo "Checking import sorting with isort..."
	poetry run isort --check-only --diff app tests
	@echo "✅ isort check complete"

lint-flake8:
	@echo "Checking code style with Flake8..."
	poetry run flake8 app tests
	@echo "✅ Flake8 check complete"

lint-mypy:
	@echo "Checking type hints with mypy..."
	poetry run mypy app tests
	@echo "✅ mypy check complete"

lint-pylint:
	@echo "Checking code quality with pylint..."
	poetry run pylint app tests
	@echo "✅ pylint check complete"

lint-bandit:
	@echo "Scanning for security vulnerabilities with bandit..."
	poetry run bandit -r app -ll
	@echo "✅ Security scan complete"

lint-vulture:
	@echo "Finding dead code with vulture..."
	poetry run vulture app tests --min-confidence 80
	@echo "✅ Dead code check complete"

# Python formatters (auto-fix)
format-black:
	@echo "Auto-formatting code with Black..."
	poetry run black app tests
	@echo "✅ Black formatting complete"

format-isort:
	@echo "Auto-sorting imports with isort..."
	poetry run isort app tests
	@echo "✅ isort formatting complete"

# Aggregate Python commands
lint-python: lint-black lint-isort lint-flake8 lint-mypy
	@echo "✅ All Python linting checks complete"

format-python: format-isort format-black
	@echo "✅ All Python formatting complete"

# Security and code quality scanning
security-scan: lint-bandit
	@echo "✅ Security scanning complete"

find-dead-code: lint-vulture
	@echo "✅ Dead code detection complete"

# Combined lint command - runs all checks and fixes
lint-all:
	@echo "Running all linters and formatters..."
	@echo ""
	@echo "Step 1: Auto-formatting code..."
	@$(MAKE) format-python
	@echo ""
	@echo "Step 2: Running linting checks..."
	@$(MAKE) lint-python
	@echo ""
	@echo "Step 3: Running additional code quality checks..."
	@$(MAKE) lint-pylint || true  # Continue even if pylint finds issues
	@echo ""
	@echo "Step 4: Security scanning..."
	@$(MAKE) security-scan || true  # Continue even if security issues found
	@echo ""
	@echo "Step 5: Dead code detection..."
	@$(MAKE) find-dead-code || true  # Continue even if dead code found
	@echo ""
	@echo "✅ All linting and formatting complete!"

# Pre-commit hook commands
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	poetry run pre-commit install
	@echo "✅ Pre-commit hooks installed"

pre-commit-run:
	@echo "Running pre-commit hooks on all files..."
	poetry run pre-commit run --all-files
	@echo "✅ Pre-commit hooks complete"
