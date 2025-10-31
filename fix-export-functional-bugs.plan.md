# Fix Export Logic Functional Bugs

## Overview

After fixing test infrastructure issues, the integration tests are now correctly identifying real functional bugs in the portfolio export logic. These bugs involve incorrect schema transformations that drop the "Metric Type" column and over-aggressive aggregation.

## Issue Analysis

### Bug 1: Missing "Metric Type" Column (3 tests failing)

**Failing Tests**:

- `test_sma_portfolios_filtered_export`
- `test_ema_portfolios_filtered_export`
- `test_macd_portfolios_filtered_export`

**Expected Behavior**:

- Export type: `portfolios_filtered`
- Target schema: `EXTENDED` (62 columns)
- Input data contains "Metric Type" column
- Output should preserve "Metric Type" column

**Actual Behavior**:

- Output has 64 columns instead of expected schema
- "Metric Type" column is missing
- Test assertion fails: `assert "Metric Type" in df.columns`

**Root Cause Hypothesis**:
The schema transformation logic in `export_portfolios.py` may be:

1. Applying the wrong schema type (EXTENDED doesn't include Metric Type)
2. Dropping the column during normalization
3. Using incorrect config mapping for `portfolios_filtered` export type

### Bug 2: Over-Aggressive Aggregation (2 tests failing)

**Failing Tests**:

- `test_sma_portfolios_best_export`
- `test_ema_portfolios_best_export`

**Expected Behavior**:

- Export type: `portfolios_best`
- Target schema: `FILTERED` (63 columns with Metric Type)
- Input: 2 portfolios with different "Metric Type" values
- Output: Should preserve both portfolios (different metrics)

**Actual Behavior**:

- Only 1 portfolio returned instead of 2
- Test assertion fails: `assert len(df) == 2` (actual: len = 1)

**Root Cause Hypothesis**:
The aggregation logic in `deduplicate_and_aggregate_portfolios` may be:

1. Incorrectly treating different Metric Types as duplicates
2. Aggregating when it shouldn't for portfolios_best
3. Using wrong grouping keys that ignore Metric Type

## Investigation Steps

### Step 1: Analyze Schema Configuration for portfolios_filtered

**File**: `app/tools/strategy/export_portfolios.py`

Check the `EXPORT_SCHEMA_CONFIG` mapping:

- Line 151-188: Verify `portfolios_filtered` configuration
- Expected: Should use EXTENDED schema (62 columns, NO Metric Type)
- Issue: Config says EXTENDED but test expects Metric Type column

**Questions to answer**:

1. Should `portfolios_filtered` use EXTENDED or FILTERED schema?
2. Is the test expectation correct?
3. What's the intended behavior for filtered exports?

### Step 2: Trace Metric Type Column Through Export Flow

**File**: `app/tools/strategy/export_portfolios.py`

Trace the column through the export process:

1. Line 413: Initial DataFrame creation from portfolios list
2. Line 654-728: Schema normalization for FILTERED types
3. Line 676-690: `normalize_to_schema` call - may drop Metric Type
4. Check if EXTENDED schema normalization removes Metric Type

**Debug approach**:

- Add temporary logging to track when Metric Type disappears
- Check if `SchemaTransformer.normalize_to_schema` preserves it
- Verify column list after each transformation step

### Step 3: Investigate Aggregation Logic

**File**: `app/tools/portfolio/collection.py`

Examine `deduplicate_and_aggregate_portfolios` function:

- Check grouping keys used for deduplication
- Verify if Metric Type is part of the grouping key
- Ensure different Metric Types aren't treated as duplicates

**Questions to answer**:

1. What columns are used as grouping keys?
2. Is Metric Type included in the grouping?
3. Should portfolios_best aggregate at all, or just filter?

### Step 4: Review Schema Type Definitions

**File**: `app/tools/portfolio/base_extended_schemas.py`

Check schema definitions:

- `ExtendedPortfolioSchema` - 62 columns (baseline)
- `FilteredPortfolioSchema` - 63 columns (with Metric Type)
- Verify column lists and ordering

**Verify**:

1. Which schema types include Metric Type?
2. Is there confusion between EXTENDED and FILTERED usage?

## Implementation Plan

### Option A: Fix Schema Configuration (If config is wrong)

If `portfolios_filtered` should use FILTERED schema (with Metric Type):

**File**: `app/tools/strategy/export_portfolios.py` (line 170-175)

Change:

```python
"portfolios_filtered": {
    "schema": SchemaType.EXTENDED,  # ← Change this
    "description": "62 columns, canonical format for minimums-filtered results",
```

To:

```python
"portfolios_filtered": {
    "schema": SchemaType.FILTERED,
    "description": "63 columns, Metric Type + Extended for filtered results",
```

### Option B: Fix Test Expectations (If code is correct)

If EXTENDED schema is correct for `portfolios_filtered`:

**File**: `tests/cli/integration/test_export_matrix.py`

Remove the Metric Type assertions from filtered export tests since EXTENDED schema doesn't include it.

### Option C: Fix Schema Transformation Logic (If transformation drops column incorrectly)

If normalization is incorrectly dropping Metric Type:

**File**: `app/tools/portfolio/base_extended_schemas.py`

Modify `SchemaTransformer.normalize_to_schema` to preserve Metric Type when present in source data, even for EXTENDED schema transformations.

### Fix Aggregation Bug

**File**: `app/tools/portfolio/collection.py`

**Investigation**:

1. Find the `deduplicate_and_aggregate_portfolios` function
2. Check grouping logic - ensure Metric Type is in grouping keys
3. Verify portfolios with different Metric Types aren't merged

**Likely fix**:

```python
# Ensure Metric Type is part of the grouping key
grouping_columns = ["Ticker", "Strategy Type", "Fast Period", "Slow Period", "Metric Type"]
```

## Decision Point

Before implementing fixes, we need to determine:

**Question 1**: What is the correct schema for `portfolios_filtered` export type?

- A) FILTERED (63 columns with Metric Type) - Tests are correct, config is wrong
- B) EXTENDED (62 columns without Metric Type) - Config is correct, tests are wrong

**Question 2**: Should `portfolios_best` aggregate portfolios?

- A) Yes, but preserve different Metric Types separately
- B) No, just filter without aggregation

## Testing Strategy

After fixes:

1. Run the 5 failing tests individually to verify each fix
2. Run full integration test suite to ensure no regressions
3. Verify export files have correct schemas
4. Check that Metric Type values are preserved correctly

## Expected Outcomes

- ✅ All 5 currently failing tests pass
- ✅ Metric Type column preserved in all appropriate exports
- ✅ Different Metric Types not incorrectly aggregated
- ✅ Schema consistency across export types
- ✅ No regression in currently passing tests
