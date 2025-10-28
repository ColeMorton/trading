# TypedDict Definition Audit

## Purpose

Document all TypedDict definition mismatches found during Phase 2 of type refactoring sprint.
This audit identifies missing required keys, extra undeclared keys, and naming inconsistencies.

## Summary Statistics

- Total Missing Key Errors: ~200
- Total Extra Key Errors: ~300
- Files Affected: ~50
- Primary Issue: Inconsistent naming (snake_case vs UPPER_CASE)

---

## Critical Issues by TypedDict

### 1. StrategyConfig (app/concurrency/tools/)

**Missing Keys:**

- `fast_period` (int)
- `slow_period` (int)
- `strategy_id` (str)
- `TICKER` (str | list[str])
- `BASE_DIR` (str)
- `REFRESH` (bool)
- `USE_RSI` (bool)
- `USE_HOURLY` (bool)
- `USE_SMA` (bool)
- `STRATEGY_TYPE` (str)
- `DIRECTION` (Literal["Long", "Short"])

**Extra Keys (should be renamed or removed):**

- `ticker` → should be `TICKER`
- `timeframe` → not in current definition
- `strategy` → should be `STRATEGY_TYPE`
- `ma_fast` → should be `fast_period` or `FAST_PERIOD`
- `ma_slow` → should be `slow_period` or `SLOW_PERIOD`
- `allocation` → needs to be added
- `stop_loss` → should be `STOP_LOSS`

**Files Affected:**

- `app/concurrency/tools/concurrency_analysis.py:78`
- `app/strategies/ma_cross/1_get_portfolios.py:69`
- `app/strategies/sma_atr/1_get_portfolios.py:51`

**Recommendation:** Standardize on UPPER_CASE for config keys

---

### 2. CacheConfig (app/strategies/ma_cross/)

**Missing Keys:**

- `USE_RSI` (bool)
- `RSI_WINDOW` (int)
- `RSI_THRESHOLD` (int | float)
- `STOP_LOSS` (float)

**Extra Keys (need to be added to definition):**

- `USE_HOURLY` (bool) - commonly used, should be in definition
- `DIRECTION` (Literal["Long", "Short"]) - commonly used
- `USE_CURRENT` (bool) - commonly used
- `EMA_PERIODS` (list[int]) - MA-specific
- `RVOL_THRESHOLDS` (list[float]) - volume-specific
- `VOLUME_LOOKBACKS` (list[int]) - volume-specific
- `SORT_BY` (str) - filtering
- `SORT_ASC` (bool) - filtering
- `ATR_LENGTH_MIN` (int) - ATR-specific
- `ATR_LENGTH_MAX` (int) - ATR-specific
- `ATR_MULTIPLIER_MIN` (float) - ATR-specific
- `ATR_MULTIPLIER_MAX` (float) - ATR-specific
- `ATR_MULTIPLIER_STEP` (float) - ATR-specific
- `MINIMUMS` (dict[str, int | float]) - filtering

**Files Affected:**

- `app/strategies/ma_cross/4_review_protective_stop_loss.py:26`
- `app/strategies/ma_cross/3_get_volume_stop_portfolios.py:36`
- `app/strategies/ma_cross/3_review_stop_loss.py:115`
- `app/strategies/ma_cross/2_review_rsi.py:22`
- `app/strategies/ma_cross/3_get_atr_stop_portfolios.py:32`

**Recommendation:** CacheConfig is too restrictive - add all commonly used fields with NotRequired

---

### 3. Strategy (app/concurrency/tools/report/)

**Missing Keys:**

- `allocation_score` (float)
- `allocation` (float)

**Files Affected:**

- `app/concurrency/tools/report/strategy.py:274`

**Recommendation:** Add these fields to Strategy TypedDict with NotRequired

---

### 4. StrategyParameters (app/concurrency/tools/report/)

**Missing Keys:**

- `fast_period` (int)
- `slow_period` (int)

**Files Affected:**

- `app/concurrency/tools/report/strategy.py:75`

**Recommendation:** Add MA-specific parameters with NotRequired

---

### 5. PositionSizingConfig (app/portfolio_optimization/)

**Extra Keys:**

- `portfolio` - not in definition
- `var_confidence_levels` - not in definition

**Files Affected:**

- `app/portfolio_optimization/1_analysis.py:30`

**Recommendation:** Add these fields to PositionSizingConfig or remove from usage

---

### 6. Config (ma_cross 5_review_slippage.py)

**Extra Keys:**

- `BASE_DIR` - should be in base config
- `REFRESH` - should be in base config
- `RELATIVE` - review-specific field

**Files Affected:**

- `app/strategies/ma_cross/5_review_slippage.py:70`

**Recommendation:** BASE_DIR and REFRESH already in BaseStrategyConfig, add RELATIVE

---

### 7. ConfigDict (Pydantic - app/database/config.py)

**Extra Keys:**

- `env_file` - Pydantic v2 field
- `case_sensitive` - Pydantic v2 field

**Files Affected:**

- `app/database/config.py:48`

**Recommendation:** This is a Pydantic version mismatch, not our TypedDict

---

## Action Items

### High Priority (Phase 2.2)

1. **Update StrategyConfig** - Add missing fields:

   ```python
   class StrategyConfig(TypedDict):
       # Existing fields...
       fast_period: NotRequired[int]
       slow_period: NotRequired[int]
       strategy_id: NotRequired[str]
       allocation: NotRequired[float]
       TICKER: str | list[str]  # Make consistent with UPPER_CASE
   ```

2. **Update CacheConfig** - Add commonly used fields:

   ```python
   class CacheConfig(TypedDict):
       # Add all these as NotRequired
       USE_HOURLY: NotRequired[bool]
       USE_CURRENT: NotRequired[bool]
       DIRECTION: NotRequired[Literal["Long", "Short"]]
       # ... (see full list above)
   ```

3. **Standardize Naming Convention**:
   - Decide: UPPER_CASE vs snake_case
   - Current codebase uses UPPER_CASE for config keys
   - Refactor snake_case usage to UPPER_CASE

### Medium Priority (Phase 2.3)

4. **Fix Usage Sites** - Rename keys in ~50 files:
   - `ticker` → `TICKER`
   - `ma_fast` → `FAST_PERIOD`
   - `ma_slow` → `SLOW_PERIOD`
   - etc.

### Low Priority

5. **Pydantic ConfigDict** - Update to v2 or suppress error

---

## Files Requiring Updates

### TypedDict Definitions to Update:

1. `app/concurrency/tools/report/strategy.py` - StrategyParameters, Strategy
2. `app/strategies/ma_cross/config_types.py` - CacheConfig (if exists)
3. `app/portfolio_optimization/` - PositionSizingConfig
4. `app/contexts/portfolio/types/` - StrategyConfig (if different from concurrency)

### Usage Sites to Fix:

- `app/strategies/ma_cross/*.py` (12+ files)
- `app/strategies/sma_atr/1_get_portfolios.py`
- `app/concurrency/tools/concurrency_analysis.py`
- See full list in mypy output

---

## Estimated Impact

- Fixing these definitions: ~150-200 errors
- Fixing usage sites: ~300-400 errors
- Total Phase 2 impact: ~500-600 errors fixed

---

## Next Steps (Phase 2.2)

1. Update each TypedDict definition identified above
2. Add fields with NotRequired to maintain backward compatibility
3. Test incrementally with `mypy app/concurrency/` after each change
