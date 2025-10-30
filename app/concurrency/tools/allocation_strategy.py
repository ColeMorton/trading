"""
Allocation Strategy Module.

This module provides different strategies for allocating capital across
multiple trading strategies, improving on the default signal-count-based weighting.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any

import numpy as np


class AllocationMode(Enum):
    """Enumeration of allocation modes."""

    EQUAL = "equal"  # Equal allocation to all strategies
    SIGNAL_COUNT = "signal_count"  # Allocation based on signal count (default)
    PERFORMANCE = "performance"  # Allocation based on historical performance
    RISK_ADJUSTED = "risk_adjusted"  # Allocation based on risk-adjusted metrics
    INVERSE_VOLATILITY = "inverse_volatility"  # Allocation based on inverse volatility
    CUSTOM = "custom"  # Custom allocation specified by user


def calculate_allocations(
    strategy_metrics: list[dict[str, Any]],
    mode: AllocationMode = AllocationMode.SIGNAL_COUNT,
    custom_allocations: dict[str, float] | None = None,
    performance_metric: str = "sharpe_ratio",
    log: Callable[[str, str], None] | None = None,
) -> dict[str, float]:
    """Calculate strategy allocations based on the specified mode.

    Args:
        strategy_metrics: List of strategy metrics dictionaries
        mode: Allocation mode
        custom_allocations: Custom allocations (only used with CUSTOM mode)
        performance_metric: Metric to use for performance-based allocation
        log: Optional logging function

    Returns:
        Dict[str, float]: Dictionary mapping strategy IDs to allocation weights
    """
    if not strategy_metrics:
        if log:
            log("No strategy metrics provided for allocation calculation", "error")
        return {}

    # Extract strategy IDs
    strategy_ids = [
        metrics.get("strategy_id", f"strategy_{i + 1}")
        for i, metrics in enumerate(strategy_metrics)
    ]

    # Initialize allocations
    allocations = dict.fromkeys(strategy_ids, 0.0)

    if mode == AllocationMode.EQUAL:
        # Equal allocation to all strategies
        equal_weight = 1.0 / len(strategy_ids)
        allocations = dict.fromkeys(strategy_ids, equal_weight)

    elif mode == AllocationMode.SIGNAL_COUNT:
        # Allocation based on signal count
        signal_counts = [metrics.get("signal_count", 0) for metrics in strategy_metrics]
        total_signals = sum(signal_counts)

        if total_signals > 0:
            for i, strategy_id in enumerate(strategy_ids):
                allocations[strategy_id] = signal_counts[i] / total_signals
        else:
            # Fallback to equal allocation if no signals
            equal_weight = 1.0 / len(strategy_ids)
            allocations = dict.fromkeys(strategy_ids, equal_weight)

    elif mode == AllocationMode.PERFORMANCE:
        # Allocation based on historical performance
        performance_values = []

        for metrics in strategy_metrics:
            # Get the specified performance metric, defaulting to 0
            value = metrics.get(performance_metric, 0)

            # Handle negative values (can't allocate negative weight)
            value = max(value, 0)

            performance_values.append(value)

        total_performance = sum(performance_values)

        if total_performance > 0:
            for i, strategy_id in enumerate(strategy_ids):
                allocations[strategy_id] = performance_values[i] / total_performance
        else:
            # Fallback to equal allocation if total performance is zero or negative
            equal_weight = 1.0 / len(strategy_ids)
            allocations = dict.fromkeys(strategy_ids, equal_weight)

    elif mode == AllocationMode.RISK_ADJUSTED:
        # Allocation based on risk-adjusted metrics
        # This combines multiple factors: performance, risk, and correlation

        # Extract metrics
        sharpe_ratios = [metrics.get("sharpe_ratio", 0) for metrics in strategy_metrics]
        max_drawdowns = [
            metrics.get("max_drawdown", 1.0) for metrics in strategy_metrics
        ]
        win_rates = [metrics.get("win_rate", 0.5) for metrics in strategy_metrics]

        # Calculate risk-adjusted scores
        risk_adjusted_scores = []

        for i in range(len(strategy_ids)):
            # Ensure max_drawdown is not zero to avoid division by zero
            drawdown = max(max_drawdowns[i], 0.01)

            # Calculate score: sharpe * win_rate / drawdown
            # Higher sharpe and win_rate increase score, higher drawdown decreases score
            score = sharpe_ratios[i] * win_rates[i] / drawdown

            # Ensure score is not negative
            score = max(score, 0)

            risk_adjusted_scores.append(score)

        total_score = sum(risk_adjusted_scores)

        if total_score > 0:
            for i, strategy_id in enumerate(strategy_ids):
                allocations[strategy_id] = risk_adjusted_scores[i] / total_score
        else:
            # Fallback to equal allocation if total score is zero
            equal_weight = 1.0 / len(strategy_ids)
            allocations = dict.fromkeys(strategy_ids, equal_weight)

    elif mode == AllocationMode.INVERSE_VOLATILITY:
        # Allocation based on inverse volatility
        # Lower volatility strategies get higher allocation

        # Extract volatility metrics
        volatilities = []

        for metrics in strategy_metrics:
            # Get volatility, with fallback options
            vol = metrics.get("volatility", None)
            if vol is None:
                # Try standard deviation of returns
                vol = metrics.get("return_std", None)
            if vol is None:
                # If still None, use max_drawdown as a proxy
                vol = metrics.get("max_drawdown", 0.1)

            # Ensure volatility is positive
            vol = max(vol, 0.001)

            volatilities.append(vol)

        # Calculate inverse volatilities
        inverse_vols = [1.0 / vol for vol in volatilities]
        total_inverse_vol = sum(inverse_vols)

        if total_inverse_vol > 0:
            for i, strategy_id in enumerate(strategy_ids):
                allocations[strategy_id] = inverse_vols[i] / total_inverse_vol
        else:
            # Fallback to equal allocation
            equal_weight = 1.0 / len(strategy_ids)
            allocations = dict.fromkeys(strategy_ids, equal_weight)

    elif mode == AllocationMode.CUSTOM:
        # Custom allocation specified by user
        if custom_allocations:
            # Validate custom allocations
            valid_allocations = {}
            total_allocation = 0.0

            for strategy_id, allocation in custom_allocations.items():
                if strategy_id in strategy_ids and allocation >= 0:
                    valid_allocations[strategy_id] = allocation
                    total_allocation += allocation

            # Normalize allocations if total is not 1.0
            if total_allocation > 0:
                for strategy_id, allocation in valid_allocations.items():
                    allocations[strategy_id] = allocation / total_allocation
            else:
                # Fallback to equal allocation if total is zero
                equal_weight = 1.0 / len(strategy_ids)
                allocations = dict.fromkeys(strategy_ids, equal_weight)
        else:
            # No custom allocations provided, fallback to equal
            if log:
                log("No custom allocations provided, using equal allocation", "warning")
            equal_weight = 1.0 / len(strategy_ids)
            allocations = dict.fromkeys(strategy_ids, equal_weight)

    else:
        # Invalid mode, fallback to equal allocation
        if log:
            log(f"Invalid allocation mode: {mode}. Using equal allocation.", "warning")
        equal_weight = 1.0 / len(strategy_ids)
        allocations = dict.fromkeys(strategy_ids, equal_weight)

    # Ensure allocations sum to 1.0 (handle floating point precision issues)
    total = sum(allocations.values())
    if total > 0:
        for strategy_id in allocations:
            allocations[strategy_id] /= total

    if log:
        log(f"Calculated allocations using {mode.value} mode", "info")

    return allocations


def get_allocation_mode(config: dict[str, Any]) -> AllocationMode:
    """Get the allocation mode from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        AllocationMode: Allocation mode
    """
    mode_str = config.get("ALLOCATION_MODE", "signal_count")

    try:
        return AllocationMode(mode_str)
    except ValueError:
        # Invalid mode, return default
        return AllocationMode.SIGNAL_COUNT


def analyze_allocation_impact(
    strategy_metrics: list[dict[str, Any]],
    returns: np.ndarray,
    log: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    """Analyze the impact of different allocation modes on portfolio performance.

    Args:
        strategy_metrics: List of strategy metrics dictionaries
        returns: Array of returns for each strategy
        log: Optional logging function

    Returns:
        Dict[str, Any]: Dictionary with impact analysis
    """
    if not strategy_metrics or len(strategy_metrics) != len(returns):
        if log:
            log("Invalid inputs for allocation impact analysis", "error")
        return {}

    results = {}

    # Test different allocation modes
    for mode in AllocationMode:
        # Skip custom mode as it requires user input
        if mode == AllocationMode.CUSTOM:
            continue

        # Calculate allocations
        allocations = calculate_allocations(strategy_metrics, mode)

        # Apply allocations to returns
        weighted_returns = np.zeros(returns.shape[1])

        for i, strategy_id in enumerate(allocations.keys()):
            if i < returns.shape[0]:
                weighted_returns += returns[i] * allocations[strategy_id]

        # Calculate performance metrics
        avg_return = float(np.mean(weighted_returns))
        win_rate = float(np.mean(weighted_returns > 0))

        # Calculate profit factor
        positive_returns = weighted_returns[weighted_returns > 0]
        negative_returns = weighted_returns[weighted_returns < 0]

        profit_factor = 1.0
        if len(negative_returns) > 0 and np.sum(np.abs(negative_returns)) > 0:
            profit_factor = float(
                np.sum(positive_returns) / np.sum(np.abs(negative_returns)),
            )

        # Calculate max drawdown
        cumulative_returns = np.cumsum(weighted_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = running_max - cumulative_returns
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        results[mode.value] = {
            "avg_return": avg_return,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "allocations": allocations,
        }

    # Calculate impact relative to default (signal_count)
    if "signal_count" in results:
        baseline = results["signal_count"]

        for mode, metrics in results.items():
            if mode != "signal_count":
                impact = {
                    "avg_return_impact": metrics["avg_return"] - baseline["avg_return"],
                    "win_rate_impact": metrics["win_rate"] - baseline["win_rate"],
                    "profit_factor_impact": metrics["profit_factor"]
                    - baseline["profit_factor"],
                    "max_drawdown_impact": metrics["max_drawdown"]
                    - baseline["max_drawdown"],
                }
                results[mode]["impact"] = impact

    if log:
        log(f"Analyzed allocation impact across {len(results)} modes", "info")

    return results
