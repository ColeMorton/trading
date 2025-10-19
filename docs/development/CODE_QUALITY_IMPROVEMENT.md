# Code Quality Improvement Guide

## Overview

This guide helps you systematically improve code quality using the gradual fix script.

## Current Status

**Total Issues**: 4,718

### Priority Breakdown

| Priority | Category            | Count   | Auto-fix | Description                                           |
| -------- | ------------------- | ------- | -------- | ----------------------------------------------------- |
| 🔴 **1** | **F** (Pyflakes)    | **504** | ✗        | Undefined variables, unused imports - **likely bugs** |
| 🟡 **2** | **B** (bugbear)     | **437** | ✗        | Common bugs and anti-patterns                         |
| 🟡 **2** | **UP** (pyupgrade)  | **263** | ✓        | Modernize syntax (safe to auto-fix)                   |
| 🔵 **3** | PTH (pathlib)       | 748     | ✗        | Use pathlib instead of os.path                        |
| 🔵 **3** | RUF (Ruff-specific) | 344     | ✗        | Ruff-specific rules                                   |
| 🔵 **3** | SIM (simplify)      | 185     | ✗        | Code simplification                                   |
| ⚪ **4** | E (pycodestyle)     | 520     | ✓        | Style errors (safe to auto-fix)                       |
| ⚪ **4** | W (pycodestyle)     | 63      | ✓        | Style warnings (safe to auto-fix)                     |

## Quick Start Guide

### 1. Analyze Current State

```bash
python scripts/fix_code_quality.py --analyze
```

This shows:

- Total issues
- Issues by category
- Top 10 most common issues
- Top 10 files with most issues
- Recommendations

### 2. Fix Safe Issues First (Quick Win!)

```bash
python scripts/fix_code_quality.py --fix-safe
```

This auto-fixes:

- **UP** rules (modernize syntax like `Dict` → `dict`)
- **E/W** rules (style issues)
- Other safe transformations

**Expected result**: ~800+ issues fixed automatically!

### 3. Track Your Progress

```bash
python scripts/fix_code_quality.py --track
```

This creates a history file to track improvements over time.

## Recommended Fix Order

### Phase 1: Quick Wins (Auto-fixable) 🚀

```bash
# Fix all safe issues
python scripts/fix_code_quality.py --fix-safe

# Re-analyze to see what's left
python scripts/fix_code_quality.py --analyze

# Track progress
python scripts/fix_code_quality.py --track
```

**Expected**: Fixes ~800-1000 issues (20-25% of total)

### Phase 2: Critical Issues (High Priority) 🔴

Focus on **F** (Pyflakes) issues - these are likely bugs!

```bash
# Show what F issues exist
python scripts/fix_code_quality.py --show-category F

# Top F issues to fix:
# - F841: Unused variables (314 occurrences)
# - F401: Unused imports
# - F811: Redefined names
```

**Manual fix required** - these need careful review:

#### F841: Unused Variables

```python
# Before
result = expensive_computation()
# ... but result is never used

# Fix 1: Remove if not needed
expensive_computation()

# Fix 2: Use if needed
result = expensive_computation()
assert result is not None
```

#### F401: Unused Imports

```python
# Before
from typing import Dict, List, Optional  # Optional unused

# Fix: Remove unused
from typing import Dict, List
```

### Phase 3: Bug Prevention (Medium Priority) 🟡

Focus on **B** (bugbear) issues:

```bash
python scripts/fix_code_quality.py --show-category B
```

Common issues:

- **B904**: Missing `from err` in exception raising
- **B007**: Unused loop variable (use `_` instead)
- **B006**: Mutable default arguments

### Phase 4: Code Simplification (Lower Priority) 🔵

These improve code quality but aren't urgent:

```bash
# Show specific categories
python scripts/fix_code_quality.py --show-category SIM
python scripts/fix_code_quality.py --show-category PTH
```

## Target-Specific Fixes

### Fix a Specific File

```bash
python scripts/fix_code_quality.py --fix-file app/api/services/queue_service.py
```

### Fix a Specific Directory

```bash
python scripts/fix_code_quality.py --fix-file app/api/
```

### Fix a Specific Category

```bash
# Auto-fix modernization issues
python scripts/fix_code_quality.py --fix-category UP

# Fix specific bugbear issues
python scripts/fix_code_quality.py --fix-category B
```

## Common Issues and Solutions

### Issue: E712 - Comparison to True/False

```python
# ❌ Bad
if result == True:
    pass

# ✅ Good
if result:
    pass
```

### Issue: F841 - Unused Variable

