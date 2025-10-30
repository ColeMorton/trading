# Centralized Version Management

## Overview

This project uses **centralized version management** to eliminate fragility from version mismatches across Docker, CI/CD, and development environments.

## Single Source of Truth: `.versions`

All tool versions are defined in one place: **`.versions`** file at the project root.

```bash
# .versions - Canonical version reference
PYTHON_VERSION=3.11
POETRY_VERSION=1.8.3
NODE_VERSION=20
POSTGRES_VERSION=15
REDIS_VERSION=7
```

## Version Usage Across the Project

### 1. Docker (`Dockerfile.api`)

Uses **ARG** with defaults matching `.versions`:

```dockerfile
# Build arguments - can be overridden during build
ARG PYTHON_VERSION=3.11
ARG POETRY_VERSION=1.8.3

FROM python:${PYTHON_VERSION}-slim AS development
# ...
RUN pip install --no-cache-dir poetry==$POETRY_VERSION
```

**Benefits:**

- ✅ Default versions match `.versions`
- ✅ Can be overridden during build if needed
- ✅ Visible in image labels

### 2. GitHub Actions

Uses **composite action** as the source of truth:

**Composite Action** (`.github/actions/setup-python-poetry/action.yml`):

```yaml
inputs:
  poetry-version:
    description: 'Poetry version to install (default matches .versions file)'
    required: false
    default: '1.8.3' # Must match .versions
```

**Individual Workflows:**

```yaml
# ✅ CORRECT - Uses default from composite action
- name: Setup Python with Poetry
  uses: ./.github/actions/setup-python-poetry
  with:
    python-version: ${{ env.PYTHON_VERSION }}
    # poetry-version uses default (implicit)

# ❌ WRONG - Hardcoded version
env:
  POETRY_VERSION: '1.8.3'  # DON'T DO THIS
```

## How to Update Versions

### Easy 3-Step Process

1. **Update `.versions` file**

   ```bash
   # Edit .versions
   POETRY_VERSION=1.8.4  # New version
   ```

2. **Update two synchronized locations**

   - `Dockerfile.api` (lines 5-6) - ARG defaults
   - `.github/actions/setup-python-poetry/action.yml` - Input defaults

3. **Validate consistency**
   ```bash
   make validate-versions
   # or
   ./scripts/validate-versions.sh
   ```

That's it! No need to update individual workflows.

## Validation

### Automated Checks

The `validate-versions.sh` script ensures consistency:

```bash
# Run manually
make validate-versions

# Checks performed:
# ✅ .versions file exists and is valid
# ✅ Dockerfile ARG defaults match .versions
# ✅ GitHub Actions defaults match .versions
# ✅ No hardcoded versions in workflows
```

### CI Integration

Version validation runs automatically in CI to catch mismatches before they cause problems.

## Architecture

```
┌─────────────────────────────────────────────────┐
│          .versions (Documentation)              │
│  Single source of truth for reference           │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐   ┌──────────────────────┐
│ Dockerfile  │   │  GitHub Actions      │
│ (ARG        │   │  (Composite Action)  │
│  defaults)  │   │  (Input defaults)    │
└─────────────┘   └──────────────────────┘
       │                │
       │                │
       ▼                ▼
  Docker Build    Individual Workflows
  (uses ARGs)     (use action defaults)
```

## Benefits

### ✅ Reduced Fragility

- Version mismatches caught early
- No silent drift between environments
- Clear update path

### ✅ Easy Maintenance

- Change in 3 places (not 5+)
- Clear validation
- Self-documenting

### ✅ Developer Experience

- `make validate-versions` - instant feedback
- Documentation stays in sync
- No surprises in CI

## Migration from Old Approach

### Before (Fragile ❌)

```yaml
# Had to update in 5+ places:
# 1. Dockerfile.api (dev stage)
# 2. Dockerfile.api (prod stage)
# 3. .github/actions/setup-python-poetry/action.yml
# 4. .github/workflows/concurrency_tests.yml
# 5. .github/workflows/ma_cross_tests.yml
# 6. Documentation
```

### After (Robust ✅)

```yaml
# Update in 3 places:
# 1. .versions (documentation)
# 2. Dockerfile.api ARG defaults
# 3. Composite action input defaults
#
# Validation ensures they stay in sync!
```

## FAQ

### Q: Why not read `.versions` automatically?

**A:** Different systems (Docker, GitHub Actions, bash) have different capabilities:

- Docker: Doesn't support sourcing shell files in FROM statements
- GitHub Actions: No native way to read external files for defaults
- Bash scripts: Can source `.versions` easily

The current approach balances simplicity with validation.

### Q: Can I override versions during build?

**A:** Yes! Docker ARGs can be overridden:

```bash
docker build \
  --build-arg POETRY_VERSION=1.8.4 \
  -f Dockerfile.api \
  -t trading-api:latest .
```

### Q: What if I forget to update a location?

**A:** The validation script will catch it:

```bash
make validate-versions
# ❌ MISMATCH in Dockerfile.api
#    Expected: 1.8.4
#    Found: 1.8.3
```

### Q: Should individual workflows specify `poetry-version`?

**A:** No! Workflows should use the composite action's default. This keeps updates centralized.

```yaml
# ✅ CORRECT
- uses: ./.github/actions/setup-python-poetry
  with:
    python-version: '3.11'

# ❌ AVOID (unless you need a different version)
- uses: ./.github/actions/setup-python-poetry
  with:
    poetry-version: '1.8.3'
```

## See Also

- [Tool Versions Reference](docs/development/TOOL_VERSIONS.md) - Detailed documentation
- [Validation Script](scripts/validate-versions.sh) - Source code
- [Dockerfile](Dockerfile.api) - Docker implementation
- [Composite Action](.github/actions/setup-python-poetry/action.yml) - GHA implementation
