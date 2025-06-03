"""
Stop Loss Simulator Module.

This module provides functionality for simulating the effects of stop losses
on signal returns and adjusting signal quality metrics accordingly.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import polars as pl

from app.tools.setup_logging import setup_logging


def apply_stop_loss_to_returns(
    returns: np.ndarray,
    signals: np.ndarray,
    stop_loss: float,
    log: Optional[Callable[[str, str], None]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Apply stop loss to returns based on signals.

    This function simulates the effect of a stop loss on returns by truncating
    negative returns when they exceed the stop loss threshold.

    Args:
        returns (np.ndarray): Array of returns
        signals (np.ndarray): Array of signals (1 for long, -1 for short, 0 for no position)
        stop_loss (float): Stop loss as a decimal (e.g., 0.05 for 5%)
        log (Optional[Callable]): Logging function

    Returns:
        Tuple[np.ndarray, np.ndarray]: Tuple of (adjusted returns, stop loss triggers)
    """
    if log is None:
        # Create a default logger if none provided
        log, _, _, _ = setup_logging(
            "stop_loss_simulator", Path("./logs"), "stop_loss_simulator.log"
        )

    # Validate inputs
    if stop_loss <= 0 or stop_loss >= 1:
        log(f"Invalid stop loss value: {stop_loss}. Must be between 0 and 1.", "error")
        return returns, np.zeros_like(returns)

    # Create a copy of returns to avoid modifying the original
    adjusted_returns = returns.copy()

    # Create an array to track stop loss triggers
    stop_loss_triggers = np.zeros_like(returns)

    # Create a position array from signals
    # A position at time t is determined by the signal at time t-1
    positions = np.zeros_like(signals)
    for i in range(1, len(signals)):
        if signals[i - 1] != 0:
            positions[i] = signals[i - 1]
        elif positions[i - 1] != 0 and signals[i - 1] == 0:
            # Maintain position if no new signal
            positions[i] = positions[i - 1]

    # Log the positions for debugging
    log(f"Positions: {positions}", "debug")

    # Create arrays to track position-specific data
    position_ids = np.zeros_like(signals)  # Unique ID for each position
    current_position_id = 0
    position_cumulative_returns = (
        {}
    )  # Dictionary to track cumulative returns by position ID

    # Assign position IDs and initialize tracking
    for i in range(len(positions)):
        if i > 0 and positions[i] != 0:
            if positions[i - 1] == 0 or positions[i] != positions[i - 1]:
                # New position started
                current_position_id += 1
                position_cumulative_returns[current_position_id] = 0.0

            # Assign position ID
            position_ids[i] = current_position_id

    # Process each time step
    for i in range(len(returns)):
        # Skip if no position
        if positions[i] == 0:
            continue

        # Get position ID
        pos_id = position_ids[i]
        if pos_id == 0:
            continue

        # Calculate return based on position direction
        if positions[i] > 0:  # Long position
            position_return = returns[i]
        else:  # Short position
            position_return = -returns[i]

        # Update cumulative return for this position
        position_cumulative_returns[pos_id] += position_return

        # Log for debugging
        log(
            f"Position {pos_id} at index {i}: cumulative return = {position_cumulative_returns[pos_id]}",
            "debug",
        )

        # Check if stop loss is triggered
        if position_cumulative_returns[pos_id] <= -stop_loss:
            # Stop loss triggered
            stop_loss_triggers[i] = 1

            # Adjust return to stop loss level
            # The adjusted return is the difference between the stop loss
            # and the cumulative return before this time step
            previous_cumulative = position_cumulative_returns[pos_id] - position_return
            adjustment = -stop_loss - previous_cumulative

            log(
                f"Stop loss triggered at index {i}. Previous cumulative: {previous_cumulative}, Adjustment: {adjustment}",
                "debug",
            )

            if positions[i] > 0:  # Long position
                adjusted_returns[i] = adjustment
            else:  # Short position
                adjusted_returns[i] = -adjustment

            # Reset position tracking
            position_cumulative_returns[pos_id] = 0.0

            # Force position to close by setting subsequent positions to 0
            # until a new signal is encountered
            for j in range(i + 1, len(positions)):
                if position_ids[j] == pos_id:
                    positions[j] = 0
                    position_ids[j] = 0
                else:
                    break

    log(
        f"Applied stop loss of {stop_loss*100:.2f}% to returns. "
        + f"Triggered {int(np.sum(stop_loss_triggers))} times.",
        "info",
    )

    return adjusted_returns, stop_loss_triggers