```python
# ❌ Bad
def process():
    result = compute_something()  # Never used
    return None

# ✅ Good (Option 1: Use it)
def process():
    result = compute_something()
    return result

# ✅ Good (Option 2: Remove it)
def process():
    compute_something()
    return None

# ✅ Good (Option 3: Prefix with _ to indicate intentionally unused)
def process():
    _result = compute_something()
    return None
```

### Issue: B007 - Unused Loop Variable

```python
# ❌ Bad
for i in range(10):
    do_something()  # i is never used

# ✅ Good
for _ in range(10):
    do_something()
```

### Issue: UP038 - Modern isinstance

```python
# ❌ Old style
isinstance(x, (int, float))

# ✅ Modern (Python 3.10+)
isinstance(x, int | float)
```

### Issue: PTH123 - Use pathlib

```python
# ❌ Old style
with open(filename) as f:
    content = f.read()

# ✅ Modern
from pathlib import Path

with Path(filename).open() as f:
    content = f.read()
```

### Issue: RUF013 - Implicit Optional

```python
# ❌ Implicit
def func(value: str = None):
    pass

# ✅ Explicit
def func(value: str | None = None):
    pass
```

## Weekly Improvement Plan

### Week 1: Foundation

1. Run `--fix-safe` to auto-fix 800+ issues
2. Track baseline with `--track`
3. Target: Reduce from 4,718 to ~3,900 issues

### Week 2-3: Critical Fixes

1. Fix all F841 (unused variables) - 314 issues
2. Fix F401 (unused imports)
3. Target: Reduce to ~3,400 issues

### Week 4-5: Bug Prevention

1. Fix B904 (exception handling) - 182 issues
2. Fix B007 (loop variables)
3. Target: Reduce to ~3,000 issues

### Week 6-8: Code Quality

1. Gradually fix PTH (pathlib) issues
2. Fix SIM (simplification) issues
3. Target: Reduce to ~2,000 issues

### Ongoing: Maintain Quality

1. Run `--track` weekly to monitor progress
2. Fix issues in new code immediately
3. Set up CI to prevent new issues

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/quality.yml
- name: Check code quality
  run: |
    python scripts/fix_code_quality.py --analyze
    # Fail if issues increase
```

## Tips for Success

### 1. Fix by File, Not by Issue Type

Instead of fixing all F841s everywhere, fix all issues in one file:

```bash
# Better approach
python scripts/fix_code_quality.py --fix-file app/api/services/

# Than this
python scripts/fix_code_quality.py --fix-category F
```

### 2. Use Your IDE

Most issues show up in your IDE. Fix them as you work on files naturally.

### 3. Don't Perfect Everything at Once

- Focus on high-priority issues (F, B)
- Lower priority issues (PTH, SIM) can be fixed gradually
- New code should be clean; old code can improve over time

### 4. Regular Progress Tracking

```bash
# Every Friday
python scripts/fix_code_quality.py --track
```

This shows your progress and keeps you motivated!

### 5. Ignore Where Necessary

Some issues are false positives. Add `# noqa: CODE` when needed:

```python
# This is intentionally unused for API compatibility
def deprecated_method():  # noqa: F841
    pass
```

## Expected Timeline

| Phase              | Duration | Issues Fixed | Remaining |
| ------------------ | -------- | ------------ | --------- |
| Start              | -        | -            | 4,718     |
| Phase 1 (Auto-fix) | 1 hour   | 800-1000     | ~3,900    |
| Phase 2 (Critical) | 2 weeks  | 500          | ~3,400    |
| Phase 3 (Medium)   | 2 weeks  | 400          | ~3,000    |
| Phase 4 (Lower)    | 4 weeks  | 1,000        | ~2,000    |
| Maintenance        | Ongoing  | -            | <100/week |

## Success Metrics

### Short-term (1 month)

- ✅ All auto-fixable issues resolved
- ✅ Zero F (Pyflakes) issues in app/api/
- ✅ All new code passes Ruff checks

### Medium-term (3 months)

- ✅ <2,000 total issues
- ✅ Zero high-priority (F, B) issues
- ✅ All critical paths clean

### Long-term (6 months)

- ✅ <500 total issues
- ✅ All issues are low-priority style preferences
- ✅ Ruff checks in pre-commit prevent new issues

## Getting Help

Run the script without arguments to see current status:

```bash
python scripts/fix_code_quality.py
```

View specific category details:

```bash
python scripts/fix_code_quality.py --show-category F
```

## Additional Resources

- [Ruff Rules Documentation](https://docs.astral.sh/ruff/rules/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [PEP 8 Style Guide](https://pep8.org/)
- Main project guide: `CODE_QUALITY_GUIDE.md`

---

**Remember**: The goal isn't perfection overnight. Focus on preventing new issues and gradually improving existing code!
