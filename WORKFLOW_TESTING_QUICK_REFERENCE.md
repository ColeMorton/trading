# GitHub Workflow Testing - Quick Reference Card

## 🚀 Immediate Testing (No Setup Required)

```bash
# Full CI simulation - linting, tests, and build
make workflow-ci

# Just linting (fastest)
make workflow-ci-lint-only

# With verbose output
make workflow-ci-verbose
```

## 🔧 Advanced Testing (Requires act)

### Setup (One-Time)

```bash
make workflow-install    # Install act
make workflow-setup      # Create .secrets and .env.test
nano .secrets           # Add your GitHub token
```

### Usage

```bash
make workflow-list       # See all workflows
make workflow-test       # Validate syntax
make workflow-lint       # Test lint job
make workflow-backend    # Test backend job
make workflow-ma-cross   # Test MA Cross workflow
```

## 📋 Common Workflows

### Before Pushing

```bash
make workflow-ci
git push
```

### Testing Workflow Changes

```bash
make workflow-test      # Validate syntax
make workflow-ci        # Run full CI
```

### Debugging

```bash
make workflow-ci-verbose
```

### Custom Testing

```bash
# Test specific workflow
./scripts/test-workflow-with-act.sh --workflow ci-cd.yml

# Test specific job
./scripts/test-workflow-with-act.sh --job lint

# With event
./scripts/test-workflow-with-act.sh \
  --event push \
  --event-file .github/workflows/events/push-develop.json

# Dry-run
./scripts/test-workflow-with-act.sh --dry-run
```

## 📁 Key Files

| File                                | Purpose                                          |
| ----------------------------------- | ------------------------------------------------ |
| `.actrc`                            | act configuration                                |
| `.secrets`                          | GitHub tokens (create from .secrets.example)     |
| `.env.test`                         | Test environment (create from .env.test.example) |
| `scripts/test-ci-locally.sh`        | CI simulation script                             |
| `scripts/test-workflow-with-act.sh` | act testing script                               |
| `.github/workflows/events/`         | Event payload files                              |

## 🎯 Two Methods Compared

| Feature                | Docker Compose     | act                  |
| ---------------------- | ------------------ | -------------------- |
| **Setup**              | None needed        | Install act          |
| **Speed**              | Fast ⚡            | Slower               |
| **YAML Validation**    | ❌                 | ✅                   |
| **Service Containers** | ✅ Perfect         | ⚠️ May differ        |
| **Use Case**           | Daily testing      | YAML validation      |
| **Command**            | `make workflow-ci` | `make workflow-test` |

## 💡 Recommended Workflow

1. **Daily development:** Use `make workflow-ci`
2. **Before push:** Run `make workflow-ci`
3. **Workflow changes:** Use `make workflow-test` + `make workflow-ci`
4. **Debugging:** Use `make workflow-ci-verbose`

## 🆘 Quick Troubleshooting

```bash
# Docker not running?
open -a Docker

# Script not executable?
chmod +x scripts/test-ci-locally.sh

# act not installed?
make workflow-install

# Need help?
make workflow-help
```

## 📚 Full Documentation

- **Complete Guide:** `docs/development/WORKFLOW_TESTING.md`
- **Setup Guide:** `WORKFLOW_TESTING_SETUP.md`
- **Scripts README:** `scripts/README.md`

## ⚡ One-Liner Test

```bash
make workflow-ci && echo "✅ Ready to push!" || echo "❌ Fix issues first"
```

---

**Pro Tip:** Add `make workflow-ci` to your pre-push git hook!
