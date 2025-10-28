"""
Stop Loss Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on stop loss parameters in combination with
EMA cross signals. It analyzes how different stop loss percentages affect strategy
performance metrics including returns, win rate, and expectancy.

The analysis can be performed in relative or absolute terms based on the config:
- When config['RELATIVE'] is True, all metrics are relative to the baseline analysis
- When config['RELATIVE'] is False, all metrics are absolute
"""

import os
import sys

import numpy as np
import polars as pl


# Add the project root to Python path for module imports
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from app.strategies.ma_cross.tools.stop_loss_analysis import (
    analyze_stop_loss_parameters,
)
from app.strategies.ma_cross.tools.stop_loss_plotting import create_stop_loss_heatmap
from app.tools.cache_utils import CacheConfig, get_cache_filepath, load_cached_analysis
from app.tools.config_service import ConfigService
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging


def export_stop_loss_sensitivity_csv(
    metric_matrices: dict[str, np.ndarray],
    stop_loss_range: np.ndarray,
    config: CacheConfig,
    log: callable,
) -> str:
    """
    Export stop loss sensitivity analysis results to CSV.

    Args:
        metric_matrices: Dictionary containing metric arrays (trades, returns, score, win_rate)
        stop_loss_range: Array of stop loss percentages tested
        config: Strategy configuration
        log: Logging function

    Returns:
        str: Path to exported CSV file
    """
    # Create output directory
    output_dir = "./data/raw/stop_loss"
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename using consistent naming convention
    ticker = config.get("TICKER", "UNKNOWN")
    if isinstance(ticker, list):
        ticker = ticker[0] if ticker else "UNKNOWN"

    timeframe = "H" if config.get("USE_HOURLY", False) else "D"
    strategy_type = "SMA" if config.get("USE_SMA", False) else "EMA"
    fast_period = config.get("FAST_PERIOD", 0)
    slow_period = config.get("SLOW_PERIOD", 0)

    filename = f"{ticker}_{timeframe}_{strategy_type}_{fast_period}_{slow_period}.csv"
    filepath = os.path.join(output_dir, filename)

    # Create comprehensive DataFrame with core metrics only
    data = {
        "Stop Loss [%]": stop_loss_range,
        "Score": metric_matrices["score"],
        "Total Return [%]": metric_matrices["returns"],
        "Win Rate [%]": metric_matrices["win_rate"],
        "Total Trades": metric_matrices["trades"],
        "Profit Factor": metric_matrices["profit_factor"],
        "Expectancy per Trade": metric_matrices["expectancy"],
        "Sortino Ratio": metric_matrices["sortino"],
        "Beats BNH [%]": metric_matrices["beats_bnh"],
        "Avg Trade Duration": metric_matrices["avg_trade_duration"],
        "Trades Per Day": metric_matrices["trades_per_day"],
    }

    # Create and export DataFrame
    df = pl.DataFrame(data)

    # Reorder columns for logical grouping
    column_order = [
        "Stop Loss [%]",
        "Score",
        "Total Return [%]",
        "Win Rate [%]",
        "Total Trades",
        "Profit Factor",
        "Expectancy per Trade",
        "Sortino Ratio",
        "Beats BNH [%]",
        "Avg Trade Duration",
        "Trades Per Day",
    ]

    df = df.select(column_order)
    df.write_csv(filepath)

    log(f"Exported stop loss sensitivity analysis to {filepath}")
    log(f"CSV contains {len(df)} rows and {len(df.columns)} columns")
    log(f"Columns: {', '.join(df.columns)}")

    return filepath


# Use CacheConfig from cache_utils.py
default_config: CacheConfig = {
    "TICKER": "AMZN",
    "FAST_PERIOD": 51,
    "SLOW_PERIOD": 69,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "REFRESH": True,
    "USE_HOURLY": False,
    "RELATIVE": False,
    "DIRECTION": "Long",
    "USE_CURRENT": False,
    "USE_RSI": False,
    "RSI_WINDOW": 4,
    "RSI_THRESHOLD": 52,
}


