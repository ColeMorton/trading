# Linting Issues Resolution Plan

## Executive Summary

<summary>
  <objective>Systematically resolve all linting issues identified by the comprehensive linting system to establish a clean code baseline</objective>
  <approach>Prioritized, phased approach starting with blocking issues, then security concerns, and finally code quality improvements</approach>
  <expected-outcome>Clean codebase passing all linting checks, enabling enforcement of code quality standards via pre-commit hooks</expected-outcome>
</summary>

## Current State Analysis

### Issue Summary

1. **2 Syntax Errors** - Blocking Black formatter and Vulture
2. **752 Security Issues** - Identified by Bandit (many false positives)
3. **Thousands of Code Quality Issues** - Flake8 violations
4. **Unknown Type Issues** - MyPy not yet run due to blockers
5. **Unknown Code Analysis Issues** - Pylint not yet run

### Impact Assessment

- **Syntax errors**: Preventing code formatting and dead code detection
- **Security issues**: Mix of real concerns and false positives in test/vendor code
- **Code quality**: Affecting readability and maintainability

## Phase Breakdown

<phase number="1">
  <objective>Fix critical syntax errors blocking formatters</objective>
  <scope>Two f-string syntax errors preventing Black and Vulture from running</scope>
  <dependencies>None - must be completed first</dependencies>
  <implementation>
    <step>Fix app/strategies/ma_cross/1_scanner.py:137 - escape quotes in f-string</step>
    <step>Fix app/strategies/geometric_brownian_motion/2_extract_simulations.py:128 - escape quotes in f-string</step>
    <step>Run Black formatter to auto-fix all formatting issues</step>
    <step>Verify Vulture can now run successfully</step>
  </implementation>
  <deliverables>
    - Working Black formatter
    - Working Vulture dead code detector
    - Auto-formatted codebase
  </deliverables>
  <risks>
    - Black may make extensive changes (mitigation: review changes carefully)
  </risks>
</phase>

<phase number="2">
  <objective>Address critical security issues</objective>
  <scope>Triage and fix high-priority security vulnerabilities from Bandit</scope>
  <dependencies>Phase 1 completion for proper code formatting</dependencies>
  <implementation>
    <step>Configure Bandit to exclude vendor code (app/trading_bot/trendspider/)</step>
    <step>Add nosec comments for test files with intentional private keys</step>
    <step>Replace deprecated Crypto library usage with cryptography library</step>
    <step>Fix any genuine security issues (SQL injection, hardcoded passwords)</step>
    <step>Update .bandit configuration with appropriate exclusions</step>
  </implementation>
  <deliverables>
    - Bandit configuration excluding false positives
    - Fixed genuine security vulnerabilities
    - Documentation of security exemptions
  </deliverables>
  <risks>
    - Breaking changes when replacing crypto libraries (mitigation: thorough testing)
  </risks>
</phase>

<phase number="3">
  <objective>Fix code quality issues systematically</objective>
  <scope>Address Flake8 violations in priority order</scope>
  <dependencies>Phases 1-2 completion</dependencies>
  <implementation>
    <step>Run automated fixes for whitespace issues (trailing whitespace, blank lines)</step>
    <step>Fix unused imports using autoflake or manual removal</step>
    <step>Address line length violations (split long lines, refactor if needed)</step>
    <step>Fix docstring formatting issues (D200, D401, etc.)</step>
    <step>Replace bare except clauses with specific exceptions</step>
    <step>Fix f-string placeholder issues</step>
  </implementation>
  <deliverables>
    - Clean Flake8 output
    - Properly formatted docstrings
    - No unused imports
    - Specific exception handling
  </deliverables>
  <risks>
    - Time-consuming manual fixes (mitigation: use automation where possible)
  </risks>
</phase>

<phase number="4">
  <objective>Enable and fix type checking issues</objective>
  <scope>Run MyPy and fix type annotation issues</scope>
  <dependencies>Phase 3 completion for clean syntax</dependencies>
  <implementation>
    <step>Run MyPy to identify type issues</step>
    <step>Add type annotations to function signatures</step>
    <step>Fix any type mismatches</step>
    <step>Configure MyPy to ignore third-party libraries without stubs</step>
    <step>Add type: ignore comments for legitimate dynamic typing</step>
  </implementation>
  <deliverables>
    - Type-annotated codebase
    - Clean MyPy output
    - Improved IDE support
  </deliverables>
  <risks>
    - Extensive type annotations needed (mitigation: prioritize public APIs)
  </risks>
</phase>