def calculate_stop_loss_adjusted_metrics(
    returns: np.ndarray,
    signals: np.ndarray,
    stop_loss: float,
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """Calculate metrics adjusted for stop loss effects.

    Args:
        returns (np.ndarray): Array of returns
        signals (np.ndarray): Array of signals
        stop_loss (float): Stop loss as a decimal
        log (Optional[Callable]): Logging function

    Returns:
        Dict[str, Any]: Dictionary of stop loss adjusted metrics
    """
    if log is None:
        # Create a default logger if none provided
        log, _, _, _ = setup_logging(
            "stop_loss_simulator", Path("./logs"), "stop_loss_simulator.log"
        )

    # Apply stop loss to returns
    adjusted_returns, stop_loss_triggers = apply_stop_loss_to_returns(
        returns, signals, stop_loss, log
    )

    # Calculate metrics on adjusted returns
    # Only consider returns when signals are active
    signal_returns = returns[signals != 0]
    adjusted_signal_returns = adjusted_returns[signals != 0]

    # Basic return metrics
    avg_return = float(np.mean(signal_returns))
    adjusted_avg_return = float(np.mean(adjusted_signal_returns))

    win_rate = float(np.mean(signal_returns > 0))
    adjusted_win_rate = float(np.mean(adjusted_signal_returns > 0))

    # Profit factor
    positive_returns = signal_returns[signal_returns > 0]
    negative_returns = signal_returns[signal_returns < 0]

    adjusted_positive_returns = adjusted_signal_returns[adjusted_signal_returns > 0]
    adjusted_negative_returns = adjusted_signal_returns[adjusted_signal_returns < 0]

    profit_factor = 1.0
    if len(negative_returns) > 0 and np.sum(np.abs(negative_returns)) > 0:
        profit_factor = float(
            np.sum(positive_returns) / np.sum(np.abs(negative_returns))
        )

    adjusted_profit_factor = 1.0
    if (
        len(adjusted_negative_returns) > 0
        and np.sum(np.abs(adjusted_negative_returns)) > 0
    ):
        adjusted_profit_factor = float(
            np.sum(adjusted_positive_returns)
            / np.sum(np.abs(adjusted_negative_returns))
        )

    # Average win and loss
    avg_win = float(np.mean(positive_returns)) if len(positive_returns) > 0 else 0.0
    avg_loss = float(np.mean(negative_returns)) if len(negative_returns) > 0 else 0.0

    adjusted_avg_win = (
        float(np.mean(adjusted_positive_returns))
        if len(adjusted_positive_returns) > 0
        else 0.0
    )
    adjusted_avg_loss = (
        float(np.mean(adjusted_negative_returns))
        if len(adjusted_negative_returns) > 0
        else 0.0
    )

    # Risk-reward ratio
    risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")
    adjusted_risk_reward_ratio = (
        abs(adjusted_avg_win / adjusted_avg_loss)
        if adjusted_avg_loss != 0
        else float("inf")
    )

    # Maximum drawdown
    cumulative_returns = np.cumsum(signal_returns)
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdowns = running_max - cumulative_returns
    max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    adjusted_cumulative_returns = np.cumsum(adjusted_signal_returns)
    adjusted_running_max = np.maximum.accumulate(adjusted_cumulative_returns)
    adjusted_drawdowns = adjusted_running_max - adjusted_cumulative_returns
    adjusted_max_drawdown = (
        float(np.max(adjusted_drawdowns)) if len(adjusted_drawdowns) > 0 else 0.0
    )

    # Stop loss impact metrics
    stop_loss_count = int(np.sum(stop_loss_triggers))
    stop_loss_rate = (
        float(stop_loss_count / len(signal_returns)) if len(signal_returns) > 0 else 0.0
    )

    # Return impact
    return_impact = adjusted_avg_return - avg_return
    return_impact_pct = (
        (return_impact / abs(avg_return)) * 100 if avg_return != 0 else 0.0
    )

    # Win rate impact
    win_rate_impact = adjusted_win_rate - win_rate
    win_rate_impact_pct = (win_rate_impact / win_rate) * 100 if win_rate > 0 else 0.0

    # Drawdown impact
    drawdown_impact = adjusted_max_drawdown - max_drawdown
    drawdown_impact_pct = (
        (drawdown_impact / max_drawdown) * 100 if max_drawdown > 0 else 0.0
    )

    log(
        f"Calculated stop loss adjusted metrics with {stop_loss_count} stop loss triggers",
        "info",
    )

    return {
        # Raw metrics
        "raw_avg_return": avg_return,
        "raw_win_rate": win_rate,
        "raw_profit_factor": profit_factor,
        "raw_avg_win": avg_win,
        "raw_avg_loss": avg_loss,
        "raw_risk_reward_ratio": risk_reward_ratio,
        "raw_max_drawdown": max_drawdown,
        # Adjusted metrics
        "adjusted_avg_return": adjusted_avg_return,
        "adjusted_win_rate": adjusted_win_rate,
        "adjusted_profit_factor": adjusted_profit_factor,
        "adjusted_avg_win": adjusted_avg_win,
        "adjusted_avg_loss": adjusted_avg_loss,
        "adjusted_risk_reward_ratio": adjusted_risk_reward_ratio,
        "adjusted_max_drawdown": adjusted_max_drawdown,
        # Impact metrics
        "stop_loss_count": stop_loss_count,
        "stop_loss_rate": stop_loss_rate,
        "return_impact": return_impact,
        "return_impact_pct": return_impact_pct,
        "win_rate_impact": win_rate_impact,
        "win_rate_impact_pct": win_rate_impact_pct,
        "drawdown_impact": drawdown_impact,
        "drawdown_impact_pct": drawdown_impact_pct,
        # Stop loss value
        "stop_loss": stop_loss,
    }


def compare_stop_loss_levels(
    returns: np.ndarray,
    signals: np.ndarray,
    stop_loss_levels: List[float],
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Compare different stop loss levels.

    Args:
        returns (np.ndarray): Array of returns
        signals (np.ndarray): Array of signals
        stop_loss_levels (List[float]): List of stop loss levels to compare
        log (Optional[Callable]): Logging function

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of metrics for each stop loss level
    """
    if log is None:
        # Create a default logger if none provided
        log, _, _, _ = setup_logging(
            "stop_loss_simulator", Path("./logs"), "stop_loss_simulator.log"
        )

    results = {}

    # Calculate metrics for each stop loss level
    for stop_loss in stop_loss_levels:
        metrics = calculate_stop_loss_adjusted_metrics(returns, signals, stop_loss, log)

        results[f"stop_loss_{int(stop_loss*100)}pct"] = metrics

    # Calculate metrics without stop loss for comparison
    # Use a very large stop loss value that won't be triggered
    no_stop_loss_metrics = calculate_stop_loss_adjusted_metrics(
        returns, signals, 1.0, log
    )

    results["no_stop_loss"] = no_stop_loss_metrics

    log(f"Compared {len(stop_loss_levels)} stop loss levels", "info")

    return results


def find_optimal_stop_loss(
    returns: np.ndarray,
    signals: np.ndarray,
    stop_loss_range: Tuple[float, float] = (0.01, 0.20),
    step: float = 0.01,
    optimization_metric: str = "adjusted_avg_return",
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """Find the optimal stop loss level based on a specified metric.

    Args:
        returns (np.ndarray): Array of returns
        signals (np.ndarray): Array of signals
        stop_loss_range (Tuple[float, float]): Range of stop loss levels to test
        step (float): Step size for stop loss levels
        optimization_metric (str): Metric to optimize
        log (Optional[Callable]): Logging function

    Returns:
        Dict[str, Any]: Dictionary with optimal stop loss and metrics
    """
    if log is None:
        # Create a default logger if none provided
        log, _, _, _ = setup_logging(
            "stop_loss_simulator", Path("./logs"), "stop_loss_simulator.log"
        )

    # Generate stop loss levels
    start, end = stop_loss_range
    stop_loss_levels = np.arange(start, end + step, step)

    # Calculate metrics for each stop loss level
    results = {}
    best_value = -float("inf")
    best_stop_loss = None

    for stop_loss in stop_loss_levels:
        metrics = calculate_stop_loss_adjusted_metrics(returns, signals, stop_loss, log)

        # Store metrics
        results[stop_loss] = metrics

        # Check if this is the best stop loss
        if optimization_metric in metrics:
            value = metrics[optimization_metric]

            # For drawdown metrics, lower is better
            if "drawdown" in optimization_metric:
                value = -value

            if value > best_value:
                best_value = value
                best_stop_loss = stop_loss

    if best_stop_loss is None:
        log(
            f"Could not find optimal stop loss. Metric '{optimization_metric}' not found in results.",
            "error",
        )
        return {
            "optimal_stop_loss": None,
            "optimal_metrics": {},
            "all_results": results,
        }

    log(
        f"Found optimal stop loss of {best_stop_loss*100:.2f}% based on {optimization_metric}",
        "info",
    )

    return {
        "optimal_stop_loss": best_stop_loss,
        "optimal_metrics": results[best_stop_loss],
        "all_results": results,
    }


def apply_stop_loss_to_signal_quality_metrics(
    metrics: Dict[str, Any],
    returns: np.ndarray,
    signals: np.ndarray,
    stop_loss: float,
    log: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """Apply stop loss effects to signal quality metrics.

    Args:
        metrics (Dict[str, Any]): Original signal quality metrics
        returns (np.ndarray): Array of returns
        signals (np.ndarray): Array of signals
        stop_loss (float): Stop loss as a decimal
        log (Optional[Callable]): Logging function

    Returns:
        Dict[str, Any]: Updated metrics with stop loss effects
    """
    if log is None:
        # Create a default logger if none provided
        log, _, _, _ = setup_logging(
            "stop_loss_simulator", Path("./logs"), "stop_loss_simulator.log"
        )

    # Calculate stop loss adjusted metrics
    stop_loss_metrics = calculate_stop_loss_adjusted_metrics(
        returns, signals, stop_loss, log
    )

    # Create a copy of the original metrics
    updated_metrics = metrics.copy()

    # Update metrics with stop loss adjusted values
    updated_metrics["avg_return"] = stop_loss_metrics["adjusted_avg_return"]
    updated_metrics["win_rate"] = stop_loss_metrics["adjusted_win_rate"]
    updated_metrics["profit_factor"] = stop_loss_metrics["adjusted_profit_factor"]
    updated_metrics["avg_win"] = stop_loss_metrics["adjusted_avg_win"]
    updated_metrics["avg_loss"] = stop_loss_metrics["adjusted_avg_loss"]
    updated_metrics["risk_reward_ratio"] = stop_loss_metrics[
        "adjusted_risk_reward_ratio"
    ]
    updated_metrics["max_drawdown"] = stop_loss_metrics["adjusted_max_drawdown"]

    # Add stop loss specific metrics
    updated_metrics["stop_loss"] = stop_loss
    updated_metrics["stop_loss_count"] = stop_loss_metrics["stop_loss_count"]
    updated_metrics["stop_loss_rate"] = stop_loss_metrics["stop_loss_rate"]

    # Add raw vs. adjusted comparison
    updated_metrics["raw_vs_adjusted"] = {
        "avg_return": {
            "raw": stop_loss_metrics["raw_avg_return"],
            "adjusted": stop_loss_metrics["adjusted_avg_return"],
            "impact": stop_loss_metrics["return_impact"],
            "impact_pct": stop_loss_metrics["return_impact_pct"],
        },
        "win_rate": {
            "raw": stop_loss_metrics["raw_win_rate"],
            "adjusted": stop_loss_metrics["adjusted_win_rate"],
            "impact": stop_loss_metrics["win_rate_impact"],
            "impact_pct": stop_loss_metrics["win_rate_impact_pct"],
        },
        "max_drawdown": {
            "raw": stop_loss_metrics["raw_max_drawdown"],
            "adjusted": stop_loss_metrics["adjusted_max_drawdown"],
            "impact": stop_loss_metrics["drawdown_impact"],
            "impact_pct": stop_loss_metrics["drawdown_impact_pct"],
        },
    }
    # Recalculate expectancy with adjusted values
    from app.tools.expectancy import calculate_expectancy

    # Recalculate expectancy using the adjusted metrics
    expectancy = calculate_expectancy(
        stop_loss_metrics["adjusted_win_rate"],
        stop_loss_metrics["adjusted_avg_win"],
        abs(stop_loss_metrics["adjusted_avg_loss"]),
    )
    updated_metrics["expectancy_per_signal"] = expectancy

    log(f"Applied stop loss of {stop_loss*100:.2f}% to signal quality metrics", "info")

    return updated_metrics
