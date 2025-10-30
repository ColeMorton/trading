# Scripts Directory

This directory contains helper scripts for development, testing, and workflow validation.

## Workflow Testing Scripts

### `test-ci-locally.sh`

Simulates the full CI pipeline locally using Docker Compose (no additional tools required).

**Usage:**

```bash
# Full CI simulation
./scripts/test-ci-locally.sh

# With verbose output
./scripts/test-ci-locally.sh --verbose

# Linting only (fast)
./scripts/test-ci-locally.sh --lint-only

# Skip tests
./scripts/test-ci-locally.sh --no-tests

# Skip build
./scripts/test-ci-locally.sh --no-build

# Show help
./scripts/test-ci-locally.sh --help
```

**What it does:**

1. Starts PostgreSQL and Redis with Docker Compose
2. Runs linting checks (black, isort, flake8, mypy, bandit)
3. Runs the full test suite
4. Builds Docker images
5. Cleans up services

**Requirements:**

- Docker and Docker Compose
- Poetry
- Python 3.11+

### `test-workflow-with-act.sh`

Tests GitHub Actions workflows locally using `act`.

**Usage:**

```bash
# List all workflows
./scripts/test-workflow-with-act.sh --list

# Dry-run (validate syntax)
./scripts/test-workflow-with-act.sh --dry-run

# Test specific workflow
./scripts/test-workflow-with-act.sh --workflow ci-cd.yml

# Test specific job
./scripts/test-workflow-with-act.sh --job lint

# Test with event
./scripts/test-workflow-with-act.sh --event push --event-file .github/workflows/events/push-develop.json

# Verbose output
./scripts/test-workflow-with-act.sh --workflow ci-cd.yml --verbose

# Show help
./scripts/test-workflow-with-act.sh --help
```

**Requirements:**

- Docker
- act (install with `make workflow-install`)
- .secrets file (copy from .secrets.example)

## Makefile Commands

For easier usage, use the Makefile commands:

```bash
# Show workflow testing commands
make workflow-help

# Install act
make workflow-install

# Setup environment
make workflow-setup

# Quick validation
make workflow-test

# Full CI simulation (recommended)
make workflow-ci

# Test specific jobs
make workflow-lint
make workflow-backend
```

## Documentation

See `docs/development/WORKFLOW_TESTING.md` for complete documentation.

## Other Scripts

(Add documentation for other scripts in this directory)
