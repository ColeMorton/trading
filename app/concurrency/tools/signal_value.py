"""
Signal Value Metrics Module.

This module provides functions to calculate various signal value metrics
for trading strategies, helping to quantify the value of each signal.
"""

import os
from typing import Any, Callable, Dict, List

import numpy as np
import polars as pl

from .signal_processor import SignalDefinition, SignalProcessor

# Get configuration
USE_FIXED_SIGNAL_PROC = os.getenv("USE_FIXED_SIGNAL_PROC", "true").lower() == "true"


def calculate_signal_value_metrics(
    signals_df: pl.DataFrame,
    returns_df: pl.DataFrame,
    risk_metrics: Dict[str, Any],
    strategy_id: str,
    log: Callable[[str, str], None],
) -> Dict[str, Any]:
    """Calculate signal value metrics for a strategy.

    Args:
        signals_df (pl.DataFrame): DataFrame with Date and signal columns
        returns_df (pl.DataFrame): DataFrame with Date and return columns
        risk_metrics (Dict[str, Any]): Risk metrics for the strategy
        strategy_id (str): Strategy identifier
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, Any]: Dictionary with signal value metrics
    """
    try:
        # Ensure dataframes have required columns
        if "Date" not in signals_df.columns or "signal" not in signals_df.columns:
            log(f"Missing required columns in signals_df for {strategy_id}", "error")
            return {}

        if "Date" not in returns_df.columns or "return" not in returns_df.columns:
            log(f"Missing required columns in returns_df for {strategy_id}", "error")
            return {}

        # Join signals and returns on Date
        joined_df = signals_df.join(returns_df, on="Date", how="inner")

        # Extract signals and returns as numpy arrays
        signals_np = joined_df["signal"].fill_null(0).to_numpy()
        returns_np = joined_df["return"].fill_null(0).to_numpy()

        # Count signals using standardized processor
        if USE_FIXED_SIGNAL_PROC:
            signal_processor = SignalProcessor(use_fixed=True)
            signal_def = SignalDefinition(
                signal_column="signal",
                position_column="signal",  # Using signal column as position for this case
            )
            signal_counts = signal_processor.get_comprehensive_counts(
                joined_df, signal_def
            )
            signal_count = signal_counts.raw_signals
        else:
            # Legacy counting method
            signal_count = int(np.sum(signals_np != 0))

        if signal_count == 0:
            log(f"No signals found for {strategy_id}", "warning")
            return {"signal_risk_adjusted_value": 0.0, "signal_opportunity_score": 0.0}

        # Calculate signal returns (only when signal is active)
        signal_returns = returns_np[signals_np != 0]

        # Extract risk metrics
        var_95 = risk_metrics.get("var_95", -0.05)
        cvar_95 = risk_metrics.get("cvar_95", -0.07)
        risk_contribution = risk_metrics.get("risk_contribution", 0.5)

        # Calculate signal risk-adjusted value
        avg_return = float(np.mean(signal_returns))
        return_volatility = float(np.std(signal_returns))

        # Avoid division by zero
        if return_volatility == 0:
            return_volatility = 0.001

        # Signal risk-adjusted value (return per unit of risk)
        signal_risk_adjusted_value = avg_return / abs(return_volatility)

        # Signal contribution ratio (how much each signal contributes to overall performance)
        # This is calculated as the average return per signal divided by the total number of signals
        total_return = np.sum(signal_returns)
        signal_contribution_ratio = (
            total_return / signal_count if signal_count > 0 else 0.0
        )

        # Signal efficiency ratio (how efficiently signals capture available market movements)
        # For simplicity, we'll use the win rate as a proxy for efficiency
        win_rate = float(np.mean(signal_returns > 0))
        signal_efficiency_ratio = win_rate

        # Signal risk contribution (how much each signal contributes to portfolio risk)
        # We'll use the risk_contribution from the risk metrics, normalized per signal
        signal_risk_contribution = (
            risk_contribution / signal_count if signal_count > 0 else 0.0
        )

        # Signal tail risk exposure (exposure to tail risk events per signal)
        # We'll use the CVaR (Conditional Value at Risk) as a measure of tail risk
        signal_tail_risk_exposure = (
            abs(cvar_95) / signal_count if signal_count > 0 else 0.0
        )

        # Signal consistency score (consistency of signal performance over time)
        # Lower standard deviation of returns indicates more consistent performance
        signal_consistency_score = 1.0 / (1.0 + return_volatility)

        # Signal information ratio (excess return per unit of risk)
        # For simplicity, we'll use 0 as the risk-free rate
        signal_information_ratio = (
            avg_return / abs(return_volatility) if return_volatility > 0 else 0.0
        )

        # Signal market impact (estimate of market impact cost per signal)
        # This is a simplified model - in reality, market impact depends on many factors
        # We'll use a simple model based on signal size and volatility
        avg_signal_size = float(np.mean(np.abs(signals_np[signals_np != 0])))
        signal_market_impact = (
            avg_signal_size * return_volatility * 0.1
        )  # 10% of volatility as impact

        # Signal opportunity score (composite score of signal value)
        # This is a weighted combination of the above metrics
        signal_opportunity_score = _calculate_opportunity_score(
            signal_risk_adjusted_value,
            signal_contribution_ratio,
            signal_efficiency_ratio,
            signal_risk_contribution,
            signal_tail_risk_exposure,
            signal_consistency_score,
            signal_information_ratio,
            signal_market_impact,
        )

        # Signal expected value (expected monetary value of each signal)
        # This is the average return per signal, adjusted for risk
        signal_expected_value = avg_return * (1.0 - abs(var_95))

        log(
            f"Calculated signal value metrics for {strategy_id}: opportunity_score={signal_opportunity_score:.2f}",
            "info",
        )

        return {
            "signal_risk_adjusted_value": signal_risk_adjusted_value,
            "signal_contribution_ratio": signal_contribution_ratio,
            "signal_efficiency_ratio": signal_efficiency_ratio,
            "signal_risk_contribution": signal_risk_contribution,
            "signal_tail_risk_exposure": signal_tail_risk_exposure,
            "signal_consistency_score": signal_consistency_score,
            "signal_information_ratio": signal_information_ratio,
            "signal_market_impact": signal_market_impact,
            "signal_opportunity_score": signal_opportunity_score,
            "signal_expected_value": signal_expected_value,
        }
    except Exception as e:
        log(
            f"Error calculating signal value metrics for {strategy_id}: {str(e)}",
            "error",
        )
        return {}


