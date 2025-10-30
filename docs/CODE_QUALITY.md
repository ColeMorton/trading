# Code Quality Standards

This document outlines the code quality standards and automated quality gates for the trading project.

## Overview

The project uses a comprehensive suite of static analysis tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter (replaces black, isort, flake8)
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **radon**: Complexity and maintainability analysis
- **vulture**: Dead code detection
- **import-linter**: Architecture contract enforcement

## Automated Quality Gates

### Pre-commit Hooks

All commits are automatically checked for:

1. **Formatting (Ruff)**: Code must be properly formatted
2. **Linting (Ruff)**: No style violations or simple bugs
3. **Type Checking (mypy)**: Type hints validated (gradual adoption)
4. **Security (bandit)**: No security vulnerabilities
5. **Complexity (radon)**:
   - Cyclomatic Complexity < 20 (Grade C)
   - Maintainability Index > 10 (Grade B)
6. **Dead Code (vulture)**: No unused code (80% confidence)

### Quality Thresholds

| Metric                     | Threshold           | Current (2025-10-30) | Target (3 months) |
| -------------------------- | ------------------- | -------------------- | ----------------- |
| **Cyclomatic Complexity**  | Max 20 per function | 147 violations       | < 50 violations   |
| **Maintainability Index**  | Min 10 per file     | 22 violations        | < 10 violations   |
| **Dead Code**              | Zero tolerance      | 36 instances         | 0 instances       |
| **Architecture Contracts** | All passing         | TBD                  | 0 violations      |

### Understanding the Metrics

#### Cyclomatic Complexity (CC)

Measures the number of independent paths through code:

- **A (1-5)**: Simple, easy to understand
- **B (6-10)**: Moderate complexity
- **C (11-20)**: Complex, requires refactoring consideration
- **D (21-40)**: Very complex, **hard to test**
- **F (40+)**: Unmaintainable, **must refactor**

**Our Threshold**: Grade C (CC < 20)

#### Maintainability Index (MI)

Composite metric based on complexity, volume, and comments:

- **A (20-100)**: Good maintainability
- **B (10-20)**: Poor maintainability
- **C (0-10)**: Critical, urgent refactoring needed

**Our Threshold**: Grade B (MI > 10)

#### Dead Code Detection

Identifies:

- Unused functions, methods, classes
- Unused variables and imports
- Unreachable code after returns

**Our Threshold**: Zero tolerance (min 80% confidence)

## Developer Workflow

### Local Development

```bash
# Before committing - auto-fix issues
make format-python

# Check quality
make lint-python

# Full analysis
make lint-all

# Specific analysis
make analyze-complexity
make analyze-maintainability
make analyze-dependencies
make analyze-architecture
```

### Pre-commit Integration

Pre-commit hooks run automatically on `git commit`:

```bash
# Install hooks (one-time setup)
make pre-commit-install

# Run hooks manually
make pre-commit-run

# Update hook versions
make pre-commit-update
```

### Bypassing Hooks (Emergency Only)

In rare emergencies, you can skip hooks:

```bash
# Skip specific hook
SKIP=radon-complexity git commit -m "Emergency hotfix"

# Skip all hooks (strongly discouraged)
git commit --no-verify -m "Emergency fix"
```

**WARNING**: CI will still enforce all quality gates. Bypassing hooks only delays issues.

### Fixing Violations

#### High Complexity (CC > 20)

**Strategies**:

1. **Extract Method**: Break large functions into smaller ones
2. **Early Returns**: Reduce nested conditionals
3. **Strategy Pattern**: Replace complex conditionals with polymorphism
4. **Guard Clauses**: Handle edge cases early

**Example**:

```python
# BAD: High complexity (CC = 25)
def process_order(order):
    if order.is_valid():
        if order.has_inventory():
            if order.payment_successful():
                if order.shipping_available():
                    # 20 more lines of nested logic...
                    return True
    return False

# GOOD: Reduced complexity (CC = 5)
def process_order(order):
    if not order.is_valid():
        return False
    if not order.has_inventory():
        return False
    if not order.payment_successful():
        return False
    if not order.shipping_available():
        return False

    return _complete_order_processing(order)

def _complete_order_processing(order):
    # Extracted logic here
    return True
```

#### Low Maintainability (MI < 10)

**Common causes**:

- File too long (> 500 lines)
- God objects (too many responsibilities)
- Lack of abstraction
- Deep nesting

**Solutions**:

- Split into multiple files/modules
- Extract classes or functions
- Add docstrings and comments
- Simplify complex logic

#### Dead Code

