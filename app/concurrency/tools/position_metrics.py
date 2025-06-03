"""Position-based metrics calculation for concurrency analysis."""

from typing import Callable, Dict, List, Tuple

import numpy as np


def calculate_position_metrics(
    position_arrays: List[np.ndarray], log: Callable[[str, str], None]
) -> Tuple[Dict[str, float], float, int, int, int, int, float, List[Dict[str, float]]]:
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
            - List[Dict[str, float]]: Strategy-specific metrics

    Raises:
        ValueError: If position arrays list is empty
        Exception: If calculation fails
    """
    try:
        if not position_arrays:
            log("No position arrays provided", "error")
            raise ValueError("Position arrays list cannot be empty")

        log(
            f"Calculating position metrics for {len(position_arrays)} strategies",
            "info",
        )

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

        # Calculate strategy-specific metrics
        strategy_specific_metrics = []
        total_periods = len(position_arrays[0])

        for i in range(len(position_arrays)):
            # Calculate strategy-specific correlation (average correlation with other strategies)
            strategy_correlations = []
            for j in range(len(position_arrays)):
                if i != j:
                    correlation = float(
                        np.corrcoef(position_arrays[i], position_arrays[j])[0, 1]
                    )
                    strategy_correlations.append(abs(correlation))

                    # Also store in the overall correlations dict for backward compatibility
                    if j > i:
                        correlations[f"correlation_{i+1}_{j+1}"] = correlation
                        correlation_sum += abs(correlation)
                        correlation_count += 1
                        log(
                            f"Correlation between strategy {i+1} and {j+1}: {correlation:.2f}",
                            "info",
                        )

            # Calculate strategy-specific average correlation
            strategy_avg_correlation = (
                sum(strategy_correlations) / len(strategy_correlations)
                if strategy_correlations
                else 0.0
            )

            # Calculate strategy-specific activity periods
            strategy_active_periods = int(np.sum(position_arrays[i] != 0))
            strategy_inactive_periods = total_periods - strategy_active_periods

            # Calculate strategy-specific exclusive periods
            # (periods where only this strategy is active)
            exclusive_mask = np.zeros(total_periods, dtype=bool)
            for period_idx in range(total_periods):
                # Check if only this strategy is active in this period
                if position_arrays[i][period_idx] != 0:
                    other_active = False
                    for j in range(len(position_arrays)):
                        if i != j and position_arrays[j][period_idx] != 0:
                            other_active = True
                            break
                    if not other_active:
                        exclusive_mask[period_idx] = True

            strategy_exclusive_periods = int(np.sum(exclusive_mask))

            # Calculate strategy-specific concurrent periods
            # (periods where this strategy is active along with others)
            strategy_concurrent_periods = (
                strategy_active_periods - strategy_exclusive_periods
            )

            # Calculate strategy-specific ratios
            strategy_inactive_ratio = strategy_inactive_periods / total_periods
            strategy_exclusive_ratio = strategy_exclusive_periods / total_periods
            strategy_concurrent_ratio = strategy_concurrent_periods / total_periods

            # Store strategy-specific metrics
            strategy_metrics = {
                "correlation": strategy_avg_correlation,
                "inactive_ratio": strategy_inactive_ratio,
                "exclusive_ratio": strategy_exclusive_ratio,
                "concurrent_ratio": strategy_concurrent_ratio,
                "active_periods": strategy_active_periods,
                "inactive_periods": strategy_inactive_periods,
                "exclusive_periods": strategy_exclusive_periods,
                "concurrent_periods": strategy_concurrent_periods,
            }

            strategy_specific_metrics.append(strategy_metrics)

            log(f"Strategy {i+1} specific metrics:", "info")
            log(f"  Average correlation: {strategy_avg_correlation:.4f}", "info")
            log(
                f"  Active periods: {strategy_active_periods} ({strategy_active_periods/total_periods:.2%})",
                "info",
            )
            log(
                f"  Exclusive periods: {strategy_exclusive_periods} ({strategy_exclusive_ratio:.2%})",
                "info",
            )
            log(
                f"  Concurrent periods: {strategy_concurrent_periods} ({strategy_concurrent_ratio:.2%})",
                "info",
            )
            log(
                f"  Inactive periods: {strategy_inactive_periods} ({strategy_inactive_ratio:.2%})",
                "info",
            )

        avg_correlation = (
            correlation_sum / correlation_count if correlation_count > 0 else 0.0
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
            avg_concurrent,
            strategy_specific_metrics,
        )

    except Exception as e:
        log(f"Error calculating position metrics: {str(e)}", "error")
        raise
