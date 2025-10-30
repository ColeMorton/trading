# Unified Test Execution Makefile
# Phase 3: Testing Infrastructure Consolidation

.PHONY: help test test-unit test-integration test-api test-strategy test-e2e test-performance test-smoke test-all test-quick test-ci clean coverage lint install

# Default target
help:
	@echo "Trading System Unified Test Runner"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@echo "  test-smoke      - Run quick smoke tests (2 min)"
	@echo "  test-unit       - Run unit tests (5 min)"
	@echo "  test-integration- Run integration tests (15 min)"
	@echo "  test-api        - Run API tests (10 min)"
	@echo "  test-strategy   - Run strategy tests (20 min)"
	@echo "  test-e2e        - Run end-to-end tests (30 min)"
	@echo "  test-performance- Run performance tests (1 hour)"
	@echo ""
	@echo "Test suites:"
	@echo "  test-quick      - Run smoke + unit tests"
	@echo "  test-ci         - Run unit + integration + api tests"
	@echo "  test-all        - Run all test categories"
	@echo ""
	@echo "Utilities:"
	@echo "  coverage        - Generate coverage report"
	@echo "  lint            - Run code quality checks"
	@echo "  clean           - Clean test artifacts"
	@echo "  install         - Install test dependencies"

# Individual test categories
test-smoke:
	@echo "🧪 Running smoke tests..."
	@python tests/run_unified_tests.py smoke

test-unit:
	@echo "🧪 Running unit tests..."
	@python tests/run_unified_tests.py unit -v

test-integration:
	@echo "🧪 Running integration tests..."
	@python tests/run_unified_tests.py integration -v

test-api:
	@echo "🧪 Running API tests..."
	@python tests/run_unified_tests.py api -v

test-strategy:
	@echo "🧪 Running strategy tests..."
	@python tests/run_unified_tests.py strategy -v

test-e2e:
	@echo "🧪 Running end-to-end tests..."
	@python tests/run_unified_tests.py e2e -v

test-performance:
	@echo "🧪 Running performance tests..."
	@python tests/run_unified_tests.py performance -v

# Test suites
test-quick:
	@echo "🚀 Running quick test suite..."
	@python tests/run_unified_tests.py quick -v

test-ci:
	@echo "🚀 Running CI test suite..."
	@python tests/run_unified_tests.py ci -v --save test_results.json

test-all:
	@echo "🚀 Running all tests..."
	@python tests/run_unified_tests.py all -v --save test_results.json

# Test with coverage
coverage:
	@echo "📊 Running tests with coverage..."
	@python tests/run_unified_tests.py ci -c --save coverage_results.json
	@echo "Coverage report generated in htmlcov/"

# Test with parallel execution
test-parallel:
	@echo "⚡ Running tests in parallel..."
	@python tests/run_unified_tests.py quick -p -v

# Specific pytest commands for manual use
pytest-unit:
	@python -m pytest tests/ -m "unit or fast" -v --tb=short

pytest-integration:
	@python -m pytest tests/ -m "integration" -v --tb=short

pytest-api:
	@python -m pytest tests/api/ app/api/tests/ -v --tb=short

pytest-strategy:
	@python -m pytest tests/strategies/ tests/concurrency/ -m "strategy" -v --tb=short

# Code quality checks
lint:
	@echo "🔍 Running code quality checks..."
	@poetry run black --check .
	@poetry run isort --check-only .
	@poetry run flake8 .
	@poetry run mypy . --ignore-missing-imports

lint-fix:
	@echo "🔧 Fixing code quality issues..."
	@poetry run black .
	@poetry run isort .

# Dependency management
install:
	@echo "📦 Installing test dependencies..."
	@pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-timeout pytest-xdist
	@pip install black isort flake8 mypy

install-dev:
	@echo "📦 Installing development dependencies..."
	@poetry install --with dev,test

# Cleanup
clean:
	@echo "🧹 Cleaning test artifacts..."
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@rm -rf test_results.json
	@rm -rf coverage_results.json
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

# Debugging and development
test-debug:
	@echo "🐛 Running tests in debug mode..."
	@python tests/run_unified_tests.py unit -v --fail-fast

test-dry-run:
	@echo "👁️ Showing what tests would run..."
	@python tests/run_unified_tests.py all --dry-run

test-list:
	@echo "📋 Available test categories:"
	@python tests/run_unified_tests.py --list

# Performance monitoring
test-benchmark:
	@echo "⏱️ Running performance benchmarks..."
	@python tests/run_unified_tests.py performance --save benchmark_results.json
	@echo "Benchmark results saved to benchmark_results.json"

# Continuous Integration helpers
test-ci-quick:
	@python tests/run_unified_tests.py smoke unit -p --save ci_quick_results.json

test-ci-full:
	@python tests/run_unified_tests.py unit integration api -c --save ci_full_results.json

# Docker test execution (if Docker is available)
test-docker:
	@echo "🐳 Running tests in Docker container..."
	@docker-compose -f docker-compose.yml run --rm api python tests/run_unified_tests.py ci

# Test data validation
validate-test-data:
	@echo "✅ Validating test data integrity..."
	@python -c "from tests.shared.factories import create_test_market_data; print('Test data generation: OK')"
	@python -c "from tests.shared.fixtures import mock_yfinance_data; print('Mock data generation: OK')"

# Memory and resource monitoring
test-memory:
	@echo "💾 Running tests with memory monitoring..."
	@python -m pytest tests/ -m "unit" --tb=short -v --memprof-report

# Security testing
test-security:
	@echo "🔒 Running security tests..."
	@python -m bandit -r tests/ -f json -o security_report.json
	@echo "Security report saved to security_report.json"

# Documentation testing
test-docs:
	@echo "📚 Testing documentation examples..."
	@python -m doctest README.md