**Removal strategy**:

1. Verify code is truly unused
2. Check if it's part of a public API
3. Remove with confidence (git preserves history)

```bash
# Find dead code
make find-dead-code

# Review findings
poetry run vulture app/ --min-confidence 80 > dead-code-report.txt
```

## Architecture Contracts

The project enforces architectural boundaries using import-linter.

### Configured Contracts

1. **Layered Architecture**: UI → Application → Domain → Infrastructure
2. **Strategy Independence**: Strategy modules don't depend on each other
3. **Database Layer Isolation**: Direct SQLAlchemy access restricted
4. **CLI Independence**: CLI commands don't depend on each other
5. **API-CLI Separation**: API doesn't import from CLI

### Checking Contracts

```bash
# Check all contracts
make analyze-architecture

# Verbose output
poetry run lint-imports --verbose

# Show dependency graph
make analyze-dependencies
```

### Contract Configuration

See [`.importlinter`](../.importlinter) for detailed contract definitions.

## CI/CD Integration

### GitHub Actions Quality Gates

The CI pipeline runs quality analysis on every push:

1. **Lint Job**:

   - Ruff format + lint
   - mypy type checking
   - bandit security scan
   - **radon complexity analysis** (non-blocking)
   - **vulture dead code detection** (non-blocking)
   - **import-linter architecture** (non-blocking)

2. **Test Jobs**: Unit, integration, E2E tests

3. **CI Summary**: Quality metrics dashboard

### Phased Enforcement

**Current Phase (Week 1-2)**: Visibility only

- Complexity, dead code, architecture checks are **non-blocking**
- Violations are reported but don't fail CI
- Track metrics to establish baseline

**Next Phase (Week 3-4)**: Progressive enforcement

- Enable blocking for new violations
- Fix existing violations incrementally

**Final Phase (Week 5+)**: Full enforcement

- All quality gates block CI
- Zero tolerance for new violations

## Tracking Metrics Over Time

```bash
# Collect current metrics
poetry run python scripts/track_quality_metrics.py

# View history
cat data/analysis/quality-history.jsonl | tail -10 | jq '.'

# Generate trend report (TODO: implement)
poetry run python scripts/quality_trends.py
```

### Metrics Storage

Metrics are stored in `data/analysis/quality-history.jsonl`:

```json
{
  "timestamp": "2025-10-30T...",
  "git_sha": "abc123...",
  "branch": "main",
  "complexity": { "high_complexity_functions": 147 },
  "maintainability": { "low_mi_files": 22 },
  "dead_code": { "instances": 36 },
  "architecture": { "broken_contracts": 0 }
}
```

## IDE Integration

### VS Code

Recommended extensions:

- **Python** (Microsoft): Linting, formatting, debugging
- **Ruff** (Astral Software): Fast linting
- **mypy** (Matan Gover): Type checking integration

Settings (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.banditEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## Best Practices

### 1. Write Simple Code

- Keep functions small (< 50 lines)
- Limit cyclomatic complexity (< 10 ideal, < 20 max)
- Avoid deep nesting (max 3 levels)

### 2. Remove Dead Code Immediately

- Don't comment out code "just in case"
- Git preserves history - delete with confidence
- Run `make find-dead-code` regularly

### 3. Refactor Incrementally

- Don't create "refactor branches" that diverge
- Improve code quality with each change
- Use metrics to prioritize refactoring efforts

### 4. Monitor Trends

- Track metrics weekly
- Celebrate improvements
- Address regressions quickly

## Getting Help

### Common Issues

**Q: Pre-commit hook taking too long?**

- Run `pre-commit run --files app/specific/file.py` for single files
- Use `SKIP=mypy git commit` to skip slow checks temporarily

**Q: How to fix "High complexity" error?**

- See [Fixing Violations](#fixing-violations) above
- Use `make analyze-complexity` to see detailed report

**Q: Architecture contract violations?**

- Run `poetry run lint-imports --verbose` for details
- Review [`.importlinter`](../.importlinter) contracts
- Refactor imports to respect boundaries

### Resources

- **Radon docs**: https://radon.readthedocs.io/
- **Vulture docs**: https://github.com/jendrikseipp/vulture
- **Import Linter**: https://import-linter.readthedocs.io/
- **Ruff docs**: https://docs.astral.sh/ruff/

### Support Channels

- **Issues**: [GitHub Issues](https://github.com/ColeMorton/trading/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ColeMorton/trading/discussions)
- **Documentation**: [docs/](../)

---

_Last updated: 2025-10-30_
_Next review: 2025-11-30_