<phase number="5">
  <objective>Complete code analysis and cleanup</objective>
  <scope>Run Pylint and Vulture, address findings</scope>
  <dependencies>Phases 1-4 completion</dependencies>
  <implementation>
    <step>Run Pylint and categorize issues by severity</step>
    <step>Fix high-priority Pylint issues (errors, critical warnings)</step>
    <step>Run Vulture to find dead code</step>
    <step>Remove or document intentionally unused code</step>
    <step>Configure tool-specific ignore rules for false positives</step>
  </implementation>
  <deliverables>
    - Clean Pylint output (or documented exemptions)
    - Removed dead code
    - Leaner codebase
  </deliverables>
  <risks>
    - Removing code that appears dead but isn't (mitigation: careful review, tests)
  </risks>
</phase>

<phase number="6">
  <objective>Establish monitoring and maintenance</objective>
  <scope>Set up processes to maintain code quality</scope>
  <dependencies>All previous phases complete</dependencies>
  <implementation>
    <step>Enable pre-commit hooks for all developers</step>
    <step>Document linting standards in CONTRIBUTING.md</step>
    <step>Set up CI/CD linting gates</step>
    <step>Create linting exception process and documentation</step>
    <step>Schedule regular linting rule reviews</step>
  </implementation>
  <deliverables>
    - Active pre-commit enforcement
    - CI/CD quality gates
    - Team documentation
    - Maintenance process
  </deliverables>
  <risks>
    - Developer friction (mitigation: good documentation, gradual enforcement)
  </risks>
</phase>

## Specific Issue Resolutions

### 1. F-String Syntax Errors

**Issue**: Nested quotes in f-strings causing syntax errors

**File**: `app/strategies/ma_cross/1_scanner.py:137`

```python
# Current (broken):
log(f"Loaded scanner list: {config["PORTFOLIO"]}")

# Fixed:
log(f"Loaded scanner list: {config['PORTFOLIO']}")
```

**File**: `app/strategies/geometric_brownian_motion/2_extract_simulations.py:128`

```python
# Current (broken):
simulations_df.to_csv(f'csv/geometric_brownian_motion/{config['TICKER']}_gbm_extracted_simulations.csv')

# Fixed:
simulations_df.to_csv(f"csv/geometric_brownian_motion/{config['TICKER']}_gbm_extracted_simulations.csv")
```

### 2. Security Issues Prioritization

**High Priority (Fix Required)**:

- Deprecated `Crypto` library usage → Migrate to `cryptography`
- Hardcoded passwords/tokens → Use environment variables
- SQL injection risks → Use parameterized queries
- Weak hashing (SHA1) → Use SHA256 or better

**Low Priority (Document/Ignore)**:

- Test file private keys → Add `# nosec` comments
- Vendor library issues → Exclude from scanning
- Assert statements → Acceptable in non-production code

### 3. Code Quality Automation

**Automated Fixes**:

```bash
# Remove trailing whitespace
find app tests -name "*.py" -exec sed -i '' 's/[[:space:]]*$//' {} \;

# Fix import ordering (already done by isort)
poetry run isort app tests

# Remove unused imports
poetry run autoflake --in-place --remove-unused-variables app tests

# Format with Black (after syntax fixes)
poetry run black app tests
```

**Manual Fixes Required**:

- Docstring formatting (add periods, use imperative mood)
- Long line splitting (refactor complex expressions)
- Bare except replacement (specify exception types)
- F-string placeholders (add missing variables)

## Success Metrics

1. **Phase 1**: Black runs successfully, all code formatted
2. **Phase 2**: Bandit shows <10 high-severity issues (all documented)
3. **Phase 3**: Flake8 shows 0 errors, <50 warnings
4. **Phase 4**: MyPy runs with 0 errors
5. **Phase 5**: Pylint score >8.0/10
6. **Phase 6**: Pre-commit hooks passing on all commits

## Implementation Timeline

- **Phase 1**: 30 minutes (quick syntax fixes)
- **Phase 2**: 2-4 hours (security triage and fixes)
- **Phase 3**: 4-6 hours (code quality fixes)
- **Phase 4**: 3-4 hours (type annotations)
- **Phase 5**: 2-3 hours (final cleanup)
- **Phase 6**: 1-2 hours (documentation)

**Total**: 12-20 hours of focused work

## Quick Start Commands

```bash
# Phase 1: Fix syntax errors and format
# (Manual fixes required first, then:)
make format-python

# Phase 2: Security scan
make security-scan

# Phase 3: Check code quality
make lint-flake8

# Phase 4: Type checking
make lint-mypy

# Phase 5: Complete analysis
make lint-all

# Verify everything
make pre-commit-run
```

## Notes

- Start with Phase 1 immediately - it unblocks everything else
- Many issues will be auto-fixed by Black once it can run
- Focus on real issues, not style preferences
- Document exemptions rather than disabling tools
- Consider gradual enforcement for large legacy sections