def run(config: CacheConfig) -> bool:
    """
    Run stop loss parameter sensitivity analysis.

    This function performs sensitivity analysis on stop loss parameters by:
    1. Setting up logging
    2. Loading cached results or preparing new data
    3. Running sensitivity analysis across stop loss parameters
    4. Exporting comprehensive results to CSV in ./data/raw/stop_loss/
    5. Displaying interactive heatmaps in browser

    Args:
        config (CacheConfig): Configuration dictionary containing strategy parameters.
            When config['RELATIVE'] is True, metrics are relative to baseline analysis.
            When config['RELATIVE'] is False, metrics are absolute.

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If data preparation or analysis fails

    CSV Export:
        Exports sensitivity analysis to ./data/raw/stop_loss/ with naming convention:
        [TICKER]_[TIMEFRAME]_[STRATEGY_TYPE]_[FAST_PERIOD]_[SLOW_PERIOD].csv

        Contains 300 rows of optimized stop loss analysis (0.01% to 15.0%) with metrics:
        - Stop Loss Percentage
        - Score (optimized composite metric)
        - Returns, Win Rate, Trade Count
        - Profit Factor, Expectancy per Trade, Sortino Ratio
        - Beats Buy-and-Hold [%], Avg Trade Duration, Trades Per Day
    """
    log, log_close, _, _ = setup_logging(
        module_name="ma_cross", log_file="3_review_stop_loss.log",
    )

    try:
        config = ConfigService.process_config(config)
        log(f"Starting stop loss analysis for {config['TICKER']}")

        # Define optimized parameter ranges (300 rows max, 15.0% max stop loss)
        # 0.01 to 1.99 (0.01 steps) - high precision for critical low stop loss values (199 points)
        range1 = np.arange(0.01, 2.00, 0.01)
        # 2.00 to 4.96 (0.04 steps) - medium precision for mid-range values (75 points)
        range2 = np.arange(2.00, 5.00, 0.04)
        # 5.00 to 15.0 (0.4 steps) - coarse precision for high stop loss values (26 points)
        range3 = np.arange(5.00, 15.4, 0.4)

        # Combine ranges and round to 2 decimal places (total: 300 points)
        stop_loss_range = np.round(np.concatenate([range1, range2, range3]), decimals=2)
        log(
            f"Using stop loss range: {stop_loss_range[0]:.2f}% to {stop_loss_range[-1]:.2f}%",
        )

        # Check for cached results
        cache_dir, cache_file = get_cache_filepath(config, "stop_loss")
        cache_path = os.path.join(cache_dir, cache_file)
        metric_matrices = None

        if not config.get("REFRESH", False):
            metric_matrices = load_cached_analysis(
                filepath=cache_path,
                param_range=stop_loss_range,
                param_column="Stop Loss [%]",
            )
            if metric_matrices is not None:
                log("Using cached stop loss analysis results")

        # If no cache or refresh requested, run new analysis
        if metric_matrices is None:
            log("Running new stop loss analysis")
            data = get_data(config["TICKER"], config, log)

            metric_matrices = analyze_stop_loss_parameters(
                data=data, config=config, stop_loss_range=stop_loss_range, log=log,
            )

        if metric_matrices is None:
            msg = "Failed to generate or load metric matrices"
            raise Exception(msg)

        # Export sensitivity analysis results to CSV
        try:
            csv_filepath = export_stop_loss_sensitivity_csv(
                metric_matrices=metric_matrices,
                stop_loss_range=stop_loss_range,
                config=config,
                log=log,
            )
            log(f"Stop loss sensitivity analysis exported to: {csv_filepath}")
        except Exception as csv_error:
            log(f"Warning: Failed to export CSV: {csv_error!s}", "warning")
            # Continue with heatmap generation even if CSV export fails

        # Create heatmap figures
        figures = create_stop_loss_heatmap(
            metric_matrices=metric_matrices,
            stop_loss_range=stop_loss_range,
            ticker=str(config["TICKER"]),
            config=config,  # Pass config to create_stop_loss_heatmap
        )

        if not figures:
            msg = "Failed to create heatmap figures"
            raise Exception(msg)

        # Display all heatmaps in specific order
        metrics_to_display = ["trades", "returns", "score", "win_rate"]
        for metric_name in metrics_to_display:
            if metric_name in figures:
                figures[metric_name].show()
                log(f"Displayed {metric_name} heatmap")
            else:
                msg = f"Required {metric_name} heatmap not found in figures dictionary"
                raise Exception(
                    msg,
                )

        log_close()
        return True

    except Exception as e:
        log(f"Error during stop loss analysis: {e!s}", "error")
        log_close()
        raise


if __name__ == "__main__":
    try:
        result = run(default_config)
        if result:
            print("Stop loss analysis completed successfully!")
    except Exception as e:
        print(f"Stop loss analysis failed: {e!s}")
        raise
