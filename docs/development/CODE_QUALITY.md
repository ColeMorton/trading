# Code Quality and Formatting Guide

This project uses modern Python code quality tools to maintain consistent, readable, and error-free code.

## Quick Start (5 Minutes)

### Step 1: Auto-Fix Safe Issues

```bash
make quality-fix-safe
```

**Result**: Automatically fixes 800+ issues!

### Step 2: Format Code

```bash
make format-python
```

**Result**: Formats all code with Black and isort

### Step 3: Check Remaining Issues

```bash
make quality-analyze
```

**Result**: Shows categorized breakdown of issues

### Step 4: Track Progress

```bash
make quality-track
```

**Result**: Saves snapshot for tracking improvements

## Tools Overview

### Black (Code Formatter)

- **Purpose**: Auto-format Python code to consistent style
- **Line length**: 88 characters
- **Why**: Eliminates style debates, ensures consistency

### isort (Import Sorter)

- **Purpose**: Automatically sort and organize imports
- **Configuration**: Black-compatible profile
- **Why**: Keeps imports organized, reduces merge conflicts

### Ruff (Linter)

- **Purpose**: Fast, comprehensive Python linter
- **Replaces**: flake8, pyflakes, pycodestyle, parts of pylint
- **Speed**: 10-100x faster than traditional tools
- **Coverage**: Errors, code smells, security issues, and more

### Additional Tools

- **mypy**: Static type checking
- **pylint**: Code quality analysis
- **bandit**: Security vulnerability scanning
- **vulture**: Dead code detection

## Daily Commands

### Formatting (Auto-fix)

```bash
make format-black          # Auto-format code
make format-isort         # Auto-sort imports
make format-ruff          # Auto-fix Ruff issues
make format-python        # All of the above
```

### Linting (Check only)

```bash
make lint-black           # Check formatting
make lint-isort          # Check imports
make lint-ruff           # Check Ruff issues
make lint-mypy           # Type checking
make lint-python         # All linting checks
```

### Code Quality Improvement

```bash
make quality-analyze      # Show all issues by category
make quality-fix-safe     # Auto-fix safe issues
make quality-track        # Track progress over time
make quality-status       # Quick status check
```

### Complete Workflow

```bash
make lint-all            # Format + lint + security scan
```

## Configuration

All tools are configured in `pyproject.toml`:

### Black

```toml
[tool.black]
line-length = 88
target-version = ['py310']
```

### isort

```toml
[tool.isort]
profile = "black"
line_length = 88
```

### Ruff

Enabled rule categories (17 total):

- **E, W**: pycodestyle errors and warnings
- **F**: Pyflakes (undefined variables, unused imports)
- **I**: isort (import sorting)
- **N**: pep8-naming conventions
- **UP**: pyupgrade (modernize syntax)
- **B**: flake8-bugbear (common bugs)
- **C4**: flake8-comprehensions
- **SIM**: flake8-simplify
- **RET**: flake8-return
- **PTH**: flake8-use-pathlib
- **TD, FIX**: TODOs and FIXME comments
- **ERA**: Eradicate commented-out code
- **PL**: pylint rules
- **RUF**: Ruff-specific rules

## Pre-commit Hooks

Pre-commit hooks automatically run checks before each commit.

### Installation

```bash
make pre-commit-install
```

### Manual Run

```bash
make pre-commit-run
```

### What Runs on Commit

1. Trailing whitespace removal
2. End-of-file fixer
3. YAML/JSON/TOML validation
4. isort (import sorting)
5. Black (code formatting)
6. Ruff (linting with auto-fix)
7. mypy (type checking)
8. bandit (security scanning)

## Recommended Workflow

### For New Code

```bash
# Write your code
vim app/my_module.py

# Format and check
make format-python
make lint-python

# Or run everything
make lint-all
```

### Before Committing

```bash
# Run all checks
make lint-all

# Or just commit (pre-commit runs automatically)
git add .
git commit -m "Your message"
```

## Common Issues and Fixes

### Unused Variables (F841)

```python
# Bad
result = compute()  # Never used

# Good - Use it
result = compute()
return result

# Good - Remove it
compute()

# Good - Mark as intentionally unused
_result = compute()
```

### Boolean Comparison (E712)

```python
# Bad
if result == True:

# Good
if result:
```

### Unused Loop Variable (B007)

```python
# Bad
for i in range(10):
    do_something()

# Good
for _ in range(10):
    do_something()
```

### Modern Type Hints (UP038)

```python
# Old
isinstance(x, (int, float))

# Modern (Python 3.10+)
isinstance(x, int | float)
```

### Use pathlib (PTH123)

```python
# Old
with open(filename) as f:
    content = f.read()

# Modern
from pathlib import Path
with Path(filename).open() as f:
    content = f.read()
```

### Implicit Optional (RUF013)

```python
# Bad
def func(value: str = None):

# Good
def func(value: str | None = None):
```

## Gradual Improvement Strategy

### Current Status

- **Total Issues**: ~2,900
- **Auto-fixable**: ~400
- **High Priority**: ~500

### Recommended Order

#### Week 1: Quick Wins

```bash
make quality-fix-safe
make quality-track
```

**Target**: Reduce to <2,500 issues

#### Week 2-3: Critical Fixes

Fix F (Pyflakes) issues manually
**Target**: Reduce to <2,000 issues

#### Month 2-3: Quality Improvements

Fix B, PTH, SIM issues gradually
**Target**: Reduce to <1,500 issues

#### Ongoing: Maintenance

- Fix issues as you work on files
- Track progress weekly
- Keep new code clean (pre-commit helps!)

## VS Code Integration

Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": false,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll.ruff": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

Install VS Code extensions:

- `ms-python.python`
- `ms-python.black-formatter`
- `charliermarsh.ruff`

## Troubleshooting

### Ruff Conflicts with Black

This shouldn't happen - Ruff is configured to be Black-compatible. E501 (line length) is ignored.

### Too Many Errors

Start with formatting (fixes most issues):

```bash
make format-python
```

### Pre-commit is Slow

First run is slower (downloads hooks). Subsequent runs are cached and fast.

### Need to Skip a Check

```python
# Ignore specific line
long_line = "..."  # noqa: E501

# Ignore specific rule
from unused import something  # noqa: F401
```

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules Reference](https://docs.astral.sh/ruff/rules/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Ruff Quick Reference](RUFF_REFERENCE.md)
- [Code Quality Improvement Guide](CODE_QUALITY_IMPROVEMENT.md)

## Philosophy

1. **Consistency over preference**: Black formats one way, eliminating debates
2. **Automation over manual work**: Let tools handle formatting and basic checks
3. **Fast feedback**: Ruff provides instant linting
4. **Gradual adoption**: Warnings don't block commits, encourage improvements
5. **Pragmatic over perfect**: Some rules disabled when they don't add value

---

**Questions?** Run `make lint-help` for all available commands.
