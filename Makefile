# Trading Application Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev build test clean docker-build docker-up docker-down docker-logs setup-db migrate backup restore frontend-install frontend-dev frontend-build frontend-codegen frontend-test test-fullstack dev-fullstack lint-help lint-ruff lint-mypy lint-pylint lint-bandit lint-vulture format-ruff lint-python format-python security-scan find-dead-code lint-all pre-commit-install pre-commit-run pre-commit-update verify-commit verify-commit-quick verify-commit-security git-configure git-unconfigure workflow-help workflow-install workflow-list workflow-test workflow-ci workflow-full

# Default target
help:
	@echo "Trading Application - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     - Install dependencies using Poetry"
	@echo "  dev         - Start development server"
	@echo "  test        - Run unified test suite (CI configuration)"
	@echo "  test-quick  - Run quick tests for development"
	@echo "  test-full   - Run full test suite with coverage"
	@echo "  clean       - Clean temporary files"
	@echo "  lint-help   - Show all linting commands"
	@echo "  lint-all    - Run all linters and formatters"
	@echo ""
	@echo "Workflow Testing:"
	@echo "  workflow-help    - Show workflow testing commands"
	@echo "  workflow-install - Install act for local workflow testing"
	@echo "  workflow-list    - List all workflows and jobs"
	@echo "  workflow-test    - Quick workflow validation"
	@echo "  workflow-ci      - Full CI simulation (no act required)"
	@echo "  workflow-full    - Complete workflow test with act"
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
	@echo "  e2e-up      - Start E2E test stack (API+worker+db+redis)"
	@echo "  e2e-down    - Stop E2E test stack and remove volumes"
	@echo "  e2e-test    - Run Python E2E tests against containerized API"
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

# Unified test execution - delegates to comprehensive test infrastructure
test:
	@echo "🧪 Running unified test suite..."
	@echo "📊 Using Phase 3 consolidated test infrastructure"
	poetry run python tests/run_unified_tests.py ci -v
	@echo "✅ All tests completed successfully!"
	@echo "📈 View detailed results: cat test_results.json"

# Quick test for development
test-quick:
	@echo "🚀 Running quick test suite for development..."
	poetry run python tests/run_unified_tests.py quick -v

# Full test suite with coverage
test-full:
	@echo "🚀 Running full test suite with coverage..."
	poetry run python tests/run_unified_tests.py all -c --save test_results.json
	@echo "📊 Coverage report available at: htmlcov/index.html"

# Individual test categories (delegating to unified runner)
# Unit tests run natively - no services needed
test-unit:
	@echo "Running unit tests (no services needed)..."
	poetry run python tests/run_unified_tests.py unit -v

# Integration tests need services - auto-start them
test-integration: services-up
	@echo "Running integration tests with Docker services..."
	poetry run python tests/run_unified_tests.py integration -v

# API tests need services - auto-start them
test-api: services-up
	@echo "Running API tests with Docker services..."
	poetry run python tests/run_unified_tests.py api -v

# E2E tests need services - auto-start them
test-e2e: services-up
	@echo "Running E2E tests with Docker services..."
	poetry run python tests/run_unified_tests.py e2e -v

# Legacy pytest command for direct pytest access
test-pytest:
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

# Service management for local development (PostgreSQL + Redis only)
services-up: check-docker
	@echo "Starting PostgreSQL and Redis for local development..."
	docker-compose -f docker-compose.services.yml up -d
	@echo "✅ Services started"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

services-down: check-docker
	@echo "Stopping services..."
	docker-compose -f docker-compose.services.yml down

services-logs: check-docker
	docker-compose -f docker-compose.services.yml logs -f

services-clean: check-docker
	@echo "Stopping services and removing data volumes..."
	docker-compose -f docker-compose.services.yml down -v
	@echo "✅ Services stopped and data volumes removed"

# Full Docker deployment commands
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

# E2E stack for API black-box tests
e2e-up: check-docker
	@echo "Starting E2E stack (API, worker, Postgres, Redis)..."
	docker compose -f docker-compose.e2e.yml up -d
	@echo "✅ E2E stack started: http://localhost:8000"

e2e-down: check-docker
	@echo "Stopping E2E stack and removing volumes..."
	docker compose -f docker-compose.e2e.yml down -v

e2e-test: e2e-up
	@echo "Waiting for API to become healthy..."
	@bash -c 'for i in {1..180}; do if curl -sfL http://localhost:8000/health/ >/dev/null; then exit 0; fi; sleep 1; done; echo "API did not become healthy in time"; exit 1'
	poetry run pytest -q tests/e2e/test_sweep_e2e.py || ( $(MAKE) e2e-down; exit 1 )
	$(MAKE) e2e-down

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

# Development with Docker services (native app + Docker services)
dev-with-services: services-up
	@echo "Starting API server with Docker services..."
	@echo "PostgreSQL: postgresql://trading_user:changeme@localhost:5432/trading_db"
	@echo "Redis: redis://localhost:6379"
	poetry run python -m app.api.run --reload

