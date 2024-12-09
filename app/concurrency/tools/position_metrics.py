"""Position-based metrics calculation for concurrency analysis."""

from typing import List, Tuple, Dict
import numpy as np

def calculate_position_metrics(
    position_arrays: List[np.ndarray]
) -> Tuple[Dict[str, float], float, int, int, int, int, float]:
    """Calculate metrics from position arrays.

    Args:
        position_arrays (List[np.ndarray]): List of position arrays

    Returns:
        Tuple containing:
            - Dict[str, float]: Strategy correlations
            - float: Average correlation
            - int: Concurrent periods
            - int: Exclusive periods
            - int: Inactive periods
            - int: Maximum concurrent strategies
            - float: Average concurrent strategies
    """
    # Calculate concurrent positions
    concurrent_matrix = np.column_stack(position_arrays)
    active_strategies = np.sum(concurrent_matrix != 0, axis=1)
    
    # Calculate basic statistics
    concurrent_periods = int(np.sum(active_strategies >= 2))
    exclusive_periods = int(np.sum(active_strategies == 1))
    inactive_periods = int(np.sum(active_strategies == 0))
    max_concurrent = int(np.max(active_strategies))
    
    # Calculate average concurrent strategies for active periods
    active_mask = active_strategies >= 1
    avg_concurrent = (
        float(np.mean(active_strategies[active_mask]))
        if np.any(active_mask)
        else 0.0
    )
    
    # Calculate correlations
    correlations: Dict[str, float] = {}
    correlation_sum = 0.0
    correlation_count = 0
    for i in range(len(position_arrays)):
        for j in range(i+1, len(position_arrays)):
            correlation = float(
                np.corrcoef(position_arrays[i], position_arrays[j])[0, 1]
            )
            correlations[f"correlation_{i+1}_{j+1}"] = correlation
            correlation_sum += abs(correlation)
            correlation_count += 1
    
    avg_correlation = (
        correlation_sum / correlation_count
        if correlation_count > 0
        else 0.0
    )
    
    return (
        correlations,
        avg_correlation,
        concurrent_periods,
        exclusive_periods,
        inactive_periods,
        max_concurrent,
        avg_concurrent
    )
