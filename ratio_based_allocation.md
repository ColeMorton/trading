# Ratio-Based Allocation Implementation Plan

## Overview
Implement ratio-based allocation to ensure the smallest asset allocation is at least half of the largest allocation, maintaining balance and reducing risk through diversification.

## Required Changes

### 1. Update Configuration Type
Update `ConcurrencyConfig` in `config.py` to include the new flag:

```python
class ConcurrencyConfig(TypedDict):
    """Configuration for concurrency analysis.

    Required Fields:
        PORTFOLIO (str): Portfolio configuration file name
        BASE_DIR (str): Base directory for file operations
        REFRESH (bool): Whether to refresh cached data

    Optional Fields:
        SL_CANDLE_CLOSE (NotRequired[bool]): Use candle close for stop loss
        RATIO_BASED_ALLOCATION (NotRequired[bool]): Enable ratio-based allocation
    """
    PORTFOLIO: str
    BASE_DIR: str
    REFRESH: bool
    SL_CANDLE_CLOSE: NotRequired[bool]
    RATIO_BASED_ALLOCATION: NotRequired[bool]
```

### 2. Modify Allocation Logic
Update `calculate_allocation_scores` in `efficiency.py` to implement ratio-based allocation:

1. Keep existing allocation calculation as base case
2. When RATIO_BASED_ALLOCATION is True:
   - Find smallest and largest allocations
   - If smallest < 0.5 * largest:
     - Scale up smaller allocations while maintaining relative proportions
     - Scale down larger allocations to compensate
   - Normalize final allocations to sum to 100%

### 3. Pass Configuration
Modify `analyze_concurrency` in `analysis.py` to:
1. Extract RATIO_BASED_ALLOCATION from config
2. Pass it through to calculate_allocation_scores

## Implementation Details

### Ratio-Based Allocation Algorithm
1. Calculate initial allocations using current method
2. If RATIO_BASED_ALLOCATION is True:
   ```python
   min_alloc = min(allocations)
   max_alloc = max(allocations)
   
   if min_alloc < 0.5 * max_alloc:
       # Scale up smaller allocations
       scale_factor = 0.5 * max_alloc / min_alloc
       
       # Apply scaling while preserving relative proportions
       scaled_allocations = [
           alloc * scale_factor if alloc < 0.5 * max_alloc else alloc
           for alloc in allocations
       ]
       
       # Normalize to 100%
       total = sum(scaled_allocations)
       final_allocations = [alloc / total * 100 for alloc in scaled_allocations]
   ```

## Testing Plan
1. Test with RATIO_BASED_ALLOCATION = False (should match current behavior)
2. Test with RATIO_BASED_ALLOCATION = True:
   - Verify smallest allocation >= 0.5 * largest allocation
   - Verify allocations sum to 100%
   - Verify relative proportions maintained for allocations above minimum threshold

## Next Steps
1. Switch to code mode to implement changes
2. Update configuration type
3. Implement ratio-based allocation logic
4. Add configuration passing
5. Test implementation