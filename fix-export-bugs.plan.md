# Fix Export Logic Issues

## Clarified Requirements

**portfolios_filtered**:

- Should use EXTENDED schema (62 columns)
- Should NOT have "Metric Type" column
- Current behavior: CORRECT ✅
- Current tests: INCORRECT ❌ (expect Metric Type)

**portfolios_best**:

- Should use FILTERED schema (63 columns)
- Should HAVE "Metric Type" column with aggregated metric types
- Current behavior: INCORRECT ❌ (only returning 1 portfolio, should return 2)
- Current tests: CORRECT ✅

## Issues to Fix

### Issue 1: Test Expectations for portfolios_filtered (3 tests)

**Files**: `tests/cli/integration/test_export_matrix.py`

**Tests to fix**:

- `test_sma_portfolios_filtered_export` (line ~195)
- `test_ema_portfolios_filtered_export` (line ~298)
- `test_macd_portfolios_filtered_export` (line ~402)

**Fix**: Remove the assertion `assert "Metric Type" in df.columns`

These tests incorrectly expect Metric Type in EXTENDED schema exports. The export logic is working correctly - the tests have wrong expectations.

### Issue 2: Over-Aggressive Aggregation in portfolios_best (2 tests)

**File**: `app/tools/portfolio/collection.py`

**Tests failing**:

- `test_sma_portfolios_best_export` (expects 2 portfolios, gets 1)
- `test_ema_portfolios_best_export` (expects 2 portfolios, gets 1)

**Root Cause**: The `deduplicate_and_aggregate_portfolios` function is merging portfolios with different Metric Types into a single row instead of keeping them separate.

**Investigation needed**:

1. Find the grouping logic in `deduplicate_and_aggregate_portfolios`
2. Verify if "Metric Type" is included in grouping keys
3. Fix to preserve separate rows for each unique Metric Type

**Expected fix**: Ensure portfolios are grouped by Metric Type, so different metric types create separate aggregated rows.

## Implementation Steps

### Step 1: Fix Test Expectations for portfolios_filtered

**File**: `tests/cli/integration/test_export_matrix.py`

Remove Metric Type assertions from filtered export tests:

**test_sma_portfolios_filtered_export** (around line 195):

```python
# Remove this line:
assert "Metric Type" in df.columns
```

**test_ema_portfolios_filtered_export** (around line 298-306):

```python
# Remove these lines:
assert "Metric Type" in df.columns

# Verify metric type values are preserved
metric_types = df["Metric Type"].to_list()
assert "Most Total Return [%]" in metric_types
assert "Most Win Rate [%]" in metric_types
```

**test_macd_portfolios_filtered_export** (around line 402-409):

```python
# Remove these lines:
assert "Metric Type" in df.columns

# Verify MACD-specific metric types are preserved
metric_types = df["Metric Type"].to_list()
assert "Most Total Return [%]" in metric_types
assert "Most Profit Factor" in metric_types
```

### Step 2: Investigate Aggregation Logic

**File**: `app/tools/portfolio/collection.py`

Find the `deduplicate_and_aggregate_portfolios` function and:

1. Identify the grouping columns used for aggregation
2. Check if "Metric Type" is in the grouping key
3. If not, add it to ensure different Metric Types aren't merged

**Likely location**: Search for groupby operations that group portfolios

**Expected fix pattern**:

```python
# Current (incorrect):
grouping_cols = ["Ticker", "Strategy Type", "Fast Period", "Slow Period"]

# Fixed (correct):
grouping_cols = ["Ticker", "Strategy Type", "Fast Period", "Slow Period", "Metric Type"]
```

This ensures portfolios with different Metric Types remain separate rows.

### Step 3: Verify portfolios_best Schema

**File**: `app/tools/strategy/export_portfolios.py`

Confirm the schema configuration for portfolios_best is correct:

```python
"portfolios_best": {
    "schema": SchemaType.FILTERED,  # ✅ Correct - includes Metric Type
    "description": "63 columns, Metric Type + Extended for best portfolios with aggregated metrics",
    "allocation_handling": "none",
    "validation_level": "strict",
},
```

This should already be correct based on line 158-163.

## Testing

After fixes:

```bash
# Test the 3 filtered export tests (should now pass)
poetry run pytest tests/cli/integration/test_export_matrix.py::TestExportTypeMatrix::test_sma_portfolios_filtered_export -v
poetry run pytest tests/cli/integration/test_export_matrix.py::TestExportTypeMatrix::test_ema_portfolios_filtered_export -v
poetry run pytest tests/cli/integration/test_export_matrix.py::TestExportTypeMatrix::test_macd_portfolios_filtered_export -v

# Test the 2 best export tests (should now pass after aggregation fix)
poetry run pytest tests/cli/integration/test_export_matrix.py::TestExportTypeMatrix::test_sma_portfolios_best_export -v
poetry run pytest tests/cli/integration/test_export_matrix.py::TestExportTypeMatrix::test_ema_portfolios_best_export -v
```

## Expected Outcomes

- ✅ 3 filtered export tests pass (after removing incorrect Metric Type assertions)
- ✅ 2 best export tests pass (after fixing aggregation to preserve different Metric Types)
- ✅ All 7 originally failing export matrix tests pass
- ✅ Schema consistency maintained across export types
- ✅ Different Metric Types preserved as separate rows in portfolios_best
