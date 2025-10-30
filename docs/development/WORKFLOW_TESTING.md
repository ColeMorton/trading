# GitHub Workflow Testing Guide

This guide explains how to test GitHub Actions workflows locally before pushing changes to GitHub.

## Overview

Testing workflows locally helps you:

- Catch syntax errors before pushing
- Validate workflow logic without CI/CD delays
- Iterate faster during workflow development
- Reduce GitHub Actions minutes usage
- Test with different event triggers

## Quick Start

```bash
# Install act (GitHub Actions local runner)
make workflow-install

# Setup environment
make workflow-setup

# List all workflows
make workflow-list

# Quick validation (dry-run)
make workflow-test

# Full CI simulation (recommended for most testing)
make workflow-ci
```

## Testing Methods

### Method 1: Docker Compose Simulation (Recommended)

**Best for:** Testing the actual CI logic without GitHub Actions complexity

```bash
# Full CI pipeline simulation
make workflow-ci

# With verbose output
make workflow-ci-verbose

# Linting only
make workflow-ci-lint-only

# Custom options
./scripts/test-ci-locally.sh --no-tests  # Skip tests
./scripts/test-ci-locally.sh --no-build  # Skip Docker build
./scripts/test-ci-locally.sh --help      # Show all options
```

**How it works:**

- Uses `docker-compose.test.yml` to start PostgreSQL (port 5433) and Redis (port 6380)
- Test ports avoid conflicts with local services
- Uses tmpfs for faster test execution
- Sets test environment variables automatically
- Runs linting, tests, and builds
- Cleans up services when done

**Advantages:**

- ✅ No additional tools needed (uses existing Docker Compose)
- ✅ Fast execution
- ✅ Tests actual CI logic
- ✅ Works with services (PostgreSQL, Redis)
- ✅ Easy to debug
- ✅ Automatic environment setup

**Limitations:**

- ❌ Doesn't test GitHub Actions YAML syntax
- ❌ Doesn't validate workflow triggers or conditionals

### Method 2: Act (GitHub Actions Runner)

**Best for:** Testing GitHub Actions YAML syntax and workflow structure

```bash
# Install act
make workflow-install

# List available workflows and jobs
make workflow-list

# Validate workflow syntax (dry-run)
make workflow-test

# Test specific jobs
make workflow-lint          # Test lint job
make workflow-backend       # Test backend job (requires services)
make workflow-ma-cross      # Test MA Cross workflow

# Custom testing
./scripts/test-workflow-with-act.sh --help
```

**Advantages:**

- ✅ Tests actual GitHub Actions YAML
- ✅ Validates workflow syntax
- ✅ Tests different event triggers
- ✅ Tests job dependencies
- ✅ Tests matrix builds

**Limitations:**

- ❌ Service containers may behave differently
- ❌ Some GitHub-specific features not fully supported
- ❌ Slower than Docker Compose method
- ❌ Requires act installation

## Configuration Files

### `.actrc`

Configuration for act tool:

```ini
# Platform selection
--platform ubuntu-latest=catthehacker/ubuntu:act-latest

# Architecture (for M1/M2 Macs)
--container-architecture linux/amd64

# Secrets and environment
--secret-file .secrets
--env-file .env.test

# Artifact storage
--artifact-server-path /tmp/act-artifacts

# Performance
--reuse
--verbose
```

### `.secrets`

GitHub secrets for local testing:

```bash
# Copy from .secrets.example
cp .secrets.example .secrets

# Edit with your values
GITHUB_TOKEN=ghp_your_token_here
CODECOV_TOKEN=your_codecov_token
```

**Important:** Never commit `.secrets` to git! It's in `.gitignore`.

### `.env.test`

Environment variables for testing:

```bash
# Copy from .env.test.example
cp .env.test.example .env.test

# Edit if needed (defaults usually work)
ENVIRONMENT=test
DATABASE_URL=postgresql://test_user:test_password@localhost:5432/test_db
```

## Testing Scenarios

### Test Workflow Syntax

```bash
# Dry-run (no execution)
make workflow-test

# Or with act directly
act -n
```

### Test Specific Jobs

```bash
# Lint job
make workflow-lint

# Or with act
act -j lint

# Backend tests
act -j test-backend

# Build job
act -j build
```

### Test with Different Events

```bash
# Push to develop
act push -e .github/workflows/events/push-develop.json

# Push to main
act push -e .github/workflows/events/push-main.json

# Pull request
act pull_request -e .github/workflows/events/pull-request.json

# Manual trigger (workflow_dispatch)
act workflow_dispatch -e .github/workflows/events/workflow-dispatch-unit.json
```

### Test Specific Workflows

```bash
# Test CI/CD workflow
act -W .github/workflows/ci-cd.yml

# Test MA Cross Tests workflow
act -W .github/workflows/ma_cross_tests.yml

# Or with helper script
./scripts/test-workflow-with-act.sh --workflow ci-cd.yml
./scripts/test-workflow-with-act.sh --workflow ma_cross_tests.yml
```

### Test with Verbose Output

```bash
# Docker Compose method
make workflow-ci-verbose

# Act method
act -v
act -j lint -v
```

