"""Risk metrics calculation for concurrency analysis."""

from typing import Dict, List, Callable, Any
import numpy as np
import polars as pl
from app.tools.stop_loss_simulator import apply_stop_loss_to_returns

# Import fixed implementation if available
try:
    from app.concurrency.tools.risk_contribution_calculator import calculate_risk_contributions_fixed
    FIXED_IMPLEMENTATION_AVAILABLE = True
except ImportError:
    FIXED_IMPLEMENTATION_AVAILABLE = False

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
    Also calculates risk-adjusted Alpha for each strategy relative to the portfolio average.

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
            - Risk-adjusted alpha metrics for each strategy (excess return per unit of volatility)

    Raises:
        ValueError: If input arrays are empty or mismatched
        Exception: If calculation fails
    """
    # Always use the fixed implementation
    if FIXED_IMPLEMENTATION_AVAILABLE:
        log("Using fixed risk contribution calculation", "info")
        return calculate_risk_contributions_fixed(
            position_arrays, data_list, strategy_allocations, log, strategy_configs
        )
    else:
        raise ImportError("Fixed risk contribution implementation not available")


def calculate_risk_contributions_legacy(
    position_arrays: List[np.ndarray],
    data_list: List[pl.DataFrame],
    strategy_allocations: List[float],
    log: Callable[[str, str], None],
    strategy_configs: List[Dict[str, Any]] = None
) -> Dict[str, float]:
    """Legacy risk contribution calculation (deprecated).
    
    This function is kept for reference but should not be used.
    Use calculate_risk_contributions() instead.
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

        # Calculate return-based covariance matrix for portfolio risk
        log("Calculating return-based covariance matrix", "info")
        
        # Extract returns from each strategy for covariance calculation
        all_returns = []
        min_length = float('inf')
        
        for i, df in enumerate(data_list):
            close_prices = df["Close"].to_numpy()
            returns = np.diff(close_prices) / close_prices[:-1]
            all_returns.append(returns)
            min_length = min(min_length, len(returns))
        
        # Create aligned return matrix
        return_matrix = np.zeros((min_length, len(data_list)))
        for i, returns in enumerate(all_returns):
            return_matrix[:, i] = returns[:min_length]
        
        # Calculate covariance matrix from returns
        covariance_matrix = np.cov(return_matrix.T)
        
        # Check for NaN values in covariance matrix
        if np.any(np.isnan(covariance_matrix)):
            log("Warning: NaN values detected in covariance matrix, using identity matrix", "warning")
            # Use a small identity matrix as fallback
            covariance_matrix = np.eye(len(strategy_allocations)) * 0.0001
        
        # Handle NaN values in covariance matrix (can occur with zero variance)
        if np.isnan(covariance_matrix).any():
            log("Warning: NaN values detected in covariance matrix, replacing with zeros", "warning")
            covariance_matrix = np.nan_to_num(covariance_matrix, nan=0.0)

        # Calculate portfolio risk using proper portfolio theory: σ_p² = w^T Σ w
        total_allocation = sum(strategy_allocations)
        
        # Create weight vector - use equal weights if no allocations provided
        if total_allocation > 0:
            weights = np.array([alloc / total_allocation for alloc in strategy_allocations])
            log(f"Using provided allocations (total: {total_allocation:.2f}%)", "info")
        else:
            weights = np.ones(len(strategy_allocations)) / len(strategy_allocations)
            log(f"No allocations provided, using equal weights ({100/len(strategy_allocations):.2f}% each)", "info")
        
        # Calculate portfolio variance: w^T * Σ * w
        portfolio_variance = np.dot(weights, np.dot(covariance_matrix, weights))
        log(f"Portfolio variance calculated: {portfolio_variance:.8f}", "info")
        
        # Handle NaN and negative values in portfolio variance
        if np.isnan(portfolio_variance) or portfolio_variance < 0:
            log(f"Warning: Invalid portfolio variance ({portfolio_variance}), setting to 0", "warning")
            portfolio_variance = 0.0
            portfolio_risk = 0.0
        elif portfolio_variance > 0:
            portfolio_risk = np.sqrt(portfolio_variance)
            # Additional safety check for NaN in portfolio_risk
            if np.isnan(portfolio_risk):
                log("Warning: NaN detected in portfolio risk calculation, setting to 0", "warning")
                portfolio_risk = 0.0
        else:
            portfolio_risk = 0.0
            
        log(f"Portfolio risk calculated (allocation-weighted): {portfolio_risk:.4f}", "info")

        # Calculate marginal risk contributions and Alpha metrics
        if portfolio_risk > 0:
            log("Calculating individual strategy risk contributions and alphas", "info")
            for i in range(n_strategies):
                # Calculate marginal contribution to portfolio risk: (Σ * w)_i
                marginal_contrib = np.dot(covariance_matrix[i, :], weights)

                # Risk contribution: w_i * marginal_contrib / portfolio_risk
                risk_contrib = (weights[i] * marginal_contrib) / portfolio_risk
                
                # Handle potential NaN values
                if np.isnan(risk_contrib):
                    log(f"Warning: NaN detected in risk contribution for strategy {i+1}, setting to 0", "warning")
                    risk_contrib = 0.0
                    
                risk_contributions[f"strategy_{i+1}_risk_contrib"] = float(risk_contrib)
                log(f"Strategy {i+1} risk contribution: {risk_contrib:.4f}", "info")

                # Calculate Risk-Adjusted Alpha (excess return over benchmark, adjusted for volatility)
                excess_return = strategy_returns[i] - benchmark_return
                strategy_volatility = volatilities[i]
                
                if strategy_volatility > 0:
                    # Risk-adjusted alpha: excess return per unit of risk
                    risk_adjusted_alpha = excess_return / strategy_volatility
                else:
                    # If no volatility, use raw excess return (fallback for edge cases)
                    risk_adjusted_alpha = excess_return
                
                # Handle potential NaN values in alpha
                if np.isnan(risk_adjusted_alpha):
                    log(f"Warning: NaN detected in alpha for strategy {i+1}, setting to 0", "warning")
                    risk_adjusted_alpha = 0.0
                    
                risk_contributions[f"strategy_{i+1}_alpha_to_portfolio"] = float(risk_adjusted_alpha)
                log(f"Strategy {i+1} excess return: {excess_return:.6f}, volatility: {strategy_volatility:.6f}", "info")
                log(f"Strategy {i+1} risk-adjusted alpha to portfolio: {risk_adjusted_alpha:.6f}", "info")

                # Calculate pairwise risk overlaps
                for j in range(i+1, n_strategies):
                    if portfolio_variance > 0:
                        # Risk overlap: w_i * w_j * σ_ij / portfolio_variance
                        overlap = float((weights[i] * weights[j] * covariance_matrix[i, j]) / portfolio_variance)
                    else:
                        overlap = 0.0
                    
                    # Handle potential NaN values
                    if np.isnan(overlap):
                        log(f"Warning: NaN detected in risk overlap between strategy {i+1} and {j+1}, setting to 0", "warning")
                        overlap = 0.0
                        
                    risk_contributions[f"risk_overlap_{i+1}_{j+1}"] = overlap
                    log(f"Risk overlap between strategy {i+1} and {j+1}: {overlap:.4f}", "info")
        else:
            # Set default values when portfolio risk is 0
            log("Portfolio risk is 0, setting default risk contributions", "info")
            for i in range(n_strategies):
                risk_contributions[f"strategy_{i+1}_risk_contrib"] = 0.0
                risk_contributions[f"strategy_{i+1}_alpha_to_portfolio"] = 0.0
                
                # Also set default pairwise risk overlaps
                for j in range(i+1, n_strategies):
                    risk_contributions[f"risk_overlap_{i+1}_{j+1}"] = 0.0

        risk_contributions["total_portfolio_risk"] = portfolio_risk
        risk_contributions["benchmark_return"] = float(benchmark_return)

        log("Risk contribution calculations completed successfully", "info")
        return risk_contributions

    except Exception as e:
        log(f"Error calculating risk contributions: {str(e)}", "error")
        raise
