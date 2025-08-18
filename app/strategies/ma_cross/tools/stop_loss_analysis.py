"""
Stop Loss Analysis Module

This module contains functions for analyzing stop loss parameter sensitivity.
"""

from typing import Any, Callable, Dict

import numpy as np
import polars as pl

from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_rsi import calculate_rsi
from app.tools.export_csv import ExportConfig, export_csv
from app.tools.stats_converter import convert_stats


def analyze_stop_loss_parameters(
    data: pl.DataFrame,
    config: Dict[str, Any],
    stop_loss_range: np.ndarray,
    log: Callable,
) -> Dict[str, np.ndarray]:
    """
    Analyze stop loss parameters across different percentages.

    Args:
        data (pl.DataFrame): Price and indicator data
        config (Dict): Strategy configuration
        stop_loss_range (np.ndarray): Array of stop loss percentages to test
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary containing metric arrays for returns, win rates, and Score
    """
    num_stops = len(stop_loss_range)

    # Initialize result arrays
    returns_array = np.zeros(num_stops)
    win_rate_array = np.zeros(num_stops)
    score_array = np.zeros(num_stops)
    trades_array = np.zeros(num_stops)
    profit_factor_array = np.zeros(num_stops)
    expectancy_array = np.zeros(num_stops)
    sortino_array = np.zeros(num_stops)
    beats_bnh_array = np.zeros(num_stops)
    avg_trade_duration_array = np.zeros(num_stops)
    trades_per_day_array = np.zeros(num_stops)

    # Store portfolios for export
    portfolios = []

    # Add RSI if enabled
    if config.get("USE_RSI", False):
        data = calculate_rsi(data, config["RSI_WINDOW"])
        log(
            f"RSI enabled with period: {config['RSI_WINDOW']} and threshold: {config['RSI_THRESHOLD']}"
        )

    # Calculate MA and base signals
    data_with_signals = calculate_ma_and_signals(
        data,
        config["FAST_PERIOD"],
        config["SLOW_PERIOD"],
        config,
        log,  # Pass the log parameter here
    )

    # Get baseline performance ONLY IF RELATIVE is True
    if config.get("RELATIVE", True):
        baseline_config = {**config, "STOP_LOSS": None}
        baseline_portfolio = backtest_strategy(data_with_signals, baseline_config, log)
        baseline_stats = convert_stats(
            baseline_portfolio.stats(), log, baseline_config, None
        )

        # Store baseline metrics
        baseline_metrics = {
            "returns": float(baseline_stats.get("Total Return [%]", 0)),
            "win_rate": float(baseline_stats.get("Win Rate [%]", 0)),
            "score": float(baseline_stats.get("Score", 0)),
            "trades": float(baseline_stats.get("Total Closed Trades", 0)),
            "profit_factor": float(baseline_stats.get("Profit Factor", 0)),
            "expectancy": float(baseline_stats.get("Expectancy per Trade", 0)),
            "sortino": float(baseline_stats.get("Sortino Ratio", 0)),
            "beats_bnh": float(baseline_stats.get("Beats BNH [%]", 0)),
            "avg_trade_duration": float(
                baseline_stats.get("Avg Trade Duration", "0")
                .replace(" days", "")
                .split()[0]
                if isinstance(baseline_stats.get("Avg Trade Duration"), str)
                else 0
            ),
            "trades_per_day": float(baseline_stats.get("Trades Per Day", 0)),
        }

        if log:
            log(
                f"Baseline metrics - Returns: {baseline_metrics['returns']:.2f}%, "
                f"Win Rate: {baseline_metrics['win_rate']:.2f}%, "
                f"Score: {baseline_metrics['score']:.2f}, "
                f"Trades: {baseline_metrics['trades']}"
            )

    # Analyze each stop loss percentage
    for i, stop_loss in enumerate(stop_loss_range):
        # Convert percentage to decimal (e.g., 3.74% -> 0.0374)
        stop_loss_pct = round(float(stop_loss), 2)
        stop_loss_decimal = stop_loss_pct / 100
        config["STOP_LOSS"] = stop_loss_decimal

        if log:
            log(f"Testing stop loss of {stop_loss_pct:.2f}% ({stop_loss_decimal:.4f})")

        portfolio = backtest_strategy(data_with_signals, config, log)
        stats = portfolio.stats()
        converted_stats = convert_stats(stats, log, config, None)

        # Add stop loss parameter to stats
        converted_stats["Stop Loss [%]"] = stop_loss
        portfolios.append(converted_stats)

        # Calculate metrics
        current_metrics = {
            "returns": float(converted_stats.get("Total Return [%]", 0)),
            "win_rate": float(converted_stats.get("Win Rate [%]", 0)),
            "score": float(converted_stats.get("Score", 0)),
            "trades": float(converted_stats.get("Total Closed Trades", 0)),
            "profit_factor": float(converted_stats.get("Profit Factor", 0)),
            "expectancy": float(converted_stats.get("Expectancy per Trade", 0)),
            "sortino": float(converted_stats.get("Sortino Ratio", 0)),
            "beats_bnh": float(converted_stats.get("Beats BNH [%]", 0)),
            "avg_trade_duration": float(
                converted_stats.get("Avg Trade Duration", "0")
                .replace(" days", "")
                .split()[0]
                if isinstance(converted_stats.get("Avg Trade Duration"), str)
                else 0
            ),
            "trades_per_day": float(converted_stats.get("Trades Per Day", 0)),
        }

        # Calculate relative or absolute metrics based on config
        if config.get("RELATIVE", True):
            # Additive differences for rates and percentages
            returns_array[i] = current_metrics["returns"] - baseline_metrics["returns"]
            win_rate_array[i] = (
                current_metrics["win_rate"] - baseline_metrics["win_rate"]
            )
            beats_bnh_array[i] = (
                current_metrics["beats_bnh"] - baseline_metrics["beats_bnh"]
            )

            # Duration differences (in days)
            avg_trade_duration_array[i] = (
                current_metrics["avg_trade_duration"]
                - baseline_metrics["avg_trade_duration"]
            )
            trades_per_day_array[i] = (
                current_metrics["trades_per_day"] - baseline_metrics["trades_per_day"]
            )

            # Percentage changes for ratios and factors
            for metric_name, array, baseline_val, current_val in [
                (
                    "score",
                    score_array,
                    baseline_metrics["score"],
                    current_metrics["score"],
                ),
                (
                    "trades",
                    trades_array,
                    baseline_metrics["trades"],
                    current_metrics["trades"],
                ),
                (
                    "profit_factor",
                    profit_factor_array,
                    baseline_metrics["profit_factor"],
                    current_metrics["profit_factor"],
                ),
                (
                    "expectancy",
                    expectancy_array,
                    baseline_metrics["expectancy"],
                    current_metrics["expectancy"],
                ),
                (
                    "sortino",
                    sortino_array,
                    baseline_metrics["sortino"],
                    current_metrics["sortino"],
                ),
            ]:
                if baseline_val != 0:
                    array[i] = (current_val / baseline_val) * 100 - 100
                else:
                    array[i] = current_val
        else:
            # Absolute values
            returns_array[i] = current_metrics["returns"]
            win_rate_array[i] = current_metrics["win_rate"]
            score_array[i] = current_metrics["score"]
            trades_array[i] = current_metrics["trades"]
            profit_factor_array[i] = current_metrics["profit_factor"]
            expectancy_array[i] = current_metrics["expectancy"]
            sortino_array[i] = current_metrics["sortino"]
            beats_bnh_array[i] = current_metrics["beats_bnh"]
            avg_trade_duration_array[i] = current_metrics["avg_trade_duration"]
            trades_per_day_array[i] = current_metrics["trades_per_day"]

        if log:
            log(f"Analyzed stop loss {stop_loss_pct:.2f}%")

    # Create filename with MA windows and RSI if used
    ticker_prefix = config.get("TICKER", "")
    if isinstance(ticker_prefix, list):
        ticker_prefix = ticker_prefix[0] if ticker_prefix else ""

    rsi_suffix = (
        f"_RSI_{config['RSI_WINDOW']}_{config['RSI_THRESHOLD']}"
        if config.get("USE_RSI", False)
        else ""
    )
    filename = f"{ticker_prefix}_D_{'SMA' if config.get('USE_SMA', False) else 'EMA'}_{config['FAST_PERIOD']}_{config['SLOW_PERIOD']}{rsi_suffix}.csv"

    # Export portfolios
    export_config = ExportConfig(
        BASE_DIR=config["BASE_DIR"], TICKER=config.get("TICKER")
    )
    export_csv(portfolios, "ma_cross", export_config, "stop_loss", filename)

    # Ensure no NaN values in final arrays
    returns_array = np.nan_to_num(returns_array, 0)
    win_rate_array = np.nan_to_num(win_rate_array, 0)
    score_array = np.nan_to_num(score_array, 0)
    trades_array = np.nan_to_num(trades_array, 0)
    profit_factor_array = np.nan_to_num(profit_factor_array, 0)
    expectancy_array = np.nan_to_num(expectancy_array, 0)
    sortino_array = np.nan_to_num(sortino_array, 0)
    beats_bnh_array = np.nan_to_num(beats_bnh_array, 0)
    avg_trade_duration_array = np.nan_to_num(avg_trade_duration_array, 0)
    trades_per_day_array = np.nan_to_num(trades_per_day_array, 0)

    return {
        "trades": trades_array,
        "returns": returns_array,
        "score": score_array,
        "win_rate": win_rate_array,
        "profit_factor": profit_factor_array,
        "expectancy": expectancy_array,
        "sortino": sortino_array,
        "beats_bnh": beats_bnh_array,
        "avg_trade_duration": avg_trade_duration_array,
        "trades_per_day": trades_per_day_array,
    }