def _calculate_opportunity_score(
    risk_adjusted_value: float,
    contribution_ratio: float,
    efficiency_ratio: float,
    risk_contribution: float,
    tail_risk_exposure: float,
    consistency_score: float,
    information_ratio: float,
    market_impact: float,
) -> float:
    """Calculate a composite opportunity score for signal value.

    Args:
        risk_adjusted_value (float): Signal risk-adjusted value
        contribution_ratio (float): Signal contribution ratio
        efficiency_ratio (float): Signal efficiency ratio
        risk_contribution (float): Signal risk contribution
        tail_risk_exposure (float): Signal tail risk exposure
        consistency_score (float): Signal consistency score
        information_ratio (float): Signal information ratio
        market_impact (float): Signal market impact

    Returns:
        float: Signal opportunity score (0-10 scale)
    """
    # Normalize metrics to 0-1 scale
    norm_risk_adjusted_value = min(max(risk_adjusted_value, 0), 3.0) / 3.0
    norm_information_ratio = min(max(information_ratio, 0), 3.0) / 3.0

    # For risk metrics, lower is better, so we invert them
    norm_risk_contribution = 1.0 - min(risk_contribution, 1.0)
    norm_tail_risk_exposure = 1.0 - min(tail_risk_exposure, 1.0)
    norm_market_impact = 1.0 - min(market_impact, 1.0)

    # Weights for each component
    weights = {
        "risk_adjusted_value": 0.20,
        "contribution_ratio": 0.10,
        "efficiency_ratio": 0.15,
        "risk_contribution": 0.10,
        "tail_risk_exposure": 0.10,
        "consistency_score": 0.15,
        "information_ratio": 0.15,
        "market_impact": 0.05,
    }

    # Calculate weighted score (0-10 scale)
    score = 10.0 * (
        weights["risk_adjusted_value"] * norm_risk_adjusted_value
        + weights["contribution_ratio"] * contribution_ratio
        + weights["efficiency_ratio"] * efficiency_ratio
        + weights["risk_contribution"] * norm_risk_contribution
        + weights["tail_risk_exposure"] * norm_tail_risk_exposure
        + weights["consistency_score"] * consistency_score
        + weights["information_ratio"] * norm_information_ratio
        + weights["market_impact"] * norm_market_impact
    )

    return float(score)


