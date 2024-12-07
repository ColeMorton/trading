"""Core analysis functionality for concurrency analysis."""

from typing import Tuple, List, Dict
import polars as pl
import numpy as np
from app.concurrency.tools.types import ConcurrencyStats, StrategyConfig
from app.concurrency.tools.data_alignment import align_data
from app.concurrency.tools.risk_metrics import calculate_risk_contributions

def calculate_efficiency_score(
    strategy_expectancies: List[float],
    avg_correlation: float,
    concurrent_periods: int,
    exclusive_periods: int,
    inactive_periods: int,
    total_periods: int
) -> float:
    """Calculate efficiency score for concurrent strategies.

    Args:
        strategy_expectancies (List[float]): List of strategy expectancies
        avg_correlation (float): Average correlation between strategies
        concurrent_periods (int): Number of concurrent trading periods
        exclusive_periods (int): Number of exclusive trading periods
        inactive_periods (int): Number of inactive periods
        total_periods (int): Total number of periods

    Returns:
        float: Efficiency score
    """
    total_expectancy = sum(strategy_expectancies)
    
    if total_expectancy > 0:
        # Calculate diversification multiplier (penalizes high correlations)
        diversification_multiplier = 1 - avg_correlation
        
        # Calculate strategy independence multiplier
        independence_multiplier = (
            exclusive_periods / (concurrent_periods + exclusive_periods)
            if (concurrent_periods + exclusive_periods) > 0
            else 0
        )
        
        # Calculate activity multiplier (penalizes inactive periods)
        activity_multiplier = 1 - (inactive_periods / total_periods)
        
        # Calculate final efficiency score
        return (
            total_expectancy * 
            diversification_multiplier * 
            independence_multiplier * 
            activity_multiplier
        )
    
    return 0.0

def analyze_concurrency(
    data_list: List[pl.DataFrame],
    config_list: List[StrategyConfig]
) -> Tuple[ConcurrencyStats, List[pl.DataFrame]]:
    """Analyze concurrent positions across multiple strategies.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals
        config_list (List[StrategyConfig]): List of configurations

    Returns:
        Tuple[ConcurrencyStats, List[pl.DataFrame]]: Statistics and aligned data

    Raises:
        ValueError: If invalid input data
    """
    if len(data_list) != len(config_list):
        raise ValueError("Number of dataframes must match number of configurations")
    
    if len(data_list) < 2:
        raise ValueError("At least two strategies are required for analysis")

    required_cols = ["Date", "Position", "Close"]
    for df in data_list:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    # Align all data by date and handle timeframe differences
    aligned_data = [data_list[0]]
    for i in range(1, len(data_list)):
        df_aligned, next_aligned = align_data(
            aligned_data[-1],
            data_list[i],
            is_hourly_1=config_list[i-1].get('USE_HOURLY', False),
            is_hourly_2=config_list[i].get('USE_HOURLY', False)
        )
        aligned_data[-1] = df_aligned
        aligned_data.append(next_aligned)
    
    # Calculate concurrent positions
    position_arrays = [df["Position"].fill_null(0).to_numpy() for df in aligned_data]
    concurrent_matrix = np.column_stack(position_arrays)
    active_strategies = np.sum(concurrent_matrix, axis=1)
    
    # Calculate basic statistics
    total_periods = len(aligned_data[0])
    concurrent_periods = np.sum(active_strategies >= 2)
    exclusive_periods = np.sum(active_strategies == 1)
    inactive_periods = np.sum(active_strategies == 0)
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
        config.get('Expectancy per Day', 0)
        for config in config_list
    ]
    efficiency_score = calculate_efficiency_score(
        strategy_expectancies,
        avg_correlation,
        concurrent_periods,
        exclusive_periods,
        inactive_periods,
        total_periods
    )
    
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
        ),
        "efficiency_score": efficiency_score,
        "risk_metrics": risk_metrics
    }
    
    return stats, aligned_data
