# Expectancy Calculation Fix Specification

**Problem**: Expectancy calculations show up to 596,446% variance between different modules due to inconsistent formulas.

## Current Implementations

### 1. Standard Formula (CORRECT)
Location: `/app/tools/expectancy.py`
```python
expectancy = (win_rate * avg_win) - ((1.0 - win_rate) * avg_loss_abs)
```
- Returns expectancy as a percentage/decimal of amount risked
- Example: 0.05 = 5% expected return per trade
- This is the mathematically correct formula

### 2. R-Ratio Formula (INCORRECT)
Location: `/app/macd/tools/calculate_expectancy.py`, `/app/dip/dip.py`
```python
r_ratio = avg_win / avg_loss
expectancy = (win_rate * r_ratio) - (1 - win_rate)
```
- Returns expectancy in R-multiples
- Can produce astronomical values when avg_loss is very small
- This causes the 596,446% variance

## Root Cause Analysis

The massive variance occurs because:
1. R-ratio formula divides by `avg_loss`
2. When `avg_loss` is very small (e.g., 0.0001%), the R-ratio becomes huge
3. This inflated R-ratio gets multiplied by win_rate
4. Result: Expectancy values that are 5,964x larger than reality

## Solution

### Phase 2 Implementation Plan

1. **Create Standardized Expectancy Calculator**
   - Build on existing `/app/tools/expectancy.py`
   - Add validation for edge cases
   - Ensure consistent decimal representation

2. **Update All Modules to Use Standard Calculator**
   Files to update:
   - `/app/macd/tools/calculate_expectancy.py`
   - `/app/dip/dip.py`
   - Any other modules using R-ratio formula

3. **Add Feature Flag for Migration**
   - `USE_FIXED_EXPECTANCY_CALC` environment variable
   - Allows gradual rollout and testing

4. **Comprehensive Testing**
   - Unit tests for all expectancy calculation scenarios
   - Integration tests to verify consistency across modules
   - Edge case testing (zero losses, all wins, etc.)

## Mathematical Proof

### Standard Formula (Correct)
```
E = p * W - (1-p) * L
where:
  E = expectancy per trade
  p = probability of win (win rate)
  W = average win amount
  L = average loss amount (positive)
```

### R-Ratio Formula (Incorrect for direct expectancy)
```
R = W / L
E_r = p * R - (1-p)
```

The R-ratio formula gives expectancy in R-multiples, not percentage returns.
To convert: `E = E_r * L`

## Success Criteria

1. All modules return identical expectancy values for same input
2. Expectancy values are reasonable (typically -50% to +50% per trade)
3. No more 596,446% variances
4. Feature flag allows safe rollback if needed

## Migration Strategy

1. **Phase 2a**: Implement fixed calculation with feature flag
2. **Phase 2b**: Update all modules to use standardized calculator
3. **Phase 2c**: Comprehensive testing
4. **Phase 2d**: Gradual rollout with monitoring
5. **Phase 2e**: Remove legacy implementations after validation