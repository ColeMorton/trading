# Tool Versions Reference

This document tracks the versions of key tools used across the project to ensure consistency.

## Centralized Version Management

**🎯 Single Source of Truth: `.versions` file**

All tool versions are defined in the `.versions` file at the project root. This centralized approach:

- ✅ Reduces fragility from version mismatches
- ✅ Makes updates easy (change in one place)
- ✅ Enables automated validation
- ✅ Ensures consistency across Docker, CI/CD, and documentation

**📖 For complete details, see [VERSIONING.md](./VERSIONING.md)**

## Poetry Version: 1.8.3

**Why 1.8.3?**

- Supports `package-mode` field in `pyproject.toml` (introduced in Poetry 1.8.0)
- Stable release with bug fixes and improvements
- Consistent across all environments

### Poetry Version Locations

All Poetry installations in this project use version **1.8.3**:

1. **Dockerfile.api (Development Stage)** - Line 18

   - Location: `/Dockerfile.api`
   - Usage: `ENV POETRY_VERSION=1.8.3`

2. **Dockerfile.api (Production Stage)** - Line 84

   - Location: `/Dockerfile.api`
   - Usage: `ENV POETRY_VERSION=1.8.3`

3. **GitHub Actions Composite Action** - Line 11

   - Location: `/.github/actions/setup-python-poetry/action.yml`
   - Usage: Default value for `poetry-version` input

4. **Concurrency Tests Workflow** - Line 5

   - Location: `/.github/workflows/concurrency_tests.yml`
   - Usage: `POETRY_VERSION: '1.8.3'`

5. **MA Cross Tests Workflow** - Line 38
   - Location: `/.github/workflows/ma_cross_tests.yml`
   - Usage: `POETRY_VERSION: '1.8.3'`

### Updating Poetry Version

**Easy 3-Step Process:**

1. **Update `.versions` file** - Change the version number
2. **Update defaults in two locations:**
   - `Dockerfile.api` - ARG defaults (lines 5-6)
   - `.github/actions/setup-python-poetry/action.yml` - Input defaults
3. **Validate consistency:**
   ```bash
   ./scripts/validate-versions.sh
   ```

**Important:** Individual workflows should NOT hardcode versions. They use defaults from the composite action automatically.

### Installation Instructions

#### Using Poetry Installer (Recommended)

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install specific version
curl -sSL https://install.python-poetry.org | python3 - --version 1.8.3
```

#### Using pip

```bash
pip install --no-cache-dir poetry==1.8.3
```

## Python Version: 3.11

All environments use Python 3.11 for consistency.

## Other Tools

### Development Tools

- **Ruff**: Latest stable (configured in `pyproject.toml`)
- **mypy**: Latest stable (configured in `pyproject.toml`)
- **Bandit**: Latest stable (configured in `pyproject.toml`)
- **pre-commit**: Latest stable (configured in `.pre-commit-config.yaml`)

### Testing Tools

- **pytest**: Latest stable (configured in `pyproject.toml`)
- **pytest-asyncio**: Latest stable
- **pytest-cov**: Latest stable

## Validation

### Automated Version Consistency Check

Run the validation script to ensure all versions match:

```bash
./scripts/validate-versions.sh
```

This script checks:

- ✅ `.versions` file exists and is valid
- ✅ `Dockerfile.api` ARG defaults match `.versions`
- ✅ GitHub Actions composite action defaults match `.versions`
- ✅ No hardcoded versions in individual workflows

**Add to CI Pipeline:** This script runs automatically in CI to catch mismatches.

### Manual Verification

To verify tools are installed correctly:

```bash
# Check Poetry version
poetry --version  # Should show: Poetry (version 1.8.3)

# Check Python version
python --version  # Should show: Python 3.11.x

# Verify all pre-commit tools
poetry run pre-commit run --all-files
```

## CI/CD Integration

All GitHub Actions workflows use the composite action `.github/actions/setup-python-poetry` which:

- Sets up Python 3.11
- Installs Poetry 1.8.3
- Caches both Poetry installation and dependencies
- Configures virtualenvs consistently

## Troubleshooting

### Poetry Version Mismatch

If you encounter issues with `package-mode` not being recognized:

```bash
# Check current Poetry version
poetry --version

# Should show: Poetry (version 1.8.3)

# If not, reinstall:
pip install --upgrade poetry==1.8.3
```

### Lock File Issues

If `poetry.lock` becomes out of sync:

```bash
# Regenerate lock file
poetry lock --no-update

# Or with updates
poetry lock
```

## References

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry 1.8.0 Release Notes](https://github.com/python-poetry/poetry/releases/tag/1.8.0) - Introduced `package-mode`
- [Poetry 1.8.3 Release Notes](https://github.com/python-poetry/poetry/releases/tag/1.8.3) - Current version
