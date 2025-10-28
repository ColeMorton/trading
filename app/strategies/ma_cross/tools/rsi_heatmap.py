"""
RSI Heatmap Module

This module contains functions for analyzing RSI parameter sensitivity.
"""

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from app.strategies.ma_cross.tools.rsi_utils import (
    apply_rsi_mask,
    calculate_latest_rsi_matrix,
)
from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.export_csv import ExportConfig, export_csv
from app.tools.stats_converter import convert_stats


def analyze_rsi_parameters(
    data: pl.DataFrame,
    config: dict[str, Any],
    rsi_thresholds: np.ndarray,
    rsi_windows: np.ndarray,
    log: Callable,
) -> dict[str, np.ndarray]:
    """
    Analyze RSI parameters across different thresholds and window lengths.

    Args:
        data (pl.DataFrame): Price and indicator data
        config (Dict[str, Any]): Strategy configuration
        rsi_thresholds (np.ndarray): Array of RSI thresholds to test
        rsi_windows (np.ndarray): Array of RSI window lengths to test
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary containing metric matrices
    """
    # Initialize result matrices with shape (windows, thresholds) to match RSI mask
    matrices = {
        "returns": np.zeros((len(rsi_windows), len(rsi_thresholds))),
        "win_rate": np.zeros((len(rsi_windows), len(rsi_thresholds))),
        "sharpe_ratio": np.zeros((len(rsi_windows), len(rsi_thresholds))),
        "trades": np.zeros((len(rsi_windows), len(rsi_thresholds))),
    }
    portfolios = []

    # Convert price data to pandas for talib
    price_history = pd.Series(data["Close"].to_numpy())
    last_bar = price_history.iloc[-1]

    # Calculate RSI values and mask matrix
    if config.get("USE_CURRENT", False):
        log("\nCalculating current RSI values and determining active combinations...")
        _, rsi_mask = calculate_latest_rsi_matrix(
            last_bar=last_bar,
            price_history=price_history,
            rsi_windows=rsi_windows,
            rsi_thresholds=rsi_thresholds,
            log=log,
        )
        log("\nApplying mask to performance metrics...")

    # Get baseline performance ONLY IF RELATIVE is True
    if config.get("RELATIVE", True):
        baseline_config = {**config, "USE_RSI": False}
        baseline_data = calculate_ma_and_signals(
            data,
            baseline_config["FAST_PERIOD"],
            baseline_config["SLOW_PERIOD"],
            baseline_config,
            log,
        )
        baseline_portfolio = backtest_strategy(baseline_data, baseline_config, log)
        baseline_stats = convert_stats(
            baseline_portfolio.stats(), log, baseline_config, None,
        )

        # Store baseline metrics
        baseline_metrics = {
            "returns": float(baseline_stats.get("Total Return [%]", 0)),
            "win_rate": float(baseline_stats.get("Win Rate [%]", 0)),
            "sharpe_ratio": float(baseline_stats.get("Sharpe Ratio", 0)),
            "trades": float(baseline_stats.get("Total Closed Trades", 0)),
        }

        if log:
            log(
                f"Baseline metrics - Returns: {baseline_metrics['returns']:.2f}%, "
                f"Win Rate: {baseline_metrics['win_rate']:.2f}%, "
                f"Sharpe: {baseline_metrics['sharpe_ratio']:.2f}, "
                f"Trades: {baseline_metrics['trades']}",
            )

    # Analyze each combination
    for i, threshold in enumerate(rsi_thresholds):
        config["RSI_THRESHOLD"] = threshold
        config["USE_RSI"] = True

        for j, window in enumerate(rsi_windows):
            config["RSI_WINDOW"] = window
            data_with_signals = calculate_ma_and_signals(
                data, config["FAST_PERIOD"], config["SLOW_PERIOD"], config, log,
            )

            portfolio = backtest_strategy(data_with_signals, config, log)
            stats = convert_stats(portfolio.stats(), log, config, None)

            # Add RSI parameters and append to portfolios
            stats.update({"RSI Window": window, "RSI Threshold": threshold})
            portfolios.append(stats)

            # Calculate relative metrics ONLY IF RELATIVE is True
            for metric in matrices:
                current = float(
                    stats.get(
                        {
                            "returns": "Total Return [%]",
                            "win_rate": "Win Rate [%]",
                            "sharpe_ratio": "Sharpe Ratio",
                            "trades": "Total Closed Trades",
                        }[metric],
                        0,
                    ),
                )

                if config.get("RELATIVE", True):
                    baseline = baseline_metrics[metric]
                    if metric in ["sharpe_ratio", "trades"] and baseline != 0:
                        matrices[metric][j, i] = (current / baseline) * 100 - 100
                    else:
                        matrices[metric][j, i] = current - baseline
                else:
                    matrices[metric][
                        j, i,
                    ] = current  # Use absolute value when RELATIVE is False

            if log:
                log(f"Analyzed RSI window {window}, threshold {threshold}")

    # Export results
    filename = f"{config['FAST_PERIOD']}_{config['SLOW_PERIOD']}.csv"
    export_config = ExportConfig(
        BASE_DIR=config["BASE_DIR"],
        TICKER=config.get("TICKER"),
        USE_HOURLY=config.get("USE_HOURLY", False),
        USE_SMA=config.get("USE_SMA", False),
    )
    export_csv(portfolios, "ma_cross", export_config, "rsi", filename)

    # Apply RSI mask if USE_CURRENT is True
    if config.get("USE_CURRENT", False):
        for metric_name in matrices:
            matrices[metric_name] = apply_rsi_mask(matrices[metric_name], rsi_mask)
            if log:
                active_count = np.sum(~np.isnan(matrices[metric_name]))
                total_count = matrices[metric_name].size
                log(f"{metric_name}: {active_count}/{total_count} cells active")

    return matrices
