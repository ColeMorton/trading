# Makefile for concurrency module testing

.PHONY: all test unit integration performance clean coverage help

# Default Python interpreter
PYTHON := python3

# Test runner script
TEST_RUNNER := ./run_tests.py

# Help target
help:
	@echo "Concurrency Module Test Targets:"
	@echo "  make test          - Run all tests"
	@echo "  make unit          - Run unit tests only"
	@echo "  make integration   - Run integration tests only"
	@echo "  make performance   - Run performance tests only"
	@echo "  make error         - Run error handling tests"
	@echo "  make coverage      - Run tests with coverage report"
	@echo "  make clean         - Clean test artifacts"
	@echo "  make ci            - Run CI test suite"
	@echo ""
	@echo "Options:"
	@echo "  VERBOSE=1          - Run with verbose output"
	@echo "  FAILFAST=1         - Stop on first failure"

# Run all tests
test:
	@echo "Running all concurrency tests..."
	@$(PYTHON) $(TEST_RUNNER) $(if $(VERBOSE),-v) $(if $(FAILFAST),--failfast)

# Run unit tests
unit:
	@echo "Running unit tests..."
	@$(PYTHON) $(TEST_RUNNER) --type unit $(if $(VERBOSE),-v) $(if $(FAILFAST),--failfast)

# Run integration tests
integration:
	@echo "Running integration tests..."
	@$(PYTHON) $(TEST_RUNNER) --type integration $(if $(VERBOSE),-v) $(if $(FAILFAST),--failfast)

# Run performance tests
performance:
	@echo "Running performance tests..."
	@$(PYTHON) $(TEST_RUNNER) --type performance $(if $(VERBOSE),-v)

# Run error handling tests
error:
	@echo "Running error handling tests..."
	@$(PYTHON) $(TEST_RUNNER) --type error $(if $(VERBOSE),-v)

# Run with coverage
coverage:
	@echo "Running tests with coverage..."
	@$(PYTHON) $(TEST_RUNNER) --coverage --output test_results.json

# CI test suite - suitable for continuous integration
ci:
	@echo "Running CI test suite..."
	@$(PYTHON) $(TEST_RUNNER) --type unit --failfast --output ci_results.json
	@$(PYTHON) $(TEST_RUNNER) --type integration --failfast --output ci_integration_results.json
	@echo "CI tests completed successfully"

# Run with pytest (if available)
pytest:
	@echo "Running tests with pytest..."
	@pytest $(if $(VERBOSE),-v) $(if $(MARKERS),-m $(MARKERS))

# Run with pytest and coverage
pytest-coverage:
	@echo "Running pytest with coverage..."
	@pytest --cov=app.concurrency --cov-report=html --cov-report=term

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	@rm -rf __pycache__ .pytest_cache .coverage htmlcov
	@rm -f test_results.json ci_*.json
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@echo "Clean complete"

# Quick test - unit tests with failfast
quick:
	@echo "Running quick test suite..."
	@$(PYTHON) $(TEST_RUNNER) --type unit --failfast -v

# Benchmark - run performance tests and save results
benchmark:
	@echo "Running benchmark tests..."
	@$(PYTHON) $(TEST_RUNNER) --type performance -v --output benchmark_$(shell date +%Y%m%d_%H%M%S).json

# Watch tests (requires pytest-watch)
watch:
	@echo "Watching for file changes..."
	@ptw -- -v
