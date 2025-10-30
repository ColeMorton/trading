---
title: Development Documentation
version: 1.0
last_updated: 2025-10-30
owner: Development Team
status: Active
audience: Developers, DevOps
---

# Development Documentation

Comprehensive guides for developers working on the trading system platform.

## Quick Navigation

- [Getting Started](#getting-started)
- [Code Quality](#code-quality)
- [Versioning](#versioning)
- [Development Environment](#development-environment)
- [Workflow Testing](#workflow-testing)

---

## Getting Started

### Essential Reading

| Document                                    | Purpose                     | Time Required |
| ------------------------------------------- | --------------------------- | ------------- |
| [Development Guide](DEVELOPMENT_GUIDE.md)   | Complete setup and workflow | 30 min        |
| [Local Development](LOCAL_DEVELOPMENT.md)   | Local environment setup     | 15 min        |
| [AI Assistant Guide](AI_ASSISTANT_GUIDE.md) | AI-assisted development     | 10 min        |

### Prerequisites

- Python 3.11+
- Poetry 1.8.3+
- Docker Desktop (optional)
- Git

---

## Code Quality

### Standards & Tools

| Document                                                        | Purpose                     | Status    |
| --------------------------------------------------------------- | --------------------------- | --------- |
| [Code Quality](CODE_QUALITY.md)                                 | Quality standards and tools | Active    |
| [Code Quality Improvement](CODE_QUALITY_IMPROVEMENT.md)         | Improvement strategies      | Active    |
| [Linting Improvements Summary](linting_improvements_summary.md) | Linting evolution           | Reference |

### Quick Commands

```bash
# Format and lint code
make lint-all

# Run formatters
make format-python

# Run linters
make lint-python

# Validate code quality
make analyze-all
```

---

## Versioning

### Tool Version Management

| Document                                                               | Purpose                              | Status |
| ---------------------------------------------------------------------- | ------------------------------------ | ------ |
| [VERSIONING.md](VERSIONING.md)                                         | Centralized version management guide | Active |
| [TOOL_VERSIONS.md](TOOL_VERSIONS.md)                                   | Tool version reference               | Active |
| [CENTRALIZED_VERSIONING_SUMMARY.md](CENTRALIZED_VERSIONING_SUMMARY.md) | Implementation summary               | Active |

### Key Concepts

**Single Source of Truth**: All tool versions are defined in `.versions` file at the project root.

**Validation**: Run `make validate-versions` to ensure consistency across Docker, CI/CD, and development environments.

**Update Process**:

1. Update `.versions` file
2. Update `Dockerfile.api` ARG defaults
3. Update `.github/actions/setup-python-poetry/action.yml` defaults
4. Run `make validate-versions`

---

## Development Environment

### Setup Options

**1. Local Development (Native)**

```bash
# Install dependencies
make install

# Start local services
make start-local

# Run development server
make dev-local
```

**2. Docker Development**

```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

**3. Hybrid (Native app + Docker services)**

```bash
# Start only databases
make services-up

# Run app locally
make dev-with-services
```

### Configuration

- [Configuration Guide](../CONFIGURATION_GUIDE.md)
- [SSH Guide](SSH_GUIDE.md)

---

## Workflow Testing

### GitHub Actions Testing

| Document                                                                   | Purpose                         | Status |
| -------------------------------------------------------------------------- | ------------------------------- | ------ |
| [WORKFLOW_TESTING.md](WORKFLOW_TESTING.md)                                 | Complete workflow testing guide | Active |
| [workflow_testing_setup.md](workflow_testing_setup.md)                     | Setup instructions              | Active |
| [workflow_testing_quick_reference.md](workflow_testing_quick_reference.md) | Quick reference                 | Active |
| [workflow_testing_troubleshooting.md](workflow_testing_troubleshooting.md) | Troubleshooting                 | Active |
| [workflows.md](workflows.md)                                               | Workflow documentation          | Active |

### Quick Commands

```bash
# Install act (local workflow testing)
make workflow-install

# List all workflows
make workflow-list

# Validate workflows
make workflow-test

# Run full CI simulation
make workflow-ci
```

---

## Development Workflow

### Daily Workflow

1. **Pull latest changes**

   ```bash
   git pull origin main
   ```

2. **Update dependencies**

   ```bash
   make install
   ```

3. **Validate versions**

   ```bash
   make validate-versions
   ```

4. **Run tests**

   ```bash
   make test-quick
   ```

5. **Code quality checks**
   ```bash
   make lint-all
   ```

### Pre-Commit Workflow

```bash
# Install pre-commit hooks
make pre-commit-install

# Run hooks manually
make pre-commit-run

# Verify commit readiness
make verify-commit
```

---

## Testing

### Test Commands

```bash
# Quick tests
make test-quick

# Full test suite
make test-full

# Specific test categories
make test-unit
make test-integration
make test-api
make test-e2e

# With services
make services-up
make test-integration
```

See [Testing Documentation](../testing/) for complete testing guides.

---

## Debugging

### Common Commands

```bash
# Check dependencies
make check-deps

# Health checks
make health

# View logs
make logs-api
make logs-db
make logs-redis

# Database operations
make setup-db
make migrate
make backup
```

---

## Additional Resources

### Architecture

- [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)
- [Architecture Documentation](../architecture/)

### API Development

- [API Documentation](../api/)
- [API Getting Started](../api/GETTING_STARTED.md)

### Database

- [Database Schema](../database/SCHEMA.md)
- [Database Documentation](../database/)

---

## Contributing

### Documentation

1. Follow frontmatter standards
2. Update DOCUMENTATION_INDEX.md
3. Maintain link integrity
4. Update CHANGELOG.md

### Code

1. Follow code quality standards
2. Write tests for new features
3. Run pre-commit hooks
4. Update documentation

---

## Quick Links

### Most Used

- [Development Guide](DEVELOPMENT_GUIDE.md) - Complete setup
- [Code Quality](CODE_QUALITY.md) - Standards
- [VERSIONING.md](VERSIONING.md) - Version management
- [Workflow Testing](WORKFLOW_TESTING.md) - CI/CD testing

### Related Documentation

- [Getting Started](../getting-started/) - New user onboarding
- [Testing Best Practices](../testing/TESTING_BEST_PRACTICES.md)
- [User Manual](../USER_MANUAL.md)

---

**Last Updated**: 2025-10-30
**Maintained By**: Development Team
**Status**: Active

**Navigation**: [Main README](../README.md) | [Documentation Index](../DOCUMENTATION_INDEX.md)
