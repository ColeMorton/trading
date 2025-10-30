#!/bin/bash
# Local CI Testing Script
# Simulates the full CI pipeline locally without using GitHub Actions

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Parse arguments
RUN_TESTS=true
RUN_BUILD=true
RUN_LINT=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-tests)
            RUN_TESTS=false
            shift
            ;;
        --no-build)
            RUN_BUILD=false
            shift
            ;;
        --no-lint)
            RUN_LINT=false
            shift
            ;;
        --lint-only)
            RUN_TESTS=false
            RUN_BUILD=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-tests     Skip running tests"
            echo "  --no-build     Skip building Docker images"
            echo "  --no-lint      Skip linting"
            echo "  --lint-only    Only run linting (skip tests and build)"
            echo "  --verbose, -v  Show verbose output"
            echo "  --help, -h     Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_step "Starting Local CI Simulation"
echo ""

# Set environment variables
export ENVIRONMENT=test
export PYTEST_RUNNING=1

# Set application environment variables (using test ports to avoid conflicts)
export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/test_db
export REDIS_URL=redis://localhost:6380

# Start services
print_step "Starting PostgreSQL and Redis (on test ports 5433/6380)..."
docker compose -f docker-compose.test.yml up -d postgres redis

# Wait for services to be ready
print_step "Waiting for services to be healthy..."

# Wait for PostgreSQL to be healthy (with retry logic)
print_step "Waiting for PostgreSQL..."
RETRIES=30
DELAY=2
for i in $(seq 1 $RETRIES); do
    if docker compose -f docker-compose.test.yml ps postgres | grep -q "healthy"; then
        print_success "PostgreSQL is healthy"
        break
    fi
    if [ $i -eq $RETRIES ]; then
        print_error "PostgreSQL failed to become healthy after ${RETRIES} attempts"
        docker compose -f docker-compose.test.yml logs postgres
        docker compose -f docker-compose.test.yml down
        exit 1
    fi
    [ "$VERBOSE" = true ] && echo "  Attempt $i/$RETRIES..."
    sleep $DELAY
done

# Wait for Redis to be healthy
print_step "Waiting for Redis..."
for i in $(seq 1 $RETRIES); do
    if docker compose -f docker-compose.test.yml ps redis | grep -q "healthy"; then
        print_success "Redis is healthy"
        break
    fi
    if [ $i -eq $RETRIES ]; then
        print_error "Redis failed to become healthy after ${RETRIES} attempts"
        docker compose -f docker-compose.test.yml logs redis
        docker compose -f docker-compose.test.yml down
        exit 1
    fi
    [ "$VERBOSE" = true ] && echo "  Attempt $i/$RETRIES..."
    sleep $DELAY
done

print_success "Services are running"
echo ""

# Linting
if [ "$RUN_LINT" = true ]; then
    print_step "Running linting checks..."

    if [ "$VERBOSE" = true ]; then
        poetry run black --check . || (print_error "Black formatting check failed" && exit 1)
        poetry run isort --check-only . || (print_error "isort import sorting check failed" && exit 1)
        poetry run flake8 . || (print_error "flake8 linting failed" && exit 1)
        poetry run mypy app/ || print_warning "mypy type checking found issues (non-fatal)"
    else
        poetry run black --check . > /dev/null 2>&1 || (print_error "Black formatting check failed" && exit 1)
        poetry run isort --check-only . > /dev/null 2>&1 || (print_error "isort import sorting check failed" && exit 1)
        poetry run flake8 . > /dev/null 2>&1 || (print_error "flake8 linting failed" && exit 1)
        poetry run mypy app/ > /dev/null 2>&1 || print_warning "mypy type checking found issues (non-fatal)"
    fi

    print_success "Linting checks passed"

    print_step "Running security scan with bandit..."
    if [ "$VERBOSE" = true ]; then
        poetry run bandit -r app/ -ll || print_warning "Bandit found security issues (non-fatal)"
    else
        poetry run bandit -r app/ -ll > /dev/null 2>&1 || print_warning "Bandit found security issues (non-fatal)"
    fi

    print_success "Security scan completed"
    echo ""
fi

# Testing
if [ "$RUN_TESTS" = true ]; then
    print_step "Running test suite..."

    # Check if test script exists
    if [ -f "tests/run_unified_tests.py" ]; then
        if [ "$VERBOSE" = true ]; then
            poetry run python tests/run_unified_tests.py ci -c --save ci_results.json
        else
            poetry run python tests/run_unified_tests.py ci -c --save ci_results.json > /dev/null 2>&1
        fi

        if [ $? -eq 0 ]; then
            print_success "Unit tests passed"
        else
            print_error "Unit tests failed"
            docker compose down
            exit 1
        fi
    else
        print_warning "Unified test suite not found, running pytest directly..."
        if [ "$VERBOSE" = true ]; then
            poetry run pytest tests/ -v --cov=app --cov-report=term-missing
        else
            poetry run pytest tests/ --cov=app > /dev/null 2>&1
        fi

        if [ $? -eq 0 ]; then
            print_success "Tests passed"
        else
            print_error "Tests failed"
            docker compose down
            exit 1
        fi
    fi
    echo ""
fi

# Build Docker images
if [ "$RUN_BUILD" = true ]; then
    print_step "Building Docker images..."

    if [ -f "Dockerfile.api" ]; then
        if [ "$VERBOSE" = true ]; then
            docker build -f Dockerfile.api -t trading-api:test .
        else
            docker build -f Dockerfile.api -t trading-api:test . > /dev/null 2>&1
        fi

        if [ $? -eq 0 ]; then
            print_success "API Docker image built successfully"
        else
            print_error "API Docker image build failed"
            docker compose down
            exit 1
        fi
    else
        print_warning "Dockerfile.api not found, skipping API build"
    fi

    if [ -f "app/frontend/sensylate/Dockerfile" ]; then
        if [ "$VERBOSE" = true ]; then
            docker build -f app/frontend/sensylate/Dockerfile -t trading-frontend:test app/frontend/sensylate/
        else
            docker build -f app/frontend/sensylate/Dockerfile -t trading-frontend:test app/frontend/sensylate/ > /dev/null 2>&1
        fi

        if [ $? -eq 0 ]; then
            print_success "Frontend Docker image built successfully"
        else
            print_warning "Frontend Docker image build failed (non-fatal)"
        fi
    else
        print_warning "Frontend Dockerfile not found, skipping frontend build"
    fi
    echo ""
fi

# Cleanup
print_step "Cleaning up services..."
docker compose -f docker-compose.test.yml down

print_success "Cleanup complete"
echo ""

# Final summary
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ All CI checks passed successfully!  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Your changes are ready to push to GitHub!"