# Database commands
setup-db:
	poetry run python scripts/setup_database.py

migrate:
	poetry run alembic upgrade head

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
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "⚠️  CRITICAL: All tools run via Poetry"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "❌ WRONG:  ruff check ."
	@echo "✅ RIGHT:  poetry run ruff check ."
	@echo "✅ BETTER: make lint-ruff"
	@echo ""
	@echo "Linting and Code Quality Commands:"
	@echo ""
	@echo "Individual Linters (check only):"
	@echo "  lint-ruff    - Check code with Ruff (format, imports, linting)"
	@echo "  lint-mypy    - Check type hints with mypy"
	@echo "  lint-pylint  - Check code quality with pylint"
	@echo "  lint-bandit  - Security vulnerability scanning"
	@echo "  lint-vulture - Find dead code"
	@echo ""
	@echo "Code Formatters (auto-fix):"
	@echo "  format-ruff    - Auto-format and fix issues with Ruff"
	@echo ""
	@echo "Aggregate Commands:"
	@echo "  lint-python    - Run all Python linters (check only)"
	@echo "  format-python  - Auto-format all Python code"
	@echo "  security-scan  - Run security scanning with bandit"
	@echo "  find-dead-code - Find unused code with vulture"
	@echo "  lint-all       - Run all linters and formatters"
	@echo ""
	@echo "Pre-commit & Security:"
	@echo "  pre-commit-install     - Install pre-commit hooks (commit + push)"
	@echo "  pre-commit-run         - Run pre-commit hooks manually"
	@echo "  pre-commit-update      - Update hooks to latest versions"
	@echo "  verify-commit          - Comprehensive commit verification"
	@echo "  verify-commit-quick    - Quick verification (critical checks only)"
	@echo "  verify-commit-security - Security checks only"
	@echo "  git-configure          - Configure git (commit template, hooks)"
	@echo ""
	@echo "Examples:"
	@echo "  make lint-python       # Check all code quality issues"
	@echo "  make format-python     # Auto-fix formatting issues"
	@echo "  make lint-all          # Complete code quality check"
	@echo "  make lint-ruff         # Quick modern linting with Ruff"

# Individual Python linters (check only)
lint-ruff:
	@echo "Checking code with Ruff (format, imports, linting)..."
	poetry run ruff format --check app tests
	poetry run ruff check app tests
	@echo "✅ Ruff check complete"

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
	poetry run bandit -r app -ll --exclude app/trading_bot/trendspider/
	@echo "✅ Security scan complete"

lint-vulture:
	@echo "Finding dead code with vulture..."
	poetry run vulture app tests --min-confidence 80
	@echo "✅ Dead code check complete"

# Python formatters (auto-fix)
format-ruff:
	@echo "Auto-formatting and fixing issues with Ruff..."
	poetry run ruff format app tests
	poetry run ruff check --fix app tests
	@echo "✅ Ruff formatting and auto-fix complete"

# Aggregate Python commands
lint-python: lint-ruff lint-mypy
	@echo "✅ All Python linting checks complete"

format-python: format-ruff
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
	poetry run pre-commit install --hook-type pre-push
	@echo "✅ Pre-commit hooks installed for commit and push"
	@echo ""
	@echo "📋 Next steps:"
	@echo "  1. Configure git commit template: make git-configure"
	@echo "  2. Read security policy: cat SECURITY.md"
	@echo "  3. Test hooks: make pre-commit-run"

pre-commit-run:
	@echo "Running pre-commit hooks on all files..."
	poetry run pre-commit run --all-files
	@echo "✅ Pre-commit hooks complete"

pre-commit-update:
	@echo "Updating pre-commit hooks to latest versions..."
	poetry run pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated"

# Verification commands
verify-commit:
	@echo "Running comprehensive commit verification..."
	@./scripts/verify-commit.sh

verify-commit-quick:
	@echo "Running quick verification checks..."
	@./scripts/verify-commit.sh --quick

verify-commit-security:
	@echo "Running security-only checks..."
	@./scripts/verify-commit.sh --security-only

# Git configuration
git-configure:
	@echo "Configuring git settings for this repository..."
	git config commit.template .gitmessage
	git config core.hooksPath .git/hooks
	@echo "✅ Git configured successfully"
	@echo ""
	@echo "Configured settings:"
	@echo "  - Commit template: .gitmessage"
	@echo "  - Hooks path: .git/hooks"
	@echo ""
	@echo "Try 'git commit' to see the new commit template!"

git-unconfigure:
	@echo "Removing git configuration..."
	git config --unset commit.template || true
	@echo "✅ Git configuration removed"

# Code quality improvement (gradual fix)
quality-analyze:
	@echo "Analyzing code quality issues..."
	python scripts/fix_code_quality.py --analyze

quality-fix-safe:
	@echo "Auto-fixing safe issues..."
	python scripts/fix_code_quality.py --fix-safe

quality-track:
	@echo "Tracking code quality progress..."
	python scripts/fix_code_quality.py --track

quality-status:
	@echo "Quick code quality status..."
	python scripts/fix_code_quality.py

