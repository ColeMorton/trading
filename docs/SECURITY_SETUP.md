# Security Setup Guide

## Quick Start for New Developers

This guide will help you set up the security scanning and pre-commit hooks to prevent security issues from being committed.

### One-Command Setup

```bash
make pre-commit-install && make git-configure
```

This will:

- ✅ Install pre-commit hooks for both `commit` and `push`
- ✅ Configure git commit template with security reminders
- ✅ Set up automatic security scanning

### Manual Setup (If You Prefer)

#### 1. Install Pre-Commit Hooks

```bash
# Install hooks
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push

# Verify installation
poetry run pre-commit --version
```

#### 2. Configure Git Commit Template

```bash
git config commit.template .gitmessage
```

Now when you run `git commit`, you'll see helpful reminders about security checks.

#### 3. Test Your Setup

```bash
# Test all hooks
make pre-commit-run

# Or test our verification script
./scripts/verify-commit.sh --quick
```

## What Happens When You Commit

### Step-by-Step Commit Flow

```
┌─────────────────────────────────────────┐
│  1. Developer runs: git commit         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  2. Pre-commit hooks automatically run: │
│     ├─ Ruff format & linting            │
│     ├─ MyPy type checking               │
│     ├─ 🔒 Bandit security scan          │
│     └─ Other code quality checks        │
└─────────────────┬───────────────────────┘
                  │
          ┌───────┴──────┐
          │              │
          ▼              ▼
    ✅ Pass          ❌ Fail
          │              │
          │              └─► Fix issues
          │                      │
          │                      ▼
          │              Re-run commit
          │                      │
          ▼                      │
    Commit succeeds  ◄───────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│  3. Push triggers additional checks     │
│     (pre-push hooks)                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  4. CI/CD runs comprehensive validation │
│     - Pre-commit check workflow         │
│     - Bandit security scan              │
│     - All tests                         │
└─────────────────────────────────────────┘
```

### What Gets Checked

#### Before Commit (Pre-Commit Hooks)

1. **Code Formatting (Ruff)**

   - Ensures consistent code style
   - Auto-fixes many issues

2. **Code Linting (Ruff)**

   - Checks for bugs and code smells
   - Enforces best practices

3. **Type Checking (MyPy)**

   - Validates type annotations
   - Prevents type-related bugs

4. **🔒 Security Scanning (Bandit)**

   - Scans for security vulnerabilities
   - Checks for hardcoded secrets
   - Validates secure coding patterns
   - **CRITICAL**: Will block commit if issues found

5. **Other Checks**
   - Trailing whitespace removal
   - End-of-file fixer
   - YAML/JSON/TOML validation
   - Private key detection
   - Large file prevention

#### Before Push (Pre-Push Hooks)

- Re-runs all security checks
- Additional validation layer
- Catches issues if local hooks were bypassed

#### In CI/CD

Even if local hooks are bypassed (not recommended!), CI will:

- Run ALL pre-commit hooks
- Explicitly run Bandit security scan
- Block merge if any issues found

## Common Scenarios

### Scenario 1: Clean Commit (Everything Passes)

```bash
$ git add .
$ git commit -m "feat: add new feature"

trim trailing whitespace............................Passed
fix end of files....................................Passed
check yaml..........................................Passed
check for added large files.........................Passed
ruff format (Poetry)...............................Passed
ruff check (Poetry)................................Passed
mypy (Poetry)......................................Passed
🔒 Security Scan (Bandit)..........................Passed

[main abc1234] feat: add new feature
 3 files changed, 45 insertions(+), 2 deletions(-)
```

✅ **Success!** Your commit was created and is safe to push.

### Scenario 2: Security Issue Found

```bash
$ git add .
$ git commit -m "fix: update API endpoint"

trim trailing whitespace............................Passed
fix end of files....................................Passed
check yaml..........................................Passed
🔒 Security Scan (Bandit)..........................Failed

>> Issue: [B104:hardcoded_bind_all_interfaces]
   Possible binding to all interfaces.
   Location: app/api/main.py:100

hookid: bandit
```

❌ **Blocked!** Fix the security issue before committing.

**Fix options:**

1. **Fix the issue** (preferred):

   ```python
   # Before
   app.run(host="0.0.0.0")  # Security issue!

   # After
   import os
   app.run(host=os.getenv("API_HOST", "127.0.0.1"))
   ```

2. **Add nosec if false positive**:

   ```python
   app.run(host="0.0.0.0")  # nosec B104 - Docker container, intentional
   ```

3. **Run fix tools**:

   ```bash
   # Auto-fix what's possible
   poetry run ruff check --fix .

   # Or use Makefile
   make format-python
   ```

### Scenario 3: Bypassing Hooks (NOT RECOMMENDED)

```bash
$ git commit --no-verify -m "WIP: work in progress"
```

⚠️ **WARNING**: This bypasses all local security checks!

**Consequences:**

- Local hooks won't run
- CI will still catch the issues
- PR cannot be merged until fixed
- Wastes CI time and resources

**When it's acceptable:**

- Work-in-progress commits on feature branch
- You have approval from security lead
- You plan to fix before PR
- You document the reason

**Better alternatives:**

```bash
# Option 1: Fix issues first
make format-python
git commit -m "fix: proper commit"

# Option 2: Use WIP branch
git checkout -b wip/my-feature
git commit --no-verify -m "WIP: experimenting"
# Fix later before merging
```

## Troubleshooting

### Problem: Hooks Don't Run

