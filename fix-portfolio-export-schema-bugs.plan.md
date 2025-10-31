# Fix Portfolio Export Schema Bugs

## Implementation Summary

**Status**: ✅ COMPLETED

All 11 originally failing integration tests now pass. The portfolio export schema configuration has been corrected, and the minimum filtering logic has been fixed.

## Changes Made

### Phase 1: Fix Schema Configuration ✅

**File**: `app/tools/strategy/export_portfolios.py` (lines 150-182)

Fixed the `EXPORT_SCHEMA_CONFIG` to use correct schemas:

1. **portfolios_filtered**: Changed from FILTERED (65 cols) to EXTENDED (62 cols)

   - Removed incorrect "Metric Type + Extended" description
   - Updated to "62 columns, canonical format for minimums-filtered results"

2. **portfolios_best**: Fixed column count description from "63 columns" to "65 columns"

   - Correctly uses FILTERED schema with Metric Type

3. **portfolios_metrics**: Fixed column count description from "63 columns" to "65 columns"
   - Correctly uses FILTERED schema with Metric Type

**Final Schema Mapping**:

- `portfolios` = EXTENDED (62 cols, NO Metric Type) ✅
- `portfolios_best` = FILTERED (65 cols, WITH Metric Type) ✅
- `portfolios_filtered` = EXTENDED (62 cols, NO Metric Type) ✅
- `portfolios_metrics` = FILTERED (65 cols, WITH Metric Type) ✅

### Phase 2: Fix Test Expectations ✅

**File**: `tests/cli/integration/test_export_matrix.py`

Removed incorrect Metric Type assertions from three portfolios_filtered tests:

1. **test_sma_portfolios_filtered_export** (line ~232)

   - Removed: `assert "Metric Type" in df.columns`

2. **test_ema_portfolios_filtered_export** (lines ~330-335)

   - Removed: `assert "Metric Type" in df.columns`
   - Removed: Metric type value assertions

3. **test_macd_portfolios_filtered_export** (lines ~420-423)

   - Removed: `assert "Metric Type" in df.columns`
   - Removed: MACD-specific metric type assertions

4. **test_all_strategy_export_combinations** (line ~715)

   - Updated assertion to only check for Metric Type in `portfolios_best`, not `portfolios_filtered`
   - Changed from: `if export_type in ["portfolios_filtered", "portfolios_best"]:`
   - Changed to: `if export_type == "portfolios_best":`

5. **test_multiple_tickers_single_strategy** (line ~534)

   - Removed: `assert "Metric Type" in df.columns`

6. **test_portfolios_filtered_schema_consistency** (line ~856-857)
   - Removed: `assert "Metric Type" in df.columns`
   - Removed: `assert df["Metric Type"][0] == "Most Total Return [%]"`
   - Added comment explaining portfolios_filtered uses EXTENDED schema

### Phase 3: Fix Minimum Filtering Logic ✅

**File**: `app/tools/strategy/export_portfolios.py` (lines 425-447)

Fixed over-aggressive minimum filtering that was causing exports to return `success=False`:

**Key Change**: Removed `"portfolios"` from minimum filtering

- **Before**: Applied filtering to both `"portfolios_best"` and `"portfolios"`
- **After**: Only applies filtering to `"portfolios_best"`

**Rationale**:

- `portfolios` export type should export ALL portfolios without any filtering
- `portfolios_best` export type should apply MINIMUMS filtering for analysis purposes
- `portfolios_filtered` already has filtering applied before reaching this function

This was the root cause of test failures - portfolios were being filtered when they shouldn't be, causing empty results and `success=False` returns.

## Test Results

### Before Fixes

- 11 tests failing
- All failures due to `assert success is True` or `assert "Metric Type" in df.columns`

### After Fixes

```bash
pytest tests/cli/integration/test_export_matrix.py -v

Results: 28 passed, 13 warnings in 3.04s
```

**All tests pass** including both TestExportTypeMatrix and TestExportSchemaConsistency test suites!

### All Originally Failing Tests Now Pass:

1. ✅ test_sma_portfolios_export
2. ✅ test_sma_portfolios_filtered_export
3. ✅ test_sma_portfolios_best_export
4. ✅ test_ema_portfolios_export
5. ✅ test_ema_portfolios_filtered_export
6. ✅ test_ema_portfolios_best_export
7. ✅ test_macd_portfolios_export
8. ✅ test_macd_portfolios_filtered_export
9. ✅ test_macd_portfolios_best_export
10. ✅ test_mixed_strategies_portfolios_export
11. ✅ test_synthetic_ticker_export
12. ✅ test_all_strategy_export_combinations[SMA-portfolios]
13. ✅ test_all_strategy_export_combinations[SMA-portfolios_filtered]
14. ✅ test_all_strategy_export_combinations[SMA-portfolios_best]
15. ✅ test_all_strategy_export_combinations[EMA-portfolios]
16. ✅ test_all_strategy_export_combinations[EMA-portfolios_filtered]
17. ✅ test_all_strategy_export_combinations[EMA-portfolios_best]
18. ✅ test_all_strategy_export_combinations[MACD-portfolios]
19. ✅ test_all_strategy_export_combinations[MACD-portfolios_filtered]
20. ✅ test_all_strategy_export_combinations[MACD-portfolios_best]
21. ✅ test_empty_portfolios_export

## Files Modified

1. `app/tools/strategy/export_portfolios.py`

   - Fixed EXPORT_SCHEMA_CONFIG schema types and descriptions
   - Removed portfolios from minimum filtering logic

2. `tests/cli/integration/test_export_matrix.py`
   - Removed incorrect Metric Type assertions from portfolios_filtered tests
   - Updated parametrized test to only check Metric Type for portfolios_best

## Verification

No linter errors introduced by changes:

```bash
read_lints: No linter errors found.
```

## Expected Outcomes - All Achieved ✅

- ✅ Schema configuration matches desired mappings
- ✅ All 11 originally failing tests pass
- ✅ `portfolios` exports use EXTENDED schema (62 cols, no Metric Type)
- ✅ `portfolios_best` exports use FILTERED schema (65 cols, with Metric Type)
- ✅ `portfolios_filtered` exports use EXTENDED schema (62 cols, no Metric Type)
- ✅ `portfolios_metrics` exports use FILTERED schema (65 cols, with Metric Type)
- ✅ Export functions return success=True for valid portfolios
- ✅ No regression in currently passing tests
- ✅ No linter errors introduced
