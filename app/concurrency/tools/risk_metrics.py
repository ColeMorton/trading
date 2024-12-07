"""Risk metrics calculation for concurrency analysis."""

from typing import Dict, List
import numpy as np
import polars as pl

def calculate_risk_contributions(
    position_arrays: List[np.ndarray],
    data_list: List[pl.DataFrame]
) -> Dict[str, float]:
    """Calculate risk contribution metrics for concurrent strategies.

    Uses position-weighted volatility and correlation to determine how much
    each strategy contributes to overall portfolio risk during concurrent periods.
    Also calculates Alpha for each strategy relative to the average return.

    Args:
        position_arrays (List[np.ndarray]): List of position arrays for each strategy
        data_list (List[pl.DataFrame]): List of dataframes with price data

    Returns:
        Dict[str, float]: Dictionary containing:
            - Individual strategy risk contributions
            - Pairwise risk overlaps
            - Total portfolio risk
            - Alpha metrics for each strategy
    """
    n_strategies = len(position_arrays)
    
    # Calculate returns and volatilities for each strategy
    volatilities = []
    strategy_returns = []
    for i, df in enumerate(data_list):
        # Calculate returns from Close prices
        close_prices = df["Close"].to_numpy()
        returns = np.diff(close_prices) / close_prices[:-1]
        # Only consider periods where strategy was active
        active_positions = position_arrays[i][1:]  # Align with returns
        active_returns = returns[active_positions != 0]
        vol = float(np.std(active_returns)) if len(active_returns) > 0 else 0.0
        avg_return = float(np.mean(active_returns)) if len(active_returns) > 0 else 0.0
        volatilities.append(vol)
        strategy_returns.append(avg_return)
    
    # Calculate benchmark return (average of all strategies)
    benchmark_return = np.mean(strategy_returns)
    
    # Calculate position-weighted covariance matrix
    weighted_positions = []
    for pos, vol in zip(position_arrays, volatilities):
        weighted_positions.append(pos * vol)
    
    position_matrix = np.column_stack(weighted_positions)
    covariance_matrix = np.cov(position_matrix.T)
    
    # Calculate portfolio risk
    portfolio_variance = np.sum(covariance_matrix)
    portfolio_risk = np.sqrt(portfolio_variance) if portfolio_variance > 0 else 0.0
    
    # Calculate marginal risk contributions and Alpha metrics
    risk_contributions: Dict[str, float] = {}
    
    if portfolio_risk > 0:
        for i in range(n_strategies):
            # Calculate marginal contribution
            marginal_contrib = np.sum(covariance_matrix[i, :]) / portfolio_risk
            
            # Normalize by total risk
            relative_contrib = marginal_contrib / portfolio_risk
            risk_contributions[f"strategy_{i+1}_risk_contrib"] = float(relative_contrib)
            
            # Calculate Alpha (excess return over benchmark)
            alpha = strategy_returns[i] - benchmark_return
            risk_contributions[f"strategy_{i+1}_alpha"] = float(alpha)
            
            # Calculate pairwise risk overlaps
            for j in range(i+1, n_strategies):
                overlap = float(covariance_matrix[i, j] / portfolio_variance)
                risk_contributions[f"risk_overlap_{i+1}_{j+1}"] = overlap
    
    risk_contributions["total_portfolio_risk"] = portfolio_risk
    risk_contributions["benchmark_return"] = float(benchmark_return)
    
    return risk_contributions
