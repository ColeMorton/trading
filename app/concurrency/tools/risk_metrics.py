"""Risk metrics calculation for concurrency analysis."""

from typing import Dict, List, Callable
import numpy as np
import polars as pl

def calculate_risk_contributions(
    position_arrays: List[np.ndarray],
    data_list: List[pl.DataFrame],
    log: Callable[[str, str], None]
) -> Dict[str, float]:
    """Calculate risk contribution metrics for concurrent strategies.

    Uses position-weighted volatility and correlation to determine how much
    each strategy contributes to overall portfolio risk during concurrent periods.
    Also calculates Alpha for each strategy relative to the average return.

    Args:
        position_arrays (List[np.ndarray]): List of position arrays for each strategy
        data_list (List[pl.DataFrame]): List of dataframes with price data
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, float]: Dictionary containing:
            - Individual strategy risk contributions
            - Value at Risk (VaR) at 95% and 99% confidence levels
            - Conditional Value at Risk (CVaR) at 95% and 99% confidence levels
            - Pairwise risk overlaps
            - Total portfolio risk
            - Alpha metrics for each strategy

    Raises:
        ValueError: If input arrays are empty or mismatched
        Exception: If calculation fails
    """
    try:
        if not position_arrays or not data_list:
            log("Empty input arrays provided", "error")
            raise ValueError("Position arrays and data list cannot be empty")
            
        if len(position_arrays) != len(data_list):
            log("Mismatched input arrays", "error")
            raise ValueError("Number of position arrays must match number of dataframes")

        n_strategies = len(position_arrays)
        log(f"Calculating risk contributions for {n_strategies} strategies", "info")
        
        # Initialize risk contributions dictionary
        risk_contributions: Dict[str, float] = {}
        
        # Calculate returns and volatilities for each strategy
        log("Calculating strategy returns and volatilities", "info")
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
            
            # Calculate VaR and CVaR for active returns
            if len(active_returns) > 0:
                # Sort returns for percentile calculations
                sorted_returns = np.sort(active_returns)
                
                # Calculate VaR 95% and 99%
                var_95 = float(np.percentile(sorted_returns, 5))  # 5th percentile for 95% confidence
                var_99 = float(np.percentile(sorted_returns, 1))  # 1st percentile for 99% confidence
                
                # Calculate CVaR 95% and 99%
                cvar_95 = float(np.mean(sorted_returns[sorted_returns <= var_95]))
                cvar_99 = float(np.mean(sorted_returns[sorted_returns <= var_99]))
                
                risk_contributions[f"strategy_{i+1}_var_95"] = var_95
                risk_contributions[f"strategy_{i+1}_cvar_95"] = cvar_95
                risk_contributions[f"strategy_{i+1}_var_99"] = var_99
                risk_contributions[f"strategy_{i+1}_cvar_99"] = cvar_99
                
                log(f"Strategy {i+1} - Volatility: {vol:.4f}, Average Return: {avg_return:.4f}", "info")
                log(f"Strategy {i+1} - VaR 95%: {var_95:.4f}, CVaR 95%: {cvar_95:.4f}", "info")
                log(f"Strategy {i+1} - VaR 99%: {var_99:.4f}, CVaR 99%: {cvar_99:.4f}", "info")
            else:
                risk_contributions[f"strategy_{i+1}_var_95"] = 0.0
                risk_contributions[f"strategy_{i+1}_cvar_95"] = 0.0
                risk_contributions[f"strategy_{i+1}_var_99"] = 0.0
                risk_contributions[f"strategy_{i+1}_cvar_99"] = 0.0
                log(f"Strategy {i+1} - Volatility: {vol:.4f}, Average Return: {avg_return:.4f}", "info")
                log(f"Strategy {i+1} - No active returns for VaR/CVaR calculation", "info")
        
        # Calculate benchmark return (average of all strategies)
        benchmark_return = np.mean(strategy_returns)
        log(f"Benchmark return calculated: {benchmark_return:.4f}", "info")
        
        # Calculate position-weighted covariance matrix
        log("Calculating position-weighted covariance matrix", "info")
        weighted_positions = []
        for pos, vol in zip(position_arrays, volatilities):
            weighted_positions.append(pos * vol)
        
        position_matrix = np.column_stack(weighted_positions)
        covariance_matrix = np.cov(position_matrix.T)
        
        # Calculate portfolio risk
        portfolio_variance = np.sum(covariance_matrix)
        portfolio_risk = np.sqrt(portfolio_variance) if portfolio_variance > 0 else 0.0
        log(f"Portfolio risk calculated: {portfolio_risk:.4f}", "info")
        
        # Calculate marginal risk contributions and Alpha metrics
        if portfolio_risk > 0:
            log("Calculating individual strategy risk contributions and alphas", "info")
            for i in range(n_strategies):
                # Calculate marginal contribution
                marginal_contrib = np.sum(covariance_matrix[i, :]) / portfolio_risk
                
                # Normalize by total risk
                relative_contrib = marginal_contrib / portfolio_risk
                risk_contributions[f"strategy_{i+1}_risk_contrib"] = float(relative_contrib)
                log(f"Strategy {i+1} risk contribution: {relative_contrib:.4f}", "info")
                
                # Calculate Alpha (excess return over benchmark)
                alpha = strategy_returns[i] - benchmark_return
                risk_contributions[f"strategy_{i+1}_alpha"] = float(alpha)
                log(f"Strategy {i+1} alpha: {alpha:.4f}", "info")
                
                # Calculate pairwise risk overlaps
                for j in range(i+1, n_strategies):
                    overlap = float(covariance_matrix[i, j] / portfolio_variance)
                    risk_contributions[f"risk_overlap_{i+1}_{j+1}"] = overlap
                    log(f"Risk overlap between strategy {i+1} and {j+1}: {overlap:.4f}", "info")
        
        risk_contributions["total_portfolio_risk"] = portfolio_risk
        risk_contributions["benchmark_return"] = float(benchmark_return)
        
        log("Risk contribution calculations completed successfully", "info")
        return risk_contributions
        
    except Exception as e:
        log(f"Error calculating risk contributions: {str(e)}", "error")
        raise
