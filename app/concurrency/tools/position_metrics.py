"""Position-based metrics calculation for concurrency analysis."""

from typing import List, Tuple, Dict, Callable
import numpy as np

def calculate_position_metrics(
    position_arrays: List[np.ndarray],
    log: Callable[[str, str], None]
) -> Tuple[Dict[str, float], float, int, int, int, int, float]:
    """Calculate metrics from position arrays.

    Args:
        position_arrays (List[np.ndarray]): List of position arrays
        log (Callable[[str, str], None]): Logging function

    Returns:
        Tuple containing:
            - Dict[str, float]: Strategy correlations
            - float: Average correlation
            - int: Concurrent periods
            - int: Exclusive periods
            - int: Inactive periods
            - int: Maximum concurrent strategies
            - float: Average concurrent strategies

    Raises:
        ValueError: If position arrays list is empty
        Exception: If calculation fails
    """
    try:
        if not position_arrays:
            log("No position arrays provided", "error")
            raise ValueError("Position arrays list cannot be empty")

        log(f"Calculating position metrics for {len(position_arrays)} strategies", "info")
        
        # Calculate concurrent positions
        concurrent_matrix = np.column_stack(position_arrays)
        active_strategies = np.sum(concurrent_matrix != 0, axis=1)
        log("Successfully created concurrent matrix", "info")
        
        # Calculate basic statistics
        concurrent_periods = int(np.sum(active_strategies >= 2))
        exclusive_periods = int(np.sum(active_strategies == 1))
        inactive_periods = int(np.sum(active_strategies == 0))
        max_concurrent = int(np.max(active_strategies))
        
        log(f"Basic statistics calculated:", "info")
        log(f"Concurrent periods: {concurrent_periods}", "info")
        log(f"Exclusive periods: {exclusive_periods}", "info")
        log(f"Inactive periods: {inactive_periods}", "info")
        log(f"Maximum concurrent strategies: {max_concurrent}", "info")
        
        # Calculate average concurrent strategies for active periods
        active_mask = active_strategies >= 1
        avg_concurrent = (
            float(np.mean(active_strategies[active_mask]))
            if np.any(active_mask)
            else 0.0
        )
        log(f"Average concurrent strategies: {avg_concurrent:.2f}", "info")
        
        # Calculate correlations
        log("Calculating strategy correlations", "info")
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
                log(f"Correlation between strategy {i+1} and {j+1}: {correlation:.2f}", "info")
        
        avg_correlation = (
            correlation_sum / correlation_count
            if correlation_count > 0
            else 0.0
        )
        log(f"Average correlation: {avg_correlation:.2f}", "info")
        
        log("Position metrics calculation completed successfully", "info")
        return (
            correlations,
            avg_correlation,
            concurrent_periods,
            exclusive_periods,
            inactive_periods,
            max_concurrent,
            avg_concurrent
        )
        
    except Exception as e:
        log(f"Error calculating position metrics: {str(e)}", "error")
        raise