# Workflow Testing Commands
workflow-help:
	@echo "GitHub Workflow Testing Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  workflow-install  - Install act for local workflow testing"
	@echo "  workflow-setup    - Setup workflow testing environment"
	@echo ""
	@echo "Quick Testing:"
	@echo "  workflow-list     - List all workflows and jobs"
	@echo "  workflow-test     - Quick workflow syntax validation"
	@echo "  workflow-ci       - Full CI simulation without act (uses Docker Compose)"
	@echo ""
	@echo "Advanced Testing (requires act):"
	@echo "  workflow-full     - Run complete workflow with act"
	@echo "  workflow-lint     - Test lint job with act"
	@echo "  workflow-backend  - Test backend job with act"
	@echo "  workflow-ma-cross - Test MA Cross workflow with act"
	@echo ""
	@echo "Custom Testing:"
	@echo "  Run specific workflow: ./scripts/test-workflow-with-act.sh --workflow ci-cd.yml --job lint"
	@echo "  Run with event:       ./scripts/test-workflow-with-act.sh --event push --event-file .github/workflows/events/push-develop.json"
	@echo ""
	@echo "Documentation:"
	@echo "  See docs/development/WORKFLOW_TESTING.md for detailed guide"

workflow-install:
	@echo "Installing act for local GitHub Actions testing..."
	@command -v brew >/dev/null 2>&1 || { echo "❌ Homebrew required. Install from https://brew.sh"; exit 1; }
	@command -v act >/dev/null 2>&1 && echo "✅ act is already installed" || brew install act
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker required. Install Docker Desktop from https://www.docker.com/products/docker-desktop"; exit 1; }
	@echo "✅ act installed successfully"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy .secrets.example to .secrets and fill in your values"
	@echo "  2. Run 'make workflow-list' to see available workflows"
	@echo "  3. Run 'make workflow-test' for quick validation"

workflow-setup:
	@echo "Setting up workflow testing environment..."
	@test -f .secrets || { echo "Creating .secrets from example..."; cp .secrets.example .secrets; echo "⚠️  Please edit .secrets and add your tokens"; }
	@test -f .env.test || { echo "Creating .env.test from example..."; cp .env.test.example .env.test; }
	@mkdir -p /tmp/act-artifacts
	@echo "✅ Workflow testing environment ready"
	@echo ""
	@echo "Configuration files:"
	@echo "  .actrc         - act configuration"
	@echo "  .secrets       - GitHub tokens and secrets"
	@echo "  .env.test      - Test environment variables"

workflow-list:
	@command -v act >/dev/null 2>&1 || { echo "❌ act not installed. Run 'make workflow-install' first"; exit 1; }
	@echo "Available GitHub Workflows:"
	@echo ""
	act -l

workflow-test:
	@echo "Running quick workflow validation..."
	@command -v act >/dev/null 2>&1 || { echo "❌ act not installed. Run 'make workflow-install' first"; exit 1; }
	@echo "Validating CI/CD workflow..."
	act -n -W .github/workflows/ci-cd.yml
	@echo ""
	@echo "Validating MA Cross Tests workflow..."
	act -n -W .github/workflows/ma_cross_tests.yml
	@echo ""
	@echo "✅ Workflow syntax validation complete"

workflow-ci:
	@echo "Running full CI simulation locally (Docker Compose method)..."
	@./scripts/test-ci-locally.sh

workflow-ci-verbose:
	@echo "Running full CI simulation with verbose output..."
	@./scripts/test-ci-locally.sh --verbose

workflow-ci-lint-only:
	@echo "Running linting checks only..."
	@./scripts/test-ci-locally.sh --lint-only

workflow-full:
	@command -v act >/dev/null 2>&1 || { echo "❌ act not installed. Run 'make workflow-install' first"; exit 1; }
	@echo "Running complete workflow with act..."
	@./scripts/test-workflow-with-act.sh

workflow-lint:
	@command -v act >/dev/null 2>&1 || { echo "❌ act not installed. Run 'make workflow-install' first"; exit 1; }
	@echo "Testing lint job with act..."
	@./scripts/test-workflow-with-act.sh --workflow ci-cd.yml --job lint

workflow-backend:
	@command -v act >/dev/null 2>&1 || { echo "❌ act not installed. Run 'make workflow-install' first"; exit 1; }
	@echo "Testing backend job with act (note: requires service containers)..."
	@./scripts/test-workflow-with-act.sh --workflow ci-cd.yml --job test-backend

workflow-ma-cross:
	@command -v act >/dev/null 2>&1 || { echo "❌ act not installed. Run 'make workflow-install' first"; exit 1; }
	@echo "Testing MA Cross workflow with act..."
	@./scripts/test-workflow-with-act.sh --workflow ma_cross_tests.yml

workflow-dry-run:
	@command -v act >/dev/null 2>&1 || { echo "❌ act not installed. Run 'make workflow-install' first"; exit 1; }
	@echo "Dry run of all workflows (shows what would run)..."
	act -n