## Event Payload Files

Custom event payloads are in `.github/workflows/events/`:

- `push-develop.json` - Push to develop branch
- `push-main.json` - Push to main branch
- `pull-request.json` - Pull request event
- `workflow-dispatch-unit.json` - Manual trigger with unit test suite
- `workflow-dispatch-all.json` - Manual trigger with all tests

### Creating Custom Event Payloads

```json
{
  "ref": "refs/heads/feature-branch",
  "inputs": {
    "test_suite": "integration"
  },
  "repository": {
    "name": "trading",
    "owner": {
      "name": "colemorton"
    }
  }
}
```

## Common Issues and Solutions

### Issue: act not found

```bash
# Install act
make workflow-install

# Or manually
brew install act
```

### Issue: Docker not running

```bash
# Start Docker Desktop
open -a Docker

# Verify Docker is running
docker info
```

### Issue: Services not starting

```bash
# Start services manually
docker compose -f docker-compose.test.yml up -d postgres redis

# Check service health
docker compose -f docker-compose.test.yml ps

# View logs
docker compose -f docker-compose.test.yml logs postgres redis
```

### Issue: Port conflicts (port already in use)

The test services use non-standard ports to avoid conflicts:

- PostgreSQL: 5433 (instead of 5432)
- Redis: 6380 (instead of 6379)

If you still have conflicts, check what's using those ports:

```bash
# Check what's using port 5433
lsof -i :5433

# Check what's using port 6380
lsof -i :6380
```

### Issue: Permission denied on scripts

```bash
# Make scripts executable
chmod +x scripts/test-ci-locally.sh
chmod +x scripts/test-workflow-with-act.sh
```

### Issue: .secrets file missing

```bash
# Copy example and edit
cp .secrets.example .secrets

# Edit with your tokens
nano .secrets
```

### Issue: Service containers not working with act

Use the Docker Compose method instead:

```bash
make workflow-ci
```

## Best Practices

### 1. Test Before Pushing

```bash
# Run quick validation
make workflow-test

# Run full CI simulation
make workflow-ci

# If all passes, push to GitHub
git push
```

### 2. Use Docker Compose for Fast Iteration

```bash
# Fast feedback loop
make workflow-ci-lint-only  # Linting only
make workflow-ci --no-tests # Skip slow tests
```

### 3. Use act for YAML Validation

```bash
# Validate workflow structure
act -n

# Test job dependencies
act -j deploy-staging -n  # Check what would run
```

### 4. Test Different Scenarios

```bash
# Test develop branch push
act push -e .github/workflows/events/push-develop.json

# Test main branch push
act push -e .github/workflows/events/push-main.json

# Test pull request
act pull_request -e .github/workflows/events/pull-request.json
```

### 5. Keep Secrets Secure

```bash
# Never commit .secrets
git status  # Should show .secrets as untracked

# Rotate tokens regularly
# Update .secrets with new tokens
```

## Workflow Testing Checklist

Before pushing workflow changes:

- [ ] Syntax validated with `make workflow-test`
- [ ] Lint job passes locally
- [ ] Test jobs pass with `make workflow-ci`
- [ ] Docker images build successfully
- [ ] Services (PostgreSQL, Redis) work correctly
- [ ] Secrets are properly configured
- [ ] Environment variables are correct
- [ ] Event triggers work as expected
- [ ] Job dependencies are correct
- [ ] Conditional logic works properly

## Advanced Usage

### Custom Act Command

```bash
# Run specific platform
act --platform ubuntu-latest=catthehacker/ubuntu:full-latest

# Skip specific jobs
act -j lint -j test-backend

# Use specific secrets
act -s GITHUB_TOKEN=your_token

# Mount volumes
act --bind /local/path:/container/path

# Use Docker socket (for service containers)
act -v /var/run/docker.sock:/var/run/docker.sock
```

### Debug Workflow Execution

```bash
# Very verbose output
act -v -j lint

# Keep containers after failure (for debugging)
act --rm=false

# Shell into failed container
docker ps -a  # Find container ID
docker exec -it <container_id> /bin/bash
```

### Performance Optimization

```bash
# Enable container reuse (in .actrc)
--reuse

# Use cache
act --cache-server

# Pull images once
docker pull catthehacker/ubuntu:act-latest
```

## GitHub CLI Alternative

For testing on actual GitHub infrastructure:

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Trigger workflow on GitHub
gh workflow run ci-cd.yml --ref develop

# Watch workflow run
gh run watch

# View logs
gh run view --log
```

## Resources

- **act Documentation:** https://github.com/nektos/act
- **GitHub Actions Documentation:** https://docs.github.com/en/actions
- **Docker Compose Documentation:** https://docs.docker.com/compose/
- **GitHub CLI Documentation:** https://cli.github.com/

## Summary

**For most testing:** Use `make workflow-ci` (fast, reliable, works with services)

**For YAML validation:** Use `make workflow-test` (validates syntax)

**For advanced testing:** Use act with custom events and jobs

**Before every push:** Run `make workflow-ci` to ensure everything passes

Happy workflow testing! 🚀
