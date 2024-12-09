"""Core analysis functionality for concurrency analysis."""

from typing import List, Tuple, Dict, Callable
import polars as pl
import numpy as np
from app.concurrency.tools.types import ConcurrencyStats, StrategyConfig
from app.concurrency.tools.data_alignment import align_multiple_data
from app.concurrency.tools.risk_metrics import calculate_risk_contributions
from app.concurrency.tools.efficiency import calculate_efficiency_score

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

def analyze_concurrency(
    data_list: List[pl.DataFrame],
    config_list: List[StrategyConfig],
    log: Callable[[str, str], None]
) -> Tuple[ConcurrencyStats, List[pl.DataFrame]]:
    """Analyze concurrent positions across multiple strategies.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals
        config_list (List[StrategyConfig]): List of configurations
        log (Callable[[str, str], None]): Logging function

    Returns:
        Tuple[ConcurrencyStats, List[pl.DataFrame]]: Statistics and aligned data

    Raises:
        ValueError: If invalid input data
    """
    try:
        if len(data_list) != len(config_list):
            raise ValueError("Number of dataframes must match number of configurations")
        
        if len(data_list) < 2:
            raise ValueError("At least two strategies are required for analysis")

        required_cols = ["Date", "Position", "Close"]
        for df in data_list:
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

        log("Starting concurrency analysis", "info")
        log(f"Number of strategies: {len(data_list)}", "info")
        
        # Get hourly flags from configs
        hourly_flags = [
            config.get('USE_HOURLY', False)
            for config in config_list
        ]
        
        # Align data across all strategies
        aligned_data = align_multiple_data(data_list, hourly_flags, log)
        
        # Extract position arrays
        position_arrays = [
            df["Position"].fill_null(0).to_numpy()
            for df in aligned_data
        ]
        
        # Calculate position-based metrics
        (
            correlations,
            avg_correlation,
            concurrent_periods,
            exclusive_periods,
            inactive_periods,
            max_concurrent,
            avg_concurrent
        ) = calculate_position_metrics(position_arrays)
        
        total_periods = len(aligned_data[0])
        
        # Calculate risk concentration index
        risk_concentration_index = (
            avg_concurrent / max_concurrent
            if max_concurrent > 0
            else 0.0
        )
        
        # Calculate risk metrics
        risk_metrics = calculate_risk_contributions(position_arrays, aligned_data)
        
        # Calculate efficiency score
        strategy_expectancies = [
            config.get('Expectancy_per_Day', 0)
            for config in config_list
        ]
        efficiency_score = calculate_efficiency_score(
            strategy_expectancies,
            avg_correlation,
            concurrent_periods,
            exclusive_periods,
            inactive_periods,
            total_periods,
            log
        )
        
        # Compile statistics
        stats: ConcurrencyStats = {
            "total_periods": total_periods,
            "total_concurrent_periods": concurrent_periods,
            "exclusive_periods": exclusive_periods,
            "concurrency_ratio": float(concurrent_periods / total_periods),
            "exclusive_ratio": float(exclusive_periods / total_periods),
            "inactive_ratio": float(inactive_periods / total_periods),
            "avg_concurrent_strategies": avg_concurrent,
            "risk_concentration_index": risk_concentration_index,
            "max_concurrent_strategies": max_concurrent,
            "strategy_correlations": correlations,
            "avg_position_length": float(
                sum(df["Position"].sum() for df in aligned_data) / len(aligned_data)
            ),
            "efficiency_score": efficiency_score,
            "risk_metrics": risk_metrics,
            "start_date": str(aligned_data[0]["Date"].min()),
            "end_date": str(aligned_data[0]["Date"].max())
        }
        
        log("Analysis completed successfully", "info")
        return stats, aligned_data
        
    except Exception as e:
        log(f"Error during analysis: {str(e)}", "error")
        raise