def integrate_signal_value_metrics(
    signals_df_list: List[pl.DataFrame],
    returns_df_list: List[pl.DataFrame],
    risk_metrics: Dict[str, Dict[str, float]],
    log: Callable[[str, str], None],
) -> Dict[str, Dict[str, float]]:
    """Calculate and integrate signal value metrics for all strategies.

    Args:
        signals_df_list (List[pl.DataFrame]): List of signal dataframes
        returns_df_list (List[pl.DataFrame]): List of return dataframes
        risk_metrics (Dict[str, Dict[str, float]]): Risk metrics for all strategies
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, Dict[str, float]]: Signal value metrics for all strategies
    """
    try:
        log("Calculating signal value metrics for all strategies", "info")

        # Initialize results dictionary
        results = {}

        # Calculate metrics for each strategy
        for i, (signals_df, returns_df) in enumerate(
            zip(signals_df_list, returns_df_list)
        ):
            strategy_id = f"strategy_{i+1}"

            # Get risk metrics for this strategy
            strategy_risk_metrics = risk_metrics.get(strategy_id, {})

            # Calculate signal value metrics
            metrics = calculate_signal_value_metrics(
                signals_df=signals_df,
                returns_df=returns_df,
                risk_metrics=strategy_risk_metrics,
                strategy_id=strategy_id,
                log=log,
            )

            # Store results
            results[strategy_id] = metrics

        # Calculate aggregate metrics
        aggregate_metrics = _calculate_aggregate_signal_value_metrics(results, log)
        results["aggregate"] = aggregate_metrics

        log(f"Calculated signal value metrics for {len(results)-1} strategies", "info")

        return results
    except Exception as e:
        log(f"Error integrating signal value metrics: {str(e)}", "error")
        return {}


def _calculate_aggregate_signal_value_metrics(
    strategy_metrics: Dict[str, Dict[str, float]], log: Callable[[str, str], None]
) -> Dict[str, float]:
    """Calculate aggregate signal value metrics across all strategies.

    Args:
        strategy_metrics (Dict[str, Dict[str, float]]): Signal value metrics for all strategies
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, float]: Aggregate signal value metrics
    """
    try:
        # Initialize aggregate metrics
        aggregate_metrics = {
            "signal_risk_adjusted_value": 0.0,
            "signal_contribution_ratio": 0.0,
            "signal_efficiency_ratio": 0.0,
            "signal_risk_contribution": 0.0,
            "signal_tail_risk_exposure": 0.0,
            "signal_consistency_score": 0.0,
            "signal_information_ratio": 0.0,
            "signal_market_impact": 0.0,
            "signal_opportunity_score": 0.0,
            "signal_expected_value": 0.0,
        }

        # Count strategies with valid metrics
        valid_strategies = 0

        # Sum metrics across all strategies
        for strategy_id, metrics in strategy_metrics.items():
            if not metrics:
                continue

            valid_strategies += 1

            for metric_name in aggregate_metrics.keys():
                if metric_name in metrics:
                    aggregate_metrics[metric_name] += metrics[metric_name]

        # Calculate averages
        if valid_strategies > 0:
            for metric_name in aggregate_metrics.keys():
                aggregate_metrics[metric_name] /= valid_strategies

        log(
            f"Calculated aggregate signal value metrics across {valid_strategies} strategies",
            "info",
        )

        return aggregate_metrics
    except Exception as e:
        log(f"Error calculating aggregate signal value metrics: {str(e)}", "error")
        return {"signal_opportunity_score": 0.0, "error": str(e)}
