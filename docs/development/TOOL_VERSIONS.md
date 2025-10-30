# Tool Version Management

## Single Source of Truth: Poetry

**CRITICAL:** All linting and formatting tools MUST run through Poetry.

### ❌ WRONG - Never do this:

```bash
black --check .
isort .
flake8 app/
mypy app/
```

### ✅ CORRECT - Always use Poetry:

```bash
poetry run black --check .
poetry run isort .
poetry run flake8 app/
poetry run mypy app/
```

### ✅ EVEN BETTER - Use Makefile commands:

```bash
make lint-black
make lint-imports
make lint-mypy
make format-python
```

## Why Poetry-First?

1. **Version Consistency**: Poetry lock file ensures identical versions across all environments
2. **CI Parity**: CI uses same Poetry environment as local development
3. **No Drift**: Impossible to have version mismatches between local, CI, and pre-commit
4. **Single Source**: `pyproject.toml` is the only source of truth for tool versions
5. **Automatic Updates**: `poetry update` updates all tools consistently

## Current Versions (from pyproject.toml)

- **black**: ^25.0.0 (Code formatting)
- **isort**: ^6.0.0 (Import sorting)
- **flake8**: ^7.2.0 (Style guide enforcement)
- **mypy**: ^1.16.0 (Static type checking)
- **ruff**: ^0.8.0 (Fast modern linter)
- **bandit**: ^1.8.0 (Security vulnerability scanning)

## Enforcement

All tooling enforces Poetry usage:

- **Makefile**: All commands use `poetry run`
- **Pre-commit**: Hooks call `poetry run`
- **CI**: Scripts use `poetry run`
- **Tests**: test Makefile uses `poetry run`

## Development Workflow

### 1. Initial Setup

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Verify tool versions
poetry run black --version
poetry run isort --version
poetry run mypy --version
```

### 2. Daily Development

```bash
# Check code quality
make lint-python

# Fix formatting issues
make format-python

# Run specific linter
make lint-black
make lint-mypy

# Run tests
make test
```

### 3. Pre-commit Setup

```bash
# Install pre-commit hooks (uses Poetry internally)
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

## Troubleshooting

### Version Mismatch Issues

**Problem**: CI fails but local passes

```bash
# Check Poetry versions
poetry run black --version
poetry run isort --version

# Update Poetry lock file
poetry lock --no-update
poetry install
```

**Problem**: "Command not found" errors

```bash
# Ensure Poetry is installed
poetry --version

# Install dependencies
poetry install

# Use Poetry to run tools
poetry run black --check .
```

### Pre-commit Issues

**Problem**: Pre-commit hooks fail

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Run hooks manually to debug
pre-commit run black --all-files
preetry run black --check .
```

## Migration from Direct Tool Usage

If you've been using tools directly:

1. **Remove system installations** (optional):

   ```bash
   pip uninstall black isort flake8 mypy ruff
   ```

2. **Use Poetry commands**:

   ```bash
   # Old way
   black --check .

   # New way
   poetry run black --check .
   # or
   make lint-black
   ```

3. **Update scripts**:

   ```bash
   # Find direct tool calls
   grep -r "black --check" scripts/

   # Replace with Poetry
   sed -i 's/black --check/poetry run black --check/g' scripts/*
   ```

## Validation

Run the validation script to ensure Poetry-first compliance:

```bash
# Check for direct tool usage
bash scripts/validate-tool-versions.sh

# Test all linting commands
make lint-python

# Test pre-commit hooks
pre-commit run --all-files
```

## Benefits Achieved

✅ **Zero Version Drift**: Local = CI = Pre-commit
✅ **Single Source**: `pyproject.toml` only
✅ **Automatic Updates**: `poetry update` updates everywhere
✅ **Enforcement**: Scripts validate Poetry usage
✅ **Documentation**: Clear guidance for developers
✅ **Consistency**: All environments use identical tool versions

## Breaking Changes

⚠️ **Developers must**:

1. Have Poetry installed
2. Run `poetry install` before development
3. Use `poetry run` or `make` commands (never direct tool calls)
4. Update `.pre-commit-config.yaml` (auto-update with `pre-commit autoupdate` won't work for local hooks)

## Rollback Plan

If issues arise:

1. Revert `.pre-commit-config.yaml` to external repos
2. Revert `tests/Makefile` to python -m calls
3. Keep main Makefile (already correct)

## Related Documentation

- [Development Guide](DEVELOPMENT_GUIDE.md)
- [Code Quality](CODE_QUALITY.md)
- [Testing Guide](../testing/TESTING_BEST_PRACTICES.md)
