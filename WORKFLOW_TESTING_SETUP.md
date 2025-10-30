# GitHub Workflow Local Testing Setup ✅

This project is now configured for local GitHub Actions workflow testing!

## What Was Added

### 1. Configuration Files

- **`.actrc`** - Configuration for act (GitHub Actions local runner)
- **`.secrets.example`** - Template for GitHub tokens and secrets
- **`.env.test.example`** - Template for test environment variables
- Updated **`.gitignore`** - Added patterns for workflow testing artifacts

### 2. Testing Scripts

- **`scripts/test-ci-locally.sh`** - Full CI simulation using Docker Compose
- **`scripts/test-workflow-with-act.sh`** - Test workflows with act tool
- **`scripts/README.md`** - Scripts documentation

### 3. Event Payload Files

Located in `.github/workflows/events/`:

- `push-develop.json` - Simulate push to develop
- `push-main.json` - Simulate push to main
- `pull-request.json` - Simulate pull request
- `workflow-dispatch-unit.json` - Manual trigger with unit tests
- `workflow-dispatch-all.json` - Manual trigger with all tests

### 4. Makefile Commands

Added comprehensive workflow testing commands (run `make workflow-help` to see all).

### 5. Documentation

- **`docs/development/WORKFLOW_TESTING.md`** - Complete workflow testing guide

## Quick Start

### Option 1: Docker Compose Method (Recommended - No Setup Required)

Test your CI pipeline immediately without installing anything extra:

```bash
# Full CI simulation (linting + tests + build)
make workflow-ci

# Verbose output
make workflow-ci-verbose

# Linting only (fast)
make workflow-ci-lint-only
```

**How it works:**

- Uses `docker-compose.test.yml` with isolated test services
- PostgreSQL on port 5433 (avoids conflicts)
- Redis on port 6380 (avoids conflicts)
- Uses tmpfs for faster execution

**Advantages:**
✅ No additional tools needed
✅ Works immediately
✅ Fast execution
✅ Tests actual CI logic
✅ No port conflicts with local services

### Option 2: Act Method (Advanced - YAML Validation)

For testing GitHub Actions YAML syntax and workflow structure:

```bash
# 1. Install act
make workflow-install

# 2. Setup environment (creates .secrets and .env.test)
make workflow-setup

# 3. Edit .secrets with your GitHub token
nano .secrets

# 4. List available workflows
make workflow-list

# 5. Validate workflow syntax
make workflow-test

# 6. Test specific jobs
make workflow-lint        # Test lint job
make workflow-backend     # Test backend job
make workflow-ma-cross    # Test MA Cross workflow
```

**Advantages:**
✅ Validates GitHub Actions YAML syntax
✅ Tests workflow triggers and conditionals
✅ Tests job dependencies
✅ Tests matrix builds

## Usage Examples

### Before Pushing Changes

```bash
# Quick validation
make workflow-test

# Full CI check
make workflow-ci

# If everything passes, push to GitHub
git add .
git commit -m "Your changes"
git push
```

### Testing Specific Workflows

```bash
# Test CI/CD workflow
./scripts/test-workflow-with-act.sh --workflow ci-cd.yml --dry-run

# Test specific job
./scripts/test-workflow-with-act.sh --workflow ci-cd.yml --job lint

# Test with push event
./scripts/test-workflow-with-act.sh \
  --event push \
  --event-file .github/workflows/events/push-develop.json
```

### Testing MA Cross Workflow

```bash
# With make
make workflow-ma-cross

# Or directly
./scripts/test-workflow-with-act.sh --workflow ma_cross_tests.yml
```

### Debugging Failed Workflows

```bash
# Run with verbose output
make workflow-ci-verbose

# Or with act
./scripts/test-workflow-with-act.sh --workflow ci-cd.yml --job lint --verbose
```

## Available Commands

### Quick Reference

| Command                  | Description                          |
| ------------------------ | ------------------------------------ |
| `make workflow-help`     | Show all workflow commands           |
| `make workflow-install`  | Install act tool                     |
| `make workflow-setup`    | Setup environment files              |
| `make workflow-list`     | List all workflows and jobs          |
| `make workflow-test`     | Validate workflow syntax             |
| `make workflow-ci`       | **Full CI simulation (recommended)** |
| `make workflow-lint`     | Test lint job                        |
| `make workflow-backend`  | Test backend tests job               |
| `make workflow-ma-cross` | Test MA Cross workflow               |

### Common Scenarios

**Fast iteration during development:**

```bash
make workflow-ci-lint-only
```

**Before committing:**

```bash
make workflow-ci
```

**Test workflow changes:**

```bash
make workflow-test
```

**Debug specific job:**

```bash
make workflow-ci-verbose
```

## Configuration

### Setting Up Secrets (Optional - for act only)

```bash
# Copy example file
cp .secrets.example .secrets

# Edit with your tokens
nano .secrets
```

Add your GitHub token:

```bash
GITHUB_TOKEN=ghp_your_token_here
```

**Note:** This is only needed for `act`. The Docker Compose method doesn't require secrets.

### Environment Variables

The `.env.test` file is automatically created from `.env.test.example`. Edit if needed:

```bash
# Edit test environment
nano .env.test
```

## Troubleshooting

### act not found

```bash
make workflow-install
```

### Docker not running

```bash
# Start Docker Desktop
open -a Docker
```

### Services not starting

```bash
# Start manually
docker compose up -d postgres redis

# Check status
docker compose ps
```

### Permission denied

```bash
chmod +x scripts/test-ci-locally.sh
chmod +x scripts/test-workflow-with-act.sh
```

## Documentation

- **Complete Guide:** `docs/development/WORKFLOW_TESTING.md`
- **Scripts README:** `scripts/README.md`
- **Makefile Help:** `make workflow-help`

## What's Next?

1. **Test it now:** Run `make workflow-ci` to see it in action
2. **Read the docs:** Check `docs/development/WORKFLOW_TESTING.md` for advanced usage
3. **Customize:** Modify event payloads in `.github/workflows/events/` for your needs
4. **Integrate:** Add `make workflow-ci` to your pre-push workflow

## Benefits

✅ **Catch errors before pushing** - Find workflow issues locally
✅ **Faster iteration** - No waiting for GitHub Actions
✅ **Save CI minutes** - Test locally instead of on GitHub
✅ **Better debugging** - Full control over execution
✅ **Confidence** - Know your workflows work before pushing

## Current Status

**Act Installation:** ❌ Not installed (run `make workflow-install`)
**Docker Compose Method:** ✅ Ready to use (run `make workflow-ci`)
**Event Payloads:** ✅ Created
**Scripts:** ✅ Executable
**Documentation:** ✅ Complete

---

**Next Steps:**

```bash
# Try it now!
make workflow-ci
```

For questions or issues, see `docs/development/WORKFLOW_TESTING.md`