**Check installation:**

```bash
# Should show pre-commit version
poetry run pre-commit --version

# Should show the hook
ls -la .git/hooks/pre-commit
```

**Fix:**

```bash
make pre-commit-install
```

### Problem: Hooks Run But With Wrong Python Version

**Symptom:** "module not found" or version mismatch errors

**Fix:**

```bash
# Reinstall hooks with correct Python
poetry run pre-commit uninstall
poetry run pre-commit install
poetry run pre-commit install --hook-type pre-push
```

### Problem: Hooks Are Slow

**Quick checks only:**

```bash
./scripts/verify-commit.sh --quick
```

**Or skip non-critical hooks:**

```bash
SKIP=mypy git commit -m "message"
```

⚠️ **Note:** Never skip security checks (`SKIP=bandit` is forbidden)

### Problem: False Positive Security Finding

1. **Verify it's truly a false positive**

   - Read the Bandit warning carefully
   - Check the CWE link for details
   - Consult with a senior developer

2. **Add nosec comment with explanation**

   ```python
   # This is safe because [clear explanation]
   code_here()  # nosec B### - [justification]
   ```

3. **Document in code review**
   - Explain why it's safe
   - Link to relevant documentation
   - Get approval from reviewer

## Available Commands

### Quick Reference

```bash
# Setup
make pre-commit-install    # Install all hooks
make git-configure         # Configure git settings

# Running Checks
make pre-commit-run        # Run all hooks manually
make verify-commit         # Comprehensive verification
make verify-commit-quick   # Quick critical checks
make verify-commit-security # Security checks only
make security-scan         # Just Bandit

# Maintenance
make pre-commit-update     # Update hooks to latest
make git-unconfigure       # Remove git configuration
```

### Detailed Command Guide

| Command                       | What It Does                 | When To Use                   |
| ----------------------------- | ---------------------------- | ----------------------------- |
| `make pre-commit-install`     | Installs commit + push hooks | Initial setup, after clone    |
| `make pre-commit-run`         | Manually runs all hooks      | Before committing, debugging  |
| `make pre-commit-update`      | Updates hook versions        | Monthly maintenance           |
| `make verify-commit`          | Full verification suite      | Before important commits      |
| `make verify-commit-quick`    | Fast critical checks         | Quick validation              |
| `make verify-commit-security` | Security scan only           | After security changes        |
| `make security-scan`          | Bandit scan                  | Investigating security issues |
| `make git-configure`          | Sets up git template         | Initial setup                 |
| `make format-python`          | Auto-format code             | Fixing format issues          |
| `make lint-all`               | All linters                  | Before PR                     |

## Best Practices

### DO ✅

- ✅ Run `make pre-commit-run` before committing large changes
- ✅ Fix security issues immediately when found
- ✅ Add clear justifications for nosec comments
- ✅ Keep hooks updated monthly: `make pre-commit-update`
- ✅ Review security warnings carefully
- ✅ Use the commit template for clear commit messages
- ✅ Test locally before pushing: `./scripts/verify-commit.sh`

### DON'T ❌

- ❌ Use `git commit --no-verify` without approval
- ❌ Skip security hooks (`SKIP=bandit`)
- ❌ Add nosec without explanation
- ❌ Commit hardcoded secrets or API keys
- ❌ Ignore security warnings without investigation
- ❌ Bypass hooks to save time (CI will catch it anyway)
- ❌ Disable hooks globally (`pre-commit uninstall`)

## Understanding Security Findings

### Security Severity Levels

| Level      | Meaning                      | Action                             |
| ---------- | ---------------------------- | ---------------------------------- |
| **HIGH**   | Critical security flaw       | ❌ Must fix before commit          |
| **MEDIUM** | Significant security concern | ❌ Must fix or add justified nosec |
| **LOW**    | Minor security issue         | ⚠️ Should fix or document          |

### Common Security Issues

#### 1. Hardcoded Secrets

```python
# ❌ BAD
# gitleaks:allow
API_KEY = "sk_live_abc123"
PASSWORD = "admin123"

# ✅ GOOD
import os
API_KEY = os.getenv("API_KEY")
PASSWORD = os.getenv("PASSWORD")
```

#### 2. SQL Injection

```python
# ❌ BAD
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# ✅ GOOD
query = "SELECT * FROM users WHERE name = :name"
db.execute(query, {"name": user_input})
```

#### 3. Insecure Deserialization

```python
# ❌ BAD
import pickle
data = pickle.load(untrusted_file)

# ✅ GOOD (if must use pickle)
import pickle
# Only load trusted internal cache files
data = pickle.load(internal_cache)  # nosec B301 - internal cache only
```

#### 4. Binding to All Interfaces

```python
# ❌ BAD (in production)
app.run(host="0.0.0.0")

# ✅ GOOD
import os
app.run(host=os.getenv("API_HOST", "127.0.0.1"))
```

## Getting Help

If you encounter issues:

1. **Check documentation**: Read [`SECURITY.md`](../SECURITY.md)
2. **Run diagnostics**: `./scripts/verify-commit.sh --help`
3. **Check logs**: `poetry run pre-commit run --all-files --verbose`
4. **Ask for help**: Contact the security team or senior developers

## Resources

- [SECURITY.md](../SECURITY.md) - Comprehensive security policy
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Pre-Commit Documentation](https://pre-commit.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

---

**Remember:** These tools are here to help you write secure code. They're not obstacles—they're guardrails that keep us all safe! 🔒
