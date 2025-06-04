"""Risk metrics calculation for concurrency analysis."""

import os
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd
import polars as pl

from app.tools.stop_loss_simulator import apply_stop_loss_to_returns

# Import fixed implementations
try:
    from app.concurrency.tools.risk_contribution_calculator import (
        calculate_risk_contributions_fixed,
    )

    FIXED_IMPLEMENTATION_AVAILABLE = True
except ImportError:
    FIXED_IMPLEMENTATION_AVAILABLE = False

try:
    from app.concurrency.tools.risk_metrics_validator import (
        DrawdownCalculator,
        RiskMetricsValidator,
        VolatilityAggregator,
    )

    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False

# Configuration
USE_FIXED_DRAWDOWN_CALC = os.getenv("USE_FIXED_DRAWDOWN_CALC", "true").lower() == "true"


def calculate_portfolio_max_drawdown_fixed(
    strategy_equity_curves: List[np.ndarray],
    allocation_weights: List[float],
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """
    Calculate portfolio max drawdown using proper equity curve combination.

    This function addresses the core issue where portfolio drawdowns are
    understated by 27-44 percentage points by using actual combined
    equity curves rather than weighted averages of individual drawdowns.

    Args:
        strategy_equity_curves: List of equity curves for each strategy
        allocation_weights: Allocation weights for each strategy
        log: Optional logging function

    Returns:
        Dictionary with max drawdown metrics
    """
    if VALIDATION_AVAILABLE and USE_FIXED_DRAWDOWN_CALC:
        calculator = DrawdownCalculator()
        drawdown_components = calculator.calculate_portfolio_max_drawdown(
            strategy_equity_curves, allocation_weights, log
        )

        return {
            "max_drawdown": drawdown_components.max_drawdown,
            "peak_date": drawdown_components.peak_date,
            "trough_date": drawdown_components.trough_date,
            "recovery_date": drawdown_components.recovery_date,
            "drawdown_duration": drawdown_components.drawdown_duration,
            "recovery_duration": drawdown_components.recovery_duration,
            "equity_curve": drawdown_components.equity_curve,
        }
    else:
        # Fallback to legacy calculation
        return calculate_portfolio_max_drawdown_legacy(
            strategy_equity_curves, allocation_weights, log
        )


def calculate_portfolio_max_drawdown_legacy(
    strategy_equity_curves: List[np.ndarray],
    allocation_weights: List[float],
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """
    Legacy portfolio max drawdown calculation (understated).

    This is the old method that causes understatement issues.
    Kept for comparison and fallback purposes.
    """
    if not strategy_equity_curves or not allocation_weights:
        return {"max_drawdown": 0.0}

    # Legacy method: weighted average of individual max drawdowns
    individual_drawdowns = []

    for curve in strategy_equity_curves:
        if len(curve) > 0:
            running_max = np.maximum.accumulate(curve)
            drawdowns = (running_max - curve) / running_max
            max_dd = np.max(drawdowns)
            individual_drawdowns.append(max_dd)
        else:
            individual_drawdowns.append(0.0)

    # Calculate weighted average (this is the problematic method)
    total_allocation = sum(allocation_weights)
    if total_allocation > 0:
        weighted_dd = (
            sum(
                dd * weight
                for dd, weight in zip(individual_drawdowns, allocation_weights)
            )
            / total_allocation
        )
    else:
        weighted_dd = np.mean(individual_drawdowns) if individual_drawdowns else 0.0

    if log:
        log(f"Legacy drawdown calculation: {weighted_dd:.4f} (understated)", "warning")

    return {"max_drawdown": weighted_dd}


def calculate_portfolio_volatility_fixed(
    individual_volatilities: List[float],
    correlation_matrix: np.ndarray,
    allocation_weights: List[float],
    log: Optional[Callable[[str, str], None]] = None,
) -> float:
    """
    Calculate portfolio volatility using proper portfolio theory.

    This addresses volatility aggregation issues by using the correct
    portfolio theory formula: σ_p = sqrt(w^T * Σ * w)

    Args:
        individual_volatilities: List of individual strategy volatilities
        correlation_matrix: Correlation matrix between strategies
        allocation_weights: Allocation weights for each strategy
        log: Optional logging function

    Returns:
        Portfolio volatility
    """
    if VALIDATION_AVAILABLE:
        aggregator = VolatilityAggregator()
        return aggregator.calculate_portfolio_volatility(
            individual_volatilities, correlation_matrix, allocation_weights, log
        )
    else:
        # Fallback to simple weighted average (incorrect but functional)
        if not individual_volatilities or not allocation_weights:
            return 0.0

        total_allocation = sum(allocation_weights)
        if total_allocation > 0:
            weights = [w / total_allocation for w in allocation_weights]
            weighted_vol = sum(
                vol * weight for vol, weight in zip(individual_volatilities, weights)
            )
        else:
            weighted_vol = np.mean(individual_volatilities)

        if log:
            log(
                f"Legacy volatility calculation: {weighted_vol:.4f} (may be inaccurate)",
                "warning",
            )

        return weighted_vol


def calculate_portfolio_var_fixed(
    strategy_returns: List[np.ndarray],
    allocation_weights: List[float],
    confidence_levels: List[float] = [0.95, 0.99],
    method: str = "historical",
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, float]:
    """
    Calculate portfolio Value at Risk (VaR) using proper methodology.

    This function addresses VaR calculation issues by implementing:
    - Portfolio-level VaR using combined returns
    - Multiple confidence levels (95%, 99%)
    - Historical and parametric methods
    - Proper handling of correlation effects

    Args:
        strategy_returns: List of return series for each strategy
        allocation_weights: Allocation weights for each strategy
        confidence_levels: List of confidence levels (e.g., [0.95, 0.99])
        method: VaR calculation method ("historical", "parametric")
        log: Optional logging function

    Returns:
        Dictionary with VaR metrics at different confidence levels
    """
    try:
        if not strategy_returns or not allocation_weights:
            return {}

        if len(strategy_returns) != len(allocation_weights):
            raise ValueError(
                "Number of return series must match number of allocation weights"
            )

        # Normalize allocation weights
        total_allocation = sum(allocation_weights)
        if total_allocation <= 0:
            raise ValueError("Total allocation must be positive")

        normalized_weights = np.array(
            [w / total_allocation for w in allocation_weights]
        )

        # Find minimum length across all return series
        min_length = min(len(returns) for returns in strategy_returns)

        if min_length < 50:  # Need sufficient data for VaR
            if log:
                log(
                    f"Warning: Insufficient data for VaR calculation ({min_length} observations)",
                    "warning",
                )
            return {}

        # Create aligned return matrix
        aligned_returns = np.zeros((min_length, len(strategy_returns)))
        for i, returns in enumerate(strategy_returns):
            aligned_returns[:, i] = returns[:min_length]

        # Calculate portfolio returns using proper allocation weighting
        portfolio_returns = np.dot(aligned_returns, normalized_weights)

        var_results = {}

        for confidence_level in confidence_levels:
            alpha = 1 - confidence_level

            if method.lower() == "historical":
                # Historical VaR: Use empirical quantile
                var_value = float(np.percentile(portfolio_returns, alpha * 100))

                # Calculate Conditional VaR (Expected Shortfall)
                var_exceedances = portfolio_returns[portfolio_returns <= var_value]
                cvar_value = (
                    float(np.mean(var_exceedances))
                    if len(var_exceedances) > 0
                    else var_value
                )

            elif method.lower() == "parametric":
                # Parametric VaR: Assume normal distribution
                portfolio_mean = np.mean(portfolio_returns)
                portfolio_std = np.std(portfolio_returns)

                # Z-score for confidence level
                from scipy import stats

                z_score = stats.norm.ppf(alpha)

                var_value = float(portfolio_mean + z_score * portfolio_std)

                # Parametric CVaR for normal distribution
                cvar_value = float(
                    portfolio_mean - portfolio_std * stats.norm.pdf(z_score) / alpha
                )

            else:
                raise ValueError(f"Unknown VaR method: {method}")

            # Store results
            confidence_pct = int(confidence_level * 100)
            var_results[f"var_{confidence_pct}"] = var_value
            var_results[f"cvar_{confidence_pct}"] = cvar_value

            if log:
                log(
                    f"Portfolio VaR {confidence_pct}%: {var_value:.4f}, CVaR: {cvar_value:.4f} (method: {method})",
                    "info",
                )

        # Add portfolio return statistics
        var_results["portfolio_mean_return"] = float(np.mean(portfolio_returns))
        var_results["portfolio_volatility"] = float(np.std(portfolio_returns))
        var_results["portfolio_skewness"] = float(
            float(np.mean((portfolio_returns - np.mean(portfolio_returns)) ** 3))
            / (np.std(portfolio_returns) ** 3)
        )
        var_results["portfolio_kurtosis"] = float(
            float(np.mean((portfolio_returns - np.mean(portfolio_returns)) ** 4))
            / (np.std(portfolio_returns) ** 4)
        )
        var_results["observations"] = min_length

        return var_results

    except Exception as e:
        error_message = f"Error calculating portfolio VaR: {str(e)}"
        if log:
            log(error_message, "error")
        return {"error": error_message}


def calculate_component_var(
    strategy_returns: List[np.ndarray],
    allocation_weights: List[float],
    confidence_level: float = 0.95,
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, float]:
    """
    Calculate component VaR for each strategy in the portfolio.

    Component VaR measures how much each strategy contributes to the
    overall portfolio VaR, accounting for correlation effects.

    Args:
        strategy_returns: List of return series for each strategy
        allocation_weights: Allocation weights for each strategy
        confidence_level: Confidence level for VaR calculation
        log: Optional logging function

    Returns:
        Dictionary with component VaR for each strategy
    """
    try:
        if not strategy_returns or not allocation_weights:
            return {}

        n_strategies = len(strategy_returns)
        if len(allocation_weights) != n_strategies:
            raise ValueError(
                "Number of return series must match number of allocation weights"
            )

        # Calculate portfolio VaR first
        portfolio_var_result = calculate_portfolio_var_fixed(
            strategy_returns, allocation_weights, [confidence_level], "historical", log
        )

        confidence_pct = int(confidence_level * 100)
        portfolio_var = portfolio_var_result.get(f"var_{confidence_pct}", 0)

        if portfolio_var == 0:
            return {}

        # Calculate component VaR using marginal VaR approach
        component_vars = {}

        # Normalize weights
        total_allocation = sum(allocation_weights)
        normalized_weights = np.array(
            [w / total_allocation for w in allocation_weights]
        )

        # Find minimum length
        min_length = min(len(returns) for returns in strategy_returns)

        # Create aligned return matrix
        aligned_returns = np.zeros((min_length, n_strategies))
        for i, returns in enumerate(strategy_returns):
            aligned_returns[:, i] = returns[:min_length]

        # Calculate portfolio returns
        portfolio_returns = np.dot(aligned_returns, normalized_weights)

        # Calculate marginal VaR for each strategy
        alpha = 1 - confidence_level
        var_threshold = np.percentile(portfolio_returns, alpha * 100)

        # Find observations that exceed VaR
        var_exceedances_mask = portfolio_returns <= var_threshold

        for i in range(n_strategies):
            if np.sum(var_exceedances_mask) > 0:
                # Calculate marginal contribution to VaR
                strategy_returns_at_var = aligned_returns[var_exceedances_mask, i]
                marginal_var = (
                    float(np.mean(strategy_returns_at_var))
                    if len(strategy_returns_at_var) > 0
                    else 0
                )

                # Component VaR = weight * marginal VaR
                component_var = normalized_weights[i] * marginal_var
                component_vars[f"strategy_{i+1}_component_var_{confidence_pct}"] = (
                    component_var
                )

                if log:
                    log(
                        f"Strategy {i+
    1} component VaR {confidence_pct}%: {component_var:.4f}",
                        "info",
                    )
            else:
                component_vars[f"strategy_{i+1}_component_var_{confidence_pct}"] = 0.0

        # Verify that component VaRs sum approximately to portfolio VaR
        total_component_var = sum(component_vars.values())
        var_reconciliation = (
            abs(total_component_var - portfolio_var) / abs(portfolio_var)
            if portfolio_var != 0
            else 0
        )

        component_vars["portfolio_var"] = portfolio_var
        component_vars["total_component_var"] = total_component_var
        component_vars["var_reconciliation_error"] = var_reconciliation

        if log:
            log(
                f"VaR reconciliation: Portfolio={portfolio_var:.4f}, Components sum={total_component_var:.4f}, Error={var_reconciliation:.2%}",
                "info",
            )

        return component_vars

    except Exception as e:
        error_message = f"Error calculating component VaR: {str(e)}"
        if log:
            log(error_message, "error")
        return {"error": error_message}


def validate_risk_metrics(
    csv_data: pd.DataFrame,
    json_metrics: Dict[str, Any],
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """
    Validate risk metrics against CSV data to detect calculation issues.

    This function addresses the validation needs identified in Phase 1,
    particularly the MSTR 62.91% drawdown understatement issue.

    Args:
        csv_data: DataFrame with CSV backtest data
        json_metrics: Dictionary with JSON portfolio metrics
        log: Optional logging function

    Returns:
        Dictionary of validation results
    """
    if VALIDATION_AVAILABLE:
        validator = RiskMetricsValidator(strict_mode=True)
        return validator.validate_all_risk_metrics(csv_data, json_metrics, log)
    else:
        if log:
            log("Risk metrics validation not available", "warning")
        return {"validation_available": False}


def calculate_risk_contributions(
    position_arrays: List[np.ndarray],
    data_list: List[pl.DataFrame],
    strategy_allocations: List[float],
    log: Callable[[str, str], None],
    strategy_configs: List[Dict[str, Any]] = None,
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
    strategy_configs: List[Dict[str, Any]] = None,
) -> Dict[str, float]:
    """Legacy risk contribution calculation (deprecated).

    This function is kept for reference but should not be used.
    Use calculate_risk_contributions() instead.
    """
    try:
        if not position_arrays or not data_list or not strategy_allocations:
            log("Empty input arrays provided", "error")
            raise ValueError(
                "Position arrays, data list, and strategy allocations cannot be empty"
            )

        if len(position_arrays) != len(data_list) or len(position_arrays) != len(
            strategy_allocations
        ):
            log("Mismatched input arrays", "error")
            raise ValueError(
                "Number of position arrays, dataframes, and strategy allocations must match"
            )

        n_strategies = len(position_arrays)
        log(f"Calculating risk contributions for {n_strategies} strategies", "info")

        # Initialize risk contributions dictionary
        risk_contributions: Dict[str, float] = {}

        # Calculate returns and volatilities for each strategy
        log("Calculating strategy returns and volatilities", "info")
        volatilities = []
        strategy_returns = []
        all_active_returns = []  # Store all active returns for combined VaR/CVaR
        weighted_active_returns = []  # Store returns weighted by allocation
        for i, df in enumerate(data_list):
            # Get stop loss value if available
            stop_loss = None
            if strategy_configs and i < len(strategy_configs):
                stop_loss = strategy_configs[i].get("STOP_LOSS")
                if stop_loss is not None:
                    log(
                        f"Using stop loss of {stop_loss*100:.2f}% for strategy {i+1}",
                        "info",
                    )
            # Calculate returns from Close prices
            close_prices = df["Close"].to_numpy()
            returns = np.diff(close_prices) / close_prices[:-1]
            # Only consider periods where strategy was active
            active_positions = position_arrays[i][1:]  # Align with returns
            active_returns = returns[active_positions != 0]
            vol = float(np.std(active_returns)) if len(active_returns) > 0 else 0.0
            avg_return = (
                float(np.mean(active_returns)) if len(active_returns) > 0 else 0.0
            )
            volatilities.append(vol)
            strategy_returns.append(avg_return)

            # Collect active returns for combined calculations
            if len(active_returns) > 0:
                # Apply stop loss if available
                if stop_loss is not None and stop_loss > 0 and stop_loss < 1:
                    # Create signal array (1 for long, -1 for short)
                    signal_array = np.ones_like(active_returns)
                    if (
                        "DIRECTION" in strategy_configs[i]
                        and strategy_configs[i]["DIRECTION"] == "Short"
                    ):
                        signal_array = -1 * signal_array

                    # Apply stop loss to active returns
                    adjusted_returns, stop_loss_triggers = apply_stop_loss_to_returns(
                        active_returns, signal_array, stop_loss, log
                    )

                    # Log stop loss impact
                    trigger_count = int(np.sum(stop_loss_triggers))
                    if trigger_count > 0:
                        log(
                            f"Stop loss triggered {trigger_count} times for strategy {i+
    1}",
                            "info",
                        )

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
                var_95 = float(
                    np.percentile(sorted_returns, 5)
                )  # 5th percentile for 95% confidence
                var_99 = float(
                    np.percentile(sorted_returns, 1)
                )  # 1st percentile for 99% confidence

                # Calculate CVaR 95% and 99%
                cvar_95 = float(np.mean(sorted_returns[sorted_returns <= var_95]))
                cvar_99 = float(np.mean(sorted_returns[sorted_returns <= var_99]))

                risk_contributions[f"strategy_{i+1}_var_95"] = var_95
                risk_contributions[f"strategy_{i+1}_cvar_95"] = cvar_95
                risk_contributions[f"strategy_{i+1}_var_99"] = var_99
                risk_contributions[f"strategy_{i+1}_cvar_99"] = cvar_99

                log(
                    f"Strategy {i+1} - Volatility: {vol:.4f}, Average Return: {avg_return:.4f}",
                    "info",
                )
                log(
                    f"Strategy {i+1} - VaR 95%: {var_95:.4f}, CVaR 95%: {cvar_95:.4f}",
                    "info",
                )
                log(
                    f"Strategy {i+1} - VaR 99%: {var_99:.4f}, CVaR 99%: {cvar_99:.4f}",
                    "info",
                )
            else:
                risk_contributions[f"strategy_{i+1}_var_95"] = 0.0
                risk_contributions[f"strategy_{i+1}_cvar_95"] = 0.0
                risk_contributions[f"strategy_{i+1}_var_99"] = 0.0
                risk_contributions[f"strategy_{i+1}_cvar_99"] = 0.0
                log(
                    f"Strategy {i+1} - Volatility: {vol:.4f}, Average Return: {avg_return:.4f}",
                    "info",
                )
                log(
                    f"Strategy {i+1} - No active returns for VaR/CVaR calculation",
                    "info",
                )

        # Calculate combined VaR and CVaR metrics using allocation-weighted approach
        log("Calculating combined VaR and CVaR metrics", "info")
        if all_active_returns and strategy_allocations:
            # Calculate weighted average of individual VaR/CVaR values based on
            # allocations
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
                allocation_weight = (
                    strategy_allocations[i] / total_allocation
                    if total_allocation > 0
                    else 1.0 / n_strategies
                )

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

            log(
                f"Combined VaR 95% (allocation-weighted): {combined_var_95:.4f}, CVaR 95%: {combined_cvar_95:.4f}",
                "info",
            )
            log(
                f"Combined VaR 99% (allocation-weighted): {combined_var_99:.4f}, CVaR 99%: {combined_cvar_99:.4f}",
                "info",
            )
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
        min_length = float("inf")

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
            log(
                "Warning: NaN values detected in covariance matrix, using identity matrix",
                "warning",
            )
            # Use a small identity matrix as fallback
            covariance_matrix = np.eye(len(strategy_allocations)) * 0.0001

        # Handle NaN values in covariance matrix (can occur with zero variance)
        if np.isnan(covariance_matrix).any():
            log(
                "Warning: NaN values detected in covariance matrix, replacing with zeros",
                "warning",
            )
            covariance_matrix = np.nan_to_num(covariance_matrix, nan=0.0)

        # Calculate portfolio risk using proper portfolio theory: σ_p² = w^T Σ w
        total_allocation = sum(strategy_allocations)

        # Create weight vector - use equal weights if no allocations provided
        if total_allocation > 0:
            weights = np.array(
                [alloc / total_allocation for alloc in strategy_allocations]
            )
            log(f"Using provided allocations (total: {total_allocation:.2f}%)", "info")
        else:
            weights = np.ones(len(strategy_allocations)) / len(strategy_allocations)
            log(
                f"No allocations provided, using equal weights ({100/len(strategy_allocations):.2f}% each)",
                "info",
            )

        # Calculate portfolio variance: w^T * Σ * w
        portfolio_variance = np.dot(weights, np.dot(covariance_matrix, weights))
        log(f"Portfolio variance calculated: {portfolio_variance:.8f}", "info")

        # Handle NaN and negative values in portfolio variance
        if np.isnan(portfolio_variance) or portfolio_variance < 0:
            log(
                f"Warning: Invalid portfolio variance ({portfolio_variance}), setting to 0",
                "warning",
            )
            portfolio_variance = 0.0
            portfolio_risk = 0.0
        elif portfolio_variance > 0:
            portfolio_risk = np.sqrt(portfolio_variance)
            # Additional safety check for NaN in portfolio_risk
            if np.isnan(portfolio_risk):
                log(
                    "Warning: NaN detected in portfolio risk calculation, setting to 0",
                    "warning",
                )
                portfolio_risk = 0.0
        else:
            portfolio_risk = 0.0

        log(
            f"Portfolio risk calculated (allocation-weighted): {portfolio_risk:.4f}",
            "info",
        )

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
                    log(
                        f"Warning: NaN detected in risk contribution for strategy {i+1}, setting to 0",
                        "warning",
                    )
                    risk_contrib = 0.0

                risk_contributions[f"strategy_{i+1}_risk_contrib"] = float(risk_contrib)
                log(f"Strategy {i+1} risk contribution: {risk_contrib:.4f}", "info")

                # Calculate Risk-Adjusted Alpha (excess return over benchmark, adjusted
                # for volatility)
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
                    log(
                        f"Warning: NaN detected in alpha for strategy {i+1}, setting to 0",
                        "warning",
                    )
                    risk_adjusted_alpha = 0.0

                risk_contributions[f"strategy_{i+1}_alpha_to_portfolio"] = float(
                    risk_adjusted_alpha
                )
                log(
                    f"Strategy {i+
    1} excess return: {excess_return:.6f}, volatility: {strategy_volatility:.6f}",
                    "info",
                )
                log(
                    f"Strategy {i+
    1} risk-adjusted alpha to portfolio: {risk_adjusted_alpha:.6f}",
                    "info",
                )

                # Calculate pairwise risk overlaps
                for j in range(i + 1, n_strategies):
                    if portfolio_variance > 0:
                        # Risk overlap: w_i * w_j * σ_ij / portfolio_variance
                        overlap = float(
                            (weights[i] * weights[j] * covariance_matrix[i, j])
                            / portfolio_variance
                        )
                    else:
                        overlap = 0.0

                    # Handle potential NaN values
                    if np.isnan(overlap):
                        log(
                            f"Warning: NaN detected in risk overlap between strategy {i+
    1} and {j+
        1}, setting to 0",
                            "warning",
                        )
                        overlap = 0.0

                    risk_contributions[f"risk_overlap_{i+1}_{j+1}"] = overlap
                    log(
                        f"Risk overlap between strategy {i+1} and {j+1}: {overlap:.4f}",
                        "info",
                    )
        else:
            # Set default values when portfolio risk is 0
            log("Portfolio risk is 0, setting default risk contributions", "info")
            for i in range(n_strategies):
                risk_contributions[f"strategy_{i+1}_risk_contrib"] = 0.0
                risk_contributions[f"strategy_{i+1}_alpha_to_portfolio"] = 0.0

                # Also set default pairwise risk overlaps
                for j in range(i + 1, n_strategies):
                    risk_contributions[f"risk_overlap_{i+1}_{j+1}"] = 0.0

        risk_contributions["total_portfolio_risk"] = portfolio_risk
        risk_contributions["benchmark_return"] = float(benchmark_return)

        log("Risk contribution calculations completed successfully", "info")
        return risk_contributions

    except Exception as e:
        log(f"Error calculating risk contributions: {str(e)}", "error")
        raise
