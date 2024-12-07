"""Core analysis functionality for concurrency analysis."""

from typing import Tuple, List, Dict
import polars as pl
import numpy as np
from app.concurrency.tools.types import ConcurrencyStats, StrategyConfig
from app.concurrency.tools.data_alignment import align_data

def calculate_risk_contributions(
    position_arrays: List[np.ndarray],
    data_list: List[pl.DataFrame]
) -> Dict[str, float]:
    """Calculate risk contribution metrics for concurrent strategies.

    Uses position-weighted volatility and correlation to determine how much
    each strategy contributes to overall portfolio risk during concurrent periods.

    Args:
        position_arrays (List[np.ndarray]): List of position arrays for each strategy
        data_list (List[pl.DataFrame]): List of dataframes with price data

    Returns:
        Dict[str, float]: Dictionary containing:
            - Individual strategy risk contributions
            - Pairwise risk overlaps
            - Total portfolio risk
    """
    n_strategies = len(position_arrays)
    
    # Calculate returns and volatilities for each strategy
    volatilities = []
    for i, df in enumerate(data_list):
        # Calculate returns from Close prices
        close_prices = df["Close"].to_numpy()
        returns = np.diff(close_prices) / close_prices[:-1]
        # Only consider periods where strategy was active
        active_positions = position_arrays[i][1:]  # Align with returns
        active_returns = returns[active_positions != 0]
        vol = float(np.std(active_returns)) if len(active_returns) > 0 else 0.0
        volatilities.append(vol)
    
    # Calculate position-weighted covariance matrix
    weighted_positions = []
    for pos, vol in zip(position_arrays, volatilities):
        weighted_positions.append(pos * vol)
    
    position_matrix = np.column_stack(weighted_positions)
    covariance_matrix = np.cov(position_matrix.T)
    
    # Calculate portfolio risk
    portfolio_variance = np.sum(covariance_matrix)
    portfolio_risk = np.sqrt(portfolio_variance) if portfolio_variance > 0 else 0.0
    
    # Calculate marginal risk contributions
    risk_contributions: Dict[str, float] = {}
    
    if portfolio_risk > 0:
        for i in range(n_strategies):
            # Calculate marginal contribution
            marginal_contrib = np.sum(covariance_matrix[i, :]) / portfolio_risk
            
            # Normalize by total risk
            relative_contrib = marginal_contrib / portfolio_risk
            risk_contributions[f"strategy_{i+1}_risk_contrib"] = float(relative_contrib)
            
            # Calculate pairwise risk overlaps
            for j in range(i+1, n_strategies):
                overlap = float(covariance_matrix[i, j] / portfolio_variance)
                risk_contributions[f"risk_overlap_{i+1}_{j+1}"] = overlap
    
    risk_contributions["total_portfolio_risk"] = portfolio_risk
    
    return risk_contributions

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

    required_cols = ["Date", "Position", "Close"]
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
    avg_correlation = 0.0
    correlation_count = 0
    for i in range(len(position_arrays)):
        for j in range(i+1, len(position_arrays)):
            correlation = float(np.corrcoef(position_arrays[i], position_arrays[j])[0, 1])
            key = f"correlation_{i+1}_{j+1}"
            correlations[key] = correlation
            avg_correlation += abs(correlation)  # Use absolute correlation
            correlation_count += 1
    
    # Calculate average absolute correlation
    avg_correlation = avg_correlation / correlation_count if correlation_count > 0 else 0.0
    
    # Calculate risk concentration index
    risk_concentration_index = avg_concurrent / max_concurrent if max_concurrent > 0 else 0.0
    
    # Calculate risk contributions using Close prices
    risk_metrics = calculate_risk_contributions(position_arrays, aligned_data)
    
    # Calculate improved efficiency score
    strategy_expectancies = [config.get('Expectancy per Day', 0) for config in config_list]
    total_expectancy = sum(strategy_expectancies)
    
    if total_expectancy > 0:
        # Calculate diversification multiplier (penalizes high correlations)
        diversification_multiplier = 1 - avg_correlation
        
        # Calculate strategy independence multiplier (rewards exclusive trading periods)
        independence_multiplier = exclusive_periods / (concurrent_periods + exclusive_periods) if (concurrent_periods + exclusive_periods) > 0 else 0
        
        # Calculate activity multiplier (penalizes inactive periods)
        activity_multiplier = 1 - (inactive_periods / total_periods)
        
        # Calculate final efficiency score
        efficiency_score = (
            total_expectancy * 
            diversification_multiplier * 
            independence_multiplier * 
            activity_multiplier
        )
    else:
        efficiency_score = 0.0
    
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
