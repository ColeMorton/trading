# Ratio-Based Allocation Fix Plan

## Current Issue
- When ratio-based allocation is active, the relative proportions between allocations are not being maintained correctly
- Example:
  * TRX-USD: 29.71% (inactive) -> 17.35% (active)
  * XMR-USD: 8.07% (inactive) -> 33.00% (active)
- The relative ordering has been inverted, violating the requirement to maintain proportions

## Root Cause Analysis
1. The current adjustment algorithm focuses on the min/max ratio constraint but doesn't properly preserve relative proportions
2. The fallback mechanism for handling proportion deviations is not effectively maintaining the original relationships
3. The iterative adjustment approach may be causing cumulative errors that lead to proportion distortion

## Proposed Solution

### 1. Direct Scaling Approach
Instead of the current iterative approach, implement a direct scaling solution that:
1. Identifies the minimum allocation
2. Scales all allocations up so the minimum meets the ratio requirement
3. Adjusts larger allocations down proportionally to maintain 100% total

### 2. Implementation Details
```python
def adjust_allocations(allocations):
    """
    Adjust allocations to ensure no value is more than twice the minimum
    or less than half the maximum while maintaining relative proportions.
    """
    alloc_array = np.array(allocations)
    if np.sum(alloc_array) == 0:
        return [100.0 / len(allocations)] * len(allocations)
    
    # Get initial proportions
    initial_proportions = alloc_array / np.sum(alloc_array)
    
    # Find minimum non-zero allocation
    min_alloc = np.min(alloc_array[alloc_array > 0])
    max_alloc = np.max(alloc_array)
    
    # If already satisfies constraint, return normalized allocations
    if min_alloc >= max_alloc / 2:
        return (initial_proportions * 100).tolist()
    
    # Calculate scaling factor to bring minimum up to half of maximum
    target_min = max_alloc / 2
    scale_factor = target_min / min_alloc
    
    # Scale all allocations
    scaled = alloc_array * scale_factor
    
    # Normalize to 100% while preserving relative proportions
    result = scaled / np.sum(scaled) * 100
    
    return result.tolist()
```

### 3. Key Improvements
- Simpler, more direct approach that focuses on the core requirements
- Single-pass scaling that maintains relative proportions
- Eliminates potential for cumulative errors from iterations
- More predictable and stable results

### 4. Validation Criteria
The solution should be verified against these criteria:
1. No allocation is less than half the maximum
2. Original relative proportions are maintained (higher stays higher)
3. Sum of allocations equals 100%
4. Zero allocations remain zero

## Testing Plan
1. Test with the original TRX-USD and XMR-USD case
2. Test edge cases:
   - All equal allocations
   - Zero allocations
   - Single dominant allocation
   - Multiple small allocations
3. Verify relative ordering is preserved in all cases

## Implementation Steps
1. Replace the existing adjust_allocations() function with the new implementation
2. Add additional logging to track allocation adjustments
3. Verify the changes maintain compatibility with existing callers
4. Run test cases to validate the solution