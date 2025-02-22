# Ratio-Based Allocation Implementation Fix

## Current Issues
1. Duplicate calculate_allocation_scores function in efficiency.py
2. Ratio-based allocation incorrectly applied to strategy allocations
3. Missing implementation for ticker-level ratio-based allocation

## Required Changes

### 1. Fix Duplicate Function
Remove the first calculate_allocation_scores function (lines 181-235) in efficiency.py and keep the second implementation that includes the ratio_based_allocation parameter.

### 2. Remove Strategy-Level Ratio Allocation
Modify analyze_concurrency in analysis.py to remove ratio-based allocation from strategy calculations:
```python
# Remove ratio_based_allocation parameter
allocation_scores, allocation_percentages = calculate_allocation_scores(
    strategy_expectancies,
    strategy_risk_contributions,
    strategy_alphas,
    allocation_efficiencies,
    log
)
```

### 3. Add Ticker-Level Ratio Allocation
1. Create a new function in efficiency.py for ticker-level allocation:
```python
def calculate_ticker_allocations(
    ticker_metrics: Dict[str, float],
    ratio_based_allocation: bool,
    log: Callable[[str, str], None]
) -> Dict[str, float]:
    """Calculate allocations for individual tickers.

    Args:
        ticker_metrics (Dict[str, float]): Dictionary of ticker metrics
        ratio_based_allocation (bool): Whether to apply ratio-based allocation
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, float]: Ticker allocation percentages
    """
```

2. Apply ratio-based allocation only to ticker allocations when calculating ticker metrics

### 4. Update Tests
1. Add test cases for ticker-level ratio-based allocation
2. Verify strategy allocations remain unaffected
3. Ensure smallest ticker allocation is at least half of largest

## Implementation Steps
1. Switch to code mode to implement changes
2. Remove duplicate function
3. Create ticker allocation function
4. Update analysis.py to use new function
5. Add tests
6. Verify implementation

## Verification Plan
1. Test with RATIO_BASED_ALLOCATION = False:
   - Strategy allocations should match current behavior
   - Ticker allocations should match current behavior

2. Test with RATIO_BASED_ALLOCATION = True:
   - Strategy allocations should remain unchanged
   - Ticker allocations should follow ratio-based rules:
     * Smallest allocation >= 0.5 * largest allocation
     * Sum to 100%
     * Maintain relative proportions above minimum threshold