"""Core analysis functionality for concurrency analysis."""

from typing import Tuple, List, Dict
import polars as pl
import numpy as np
from app.concurrency.tools.types import ConcurrencyStats, StrategyConfig
from app.concurrency.tools.data_alignment import align_data

def analyze_concurrency(
    data_list: List[pl.DataFrame],
    config_list: List[StrategyConfig]
) -> Tuple[ConcurrencyStats, List[pl.DataFrame]]:
    """Analyze concurrent positions across multiple strategies.

    Calculates various statistics about the concurrent positions across
    all provided trading strategies, including the number of concurrent periods,
    average number of concurrent strategies, maximum concurrent strategies, and
    the ratio of periods with no active strategies. Handles different timeframes 
    by resampling hourly data to daily when needed.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals for each strategy
        config_list (List[StrategyConfig]): List of configurations for each strategy

    Returns:
        Tuple[ConcurrencyStats, List[pl.DataFrame]]: Tuple containing:
            - Dictionary of concurrency statistics
            - List of aligned dataframes

    Raises:
        ValueError: If any dataframe is missing required columns or lists have different lengths
    """
    if len(data_list) != len(config_list):
        raise ValueError("Number of dataframes must match number of configurations")
    
    if len(data_list) < 2:
        raise ValueError("At least two strategies are required for analysis")

    required_cols = ["Date", "Position"]
    for df in data_list:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    # Align all data by date and handle timeframe differences
    aligned_data = [data_list[0]]  # Start with first dataframe
    for i in range(1, len(data_list)):
        df_aligned, next_aligned = align_data(
            aligned_data[-1],
            data_list[i],
            is_hourly_1=config_list[i-1].get('USE_HOURLY', False),
            is_hourly_2=config_list[i].get('USE_HOURLY', False)
        )
        # Update previous alignments and add new one
        aligned_data[-1] = df_aligned
        aligned_data.append(next_aligned)
    
    # Calculate concurrent positions across all strategies
    position_arrays = [df["Position"].fill_null(0).to_numpy() for df in aligned_data]
    concurrent_matrix = np.column_stack(position_arrays)
    
    # Calculate number of active strategies at each timepoint
    active_strategies = np.sum(concurrent_matrix, axis=1)
    
    # Calculate statistics
    total_periods = len(aligned_data[0])
    concurrent_periods = np.sum(active_strategies >= 2)
    exclusive_periods = np.sum(active_strategies == 1)  # Exactly one strategy in position
    inactive_periods = np.sum(active_strategies == 0)  # No active strategies
    max_concurrent = int(np.max(active_strategies))
    
    # Calculate average concurrent strategies only for active periods
    active_mask = active_strategies >= 1
    avg_concurrent = float(np.mean(active_strategies[active_mask])) if np.any(active_mask) else 0.0
    
    # Calculate pairwise correlations
    correlations: Dict[str, float] = {}
    for i in range(len(position_arrays)):
        for j in range(i+1, len(position_arrays)):
            key = f"correlation_{i+1}_{j+1}"
            correlations[key] = float(np.corrcoef(position_arrays[i], position_arrays[j])[0, 1])
    
    # Calculate risk concentration index
    risk_concentration_index = avg_concurrent / max_concurrent if max_concurrent > 0 else 0.0
    
    stats: ConcurrencyStats = {
        "total_periods": total_periods,
        "total_concurrent_periods": int(concurrent_periods),
        "exclusive_periods": int(exclusive_periods),
        "concurrency_ratio": float(concurrent_periods / total_periods),
        "exclusive_ratio": float(exclusive_periods / total_periods),
        "inactive_ratio": float(inactive_periods / total_periods),
        "avg_concurrent_strategies": avg_concurrent,
        "risk_concentration_index": risk_concentration_index,
        "max_concurrent_strategies": max_concurrent,
        "strategy_correlations": correlations,
        "avg_position_length": float(
            sum(df["Position"].sum() for df in aligned_data) / len(aligned_data)
        )
    }
    
    return stats, aligned_data
