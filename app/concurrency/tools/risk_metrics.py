"""Risk metrics calculation for concurrency analysis."""

from typing import Dict, List, Callable, Any
import numpy as np
import polars as pl
from app.tools.stop_loss_simulator import apply_stop_loss_to_returns

def calculate_risk_contributions(
    position_arrays: List[np.ndarray],
    data_list: List[pl.DataFrame],
    strategy_allocations: List[float],
    log: Callable[[str, str], None],
    strategy_configs: List[Dict[str, Any]] = None
) -> Dict[str, float]:
    """Calculate risk contribution metrics for concurrent strategies.

    Uses position-weighted volatility and correlation to determine how much
    each strategy contributes to overall portfolio risk during concurrent periods.
    Also calculates Alpha for each strategy relative to the average return.

    Args:
        position_arrays (List[np.ndarray]): List of position arrays for each strategy
        data_list (List[pl.DataFrame]): List of dataframes with price data
        strategy_allocations (List[float]): List of strategy allocations
        log (Callable[[str, str], None]): Logging function
        strategy_configs (List[Dict[str, Any]], optional): List of strategy configurations

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
        if not position_arrays or not data_list or not strategy_allocations:
            log("Empty input arrays provided", "error")
            raise ValueError("Position arrays, data list, and strategy allocations cannot be empty")

        if len(position_arrays) != len(data_list) or len(position_arrays) != len(strategy_allocations):
            log("Mismatched input arrays", "error")
            raise ValueError("Number of position arrays, dataframes, and strategy allocations must match")

        n_strategies = len(position_arrays)
        log(f"Calculating risk contributions for {n_strategies} strategies", "info")

        # Initialize risk contributions dictionary
        risk_contributions: Dict[str, float] = {}

        # Calculate returns and volatilities for each strategy
        log("Calculating strategy returns and volatilities", "info")
        volatilities = []
        strategy_returns = []
        all_active_returns = []  # Store all active returns for combined VaR/CVaR
        weighted_active_returns = [] # Store returns weighted by allocation
        for i, df in enumerate(data_list):
            # Get stop loss value if available
            stop_loss = None
            if strategy_configs and i < len(strategy_configs):
                stop_loss = strategy_configs[i].get('STOP_LOSS')
                if stop_loss is not None:
                    log(f"Using stop loss of {stop_loss*100:.2f}% for strategy {i+1}", "info")
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

            # Collect active returns for combined calculations
            if len(active_returns) > 0:
                # Apply stop loss if available
                if stop_loss is not None and stop_loss > 0 and stop_loss < 1:
                    # Create signal array (1 for long, -1 for short)
                    signal_array = np.ones_like(active_returns)
                    if "DIRECTION" in strategy_configs[i] and strategy_configs[i]["DIRECTION"] == "Short":
                        signal_array = -1 * signal_array
                        
                    # Apply stop loss to active returns
                    adjusted_returns, stop_loss_triggers = apply_stop_loss_to_returns(
                        active_returns, signal_array, stop_loss, log
                    )
                    
                    # Log stop loss impact
                    trigger_count = int(np.sum(stop_loss_triggers))
                    if trigger_count > 0:
                        log(f"Stop loss triggered {trigger_count} times for strategy {i+1}", "info")
                        
                    # Use adjusted returns for risk calculations
                    all_active_returns.extend(adjusted_returns)
                    # Store returns for this strategy (without weighting)
                    weighted_active_returns.extend(adjusted_returns)
                else:
                    # Use original returns if no stop loss
                    all_active_returns.extend(active_returns)
                    # Store returns for this strategy (without weighting)
                    weighted_active_returns.extend(active_returns)

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

        # Calculate combined VaR and CVaR metrics using allocation-weighted approach
        log("Calculating combined VaR and CVaR metrics", "info")
        if all_active_returns and strategy_allocations:
            # Calculate weighted average of individual VaR/CVaR values based on allocations
            total_allocation = sum(strategy_allocations)
            
            # Initialize combined risk metrics
            combined_var_95 = 0.0
            combined_var_99 = 0.0
            combined_cvar_95 = 0.0
            combined_cvar_99 = 0.0
            
            # Calculate weighted average of individual strategy risk metrics
            for i in range(n_strategies):
                # Get allocation weight (as a proportion of total allocation)
                # Handle case when total_allocation is zero by using equal weights
                allocation_weight = strategy_allocations[i] / total_allocation if total_allocation > 0 else 1.0 / n_strategies
                
                # Get individual strategy risk metrics
                var_95 = risk_contributions.get(f"strategy_{i+1}_var_95", 0.0)
                var_99 = risk_contributions.get(f"strategy_{i+1}_var_99", 0.0)
                cvar_95 = risk_contributions.get(f"strategy_{i+1}_cvar_95", 0.0)
                cvar_99 = risk_contributions.get(f"strategy_{i+1}_cvar_99", 0.0)
                
                # Add weighted contribution to combined metrics
                combined_var_95 += var_95 * allocation_weight
                combined_var_99 += var_99 * allocation_weight
                combined_cvar_95 += cvar_95 * allocation_weight
                combined_cvar_99 += cvar_99 * allocation_weight
            
            risk_contributions["combined_var_95"] = combined_var_95
            risk_contributions["combined_cvar_95"] = combined_cvar_95
            risk_contributions["combined_var_99"] = combined_var_99
            risk_contributions["combined_cvar_99"] = combined_cvar_99
            
            log(f"Combined VaR 95% (allocation-weighted): {combined_var_95:.4f}, CVaR 95%: {combined_cvar_95:.4f}", "info")
            log(f"Combined VaR 99% (allocation-weighted): {combined_var_99:.4f}, CVaR 99%: {combined_cvar_99:.4f}", "info")
        else:
            log("No active returns for combined VaR/CVaR calculation", "info")
            risk_contributions["combined_var_95"] = 0.0
            risk_contributions["combined_cvar_95"] = 0.0
            risk_contributions["combined_var_99"] = 0.0
            risk_contributions["combined_cvar_99"] = 0.0

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

        # Calculate portfolio risk with allocation weighting
        portfolio_variance = 0.0
        total_allocation = sum(strategy_allocations)
        
        # Create weighted covariance matrix
        weighted_covariance = np.zeros_like(covariance_matrix)
        for i in range(len(strategy_allocations)):
            for j in range(len(strategy_allocations)):
                weight_i = strategy_allocations[i] / total_allocation if total_allocation > 0 else 1.0 / len(strategy_allocations)
                weight_j = strategy_allocations[j] / total_allocation if total_allocation > 0 else 1.0 / len(strategy_allocations)
                weighted_covariance[i, j] = covariance_matrix[i, j] * weight_i * weight_j
        
        # Sum the weighted covariance matrix
        portfolio_variance = np.sum(weighted_covariance)
        portfolio_risk = np.sqrt(portfolio_variance) if portfolio_variance > 0 else 0.0
        log(f"Portfolio risk calculated (allocation-weighted): {portfolio_risk:.4f}", "info")

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
                risk_contributions[f"strategy_{i+1}_alpha_to_portfolio"] = float(alpha)
                log(f"Strategy {i+1} alpha to portfolio: {alpha:.4f}", "info")

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
