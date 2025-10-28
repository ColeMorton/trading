# Naming Conventions Improvement Plan (N806)

**Status:** Planned
**Priority:** Low
**Effort:** 4-5 hours
**Issues:** 253 total (201 in tests/, 54 in app/)

## Overview

Address PEP 8 naming convention violations where variables in functions use PascalCase instead of snake_case. Most violations are in test files where class names are assigned to variables.

## Current State

### Violation Distribution

**Tests (201 issues - 79%):**

- `test_seasonality_analyzer.py`: 57 issues
- `test_seasonality_patterns.py`: 43 issues
- `test_seasonality_exports.py`: 36 issues
- `test_seasonality_auto_download.py`: 26 issues
- `test_seasonality_models.py`: 26 issues
- Other test files: 13 issues

**App Code (54 issues - 21%):**

- `tools/statistical_model_validator.py`: 14 issues
- `strategies/macd/4_macd_cross_psl.py`: 10 issues
- `strategies/jump_diffusion/1_jump_diffusion.py`: 6 issues
- `tools/services/statistical_analysis_service.py`: 6 issues
- Various other files: 18 issues

### Common Patterns

**Pattern 1: Test Fixture Variables (Most Common)**

```python
# Before (N806 violation)
def test_something(self):
    SeasonalityAnalyzer = get_analyzer_class()
    PatternType = get_pattern_type()
    analyzer = SeasonalityAnalyzer()

# After (Compliant)
def test_something(self):
    seasonality_analyzer_class = get_analyzer_class()
    pattern_type_class = get_pattern_type()
    analyzer = seasonality_analyzer_class()

# Alternative (More Pythonic)
def test_something(self):
    analyzer_cls = get_analyzer_class()
    pattern_cls = get_pattern_type()
    analyzer = analyzer_cls()
```

**Pattern 2: Dynamic Class Assignment**

```python
# Before
def create_instance():
    ModelClass = get_model_for_type(model_type)
    return ModelClass(params)

# After
def create_instance():
    model_class = get_model_for_type(model_type)
    return model_class(params)
```

## Implementation Strategy

### Phase 1: Test Files (201 issues, ~3 hours)

**Priority Order:**

1. Seasonality tests (162 issues - 80% of test violations)
2. Metric type tests (5 issues)
3. Best selections tests (3 issues)
4. Other test files (31 issues)

**Approach:**

- Use consistent naming: `{class_name}_class` or `{name}_cls`
- Update all references in the same function
- Run tests after each file to ensure no breakage

**Commands:**

```bash
# After each file fix
poetry run pytest tests/tools/seasonality/test_seasonality_analyzer.py -v
```

### Phase 2: App Code (54 issues, ~1-2 hours)

**Priority Order:**

1. `statistical_model_validator.py` (14 issues)
2. MACD strategies (10 issues)
3. Jump diffusion (6 issues)
4. Services and others (24 issues)

**Approach:**

- Review each instance for logical correctness
- Ensure variable name changes don't affect external interfaces
- Test affected modules

## Risk Assessment

### Low Risk

- Purely style/convention changes
- No logic modifications
- Well-defined patterns

### Medium Risk Areas

- Test fixtures that might be referenced in multiple places
- Dynamic class assignment where variable name might matter
- Any metaprogramming patterns

### Mitigation

1. Fix one file at a time
2. Run tests after each file
3. Commit frequently (per file or small batches)
4. Review diffs carefully for unintended changes

## Execution Checklist

### Preparation

- [ ] Update todos for tracking
- [ ] Create feature branch (optional)
- [ ] Review current git status

### Phase 1: Seasonality Tests

- [ ] Fix test_seasonality_analyzer.py (57 issues)
- [ ] Run tests: `pytest tests/tools/seasonality/test_seasonality_analyzer.py`
- [ ] Fix test_seasonality_patterns.py (43 issues)
- [ ] Run tests: `pytest tests/tools/seasonality/test_seasonality_patterns.py`
- [ ] Fix test_seasonality_exports.py (36 issues)
- [ ] Run tests: `pytest tests/tools/seasonality/test_seasonality_exports.py`
- [ ] Fix test_seasonality_auto_download.py (26 issues)
- [ ] Fix test_seasonality_models.py (26 issues)
- [ ] Commit: "refactor: fix naming conventions in seasonality tests (188 issues)"

### Phase 2: Remaining Tests

- [ ] Fix other test files (13 issues)
- [ ] Run full test suite
- [ ] Commit: "refactor: fix naming conventions in remaining tests (13 issues)"

### Phase 3: App Code

- [ ] Fix statistical_model_validator.py (14 issues)
- [ ] Fix MACD strategies (10 issues)
- [ ] Fix jump_diffusion (6 issues)
- [ ] Fix statistical_analysis_service.py (6 issues)
- [ ] Fix remaining app files (18 issues)
- [ ] Run full test suite
- [ ] Commit: "refactor: fix naming conventions in app code (54 issues)"

### Verification

- [ ] Run full linting: `make lint-python`
- [ ] Verify N806 count: should be 0
- [ ] Run complete test suite: `make test`
- [ ] Review all diffs

### Finalization

- [ ] Update LINTING_IMPROVEMENTS_SUMMARY.md
- [ ] Final commit if needed
- [ ] Push to remote

## Naming Convention Standards

### Recommended Patterns

**For Class Variables in Tests:**

```python
# Pattern A: Explicit (clearest)
analyzer_class = get_analyzer_class()
pattern_type_class = get_pattern_type()

# Pattern B: Short suffix (common)
analyzer_cls = get_analyzer_class()
pattern_cls = get_pattern_type()

# Pattern C: Descriptive (best for complex cases)
seasonality_analyzer_class = get_analyzer_class()
```

**For Dynamic Class Loading:**

```python
# Pattern A: Descriptive
model_class = get_model_for_type(model_type)
instance = model_class(params)

# Pattern B: Generic
cls = get_class_for_name(class_name)
obj = cls()
```

## Expected Outcomes

### After Completion

- **N806 violations:** 253 → 0 (100% resolved)
- **Code consistency:** All variables follow PEP 8
- **Test clarity:** Better variable naming in tests
- **No functional changes:** All tests continue passing

### Benefits

- Improved code readability
- PEP 8 compliance
- Consistency across codebase
- Better IDE autocomplete support

## Time Estimates

| Phase                      | Files  | Issues  | Estimated Time |
| -------------------------- | ------ | ------- | -------------- |
| Phase 1: Seasonality Tests | 5      | 188     | 2.5 hours      |
| Phase 2: Other Tests       | 3      | 13      | 0.5 hours      |
| Phase 3: App Code          | 15     | 54      | 1.5 hours      |
| **Total**                  | **23** | **255** | **4.5 hours**  |

## Notes

- Most violations are in test files (79%)
- Seasonality tests account for 74% of total violations
- Fixing tests first validates the approach
- App code fixes are lower risk (fewer issues per file)
- All changes are mechanical and low-risk

## Automation Potential

**Not Recommended:** While sed/awk could theoretically rename variables, the risk of breaking references is too high. Manual fixes with IDE refactoring support (rename symbol) is safest.

**Tool Support:**

- Use IDE "Rename Symbol" feature where available
- This ensures all references are updated consistently

## Success Criteria

1. All 253 N806 violations resolved
2. All tests continue passing
3. No functional changes introduced
4. Consistent naming pattern applied
5. Code reviewed and committed

---

**Created:** October 28, 2025
**Last Updated:** October 28, 2025
**Status:** Ready for implementation
