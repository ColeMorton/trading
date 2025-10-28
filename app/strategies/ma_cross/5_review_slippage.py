"""
Slippage Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on slippage parameters in combination with
EMA cross signals. It analyzes how different slippage percentages affect strategy
performance metrics including returns, win rate, and expectancy.

Note: For long positions, slippage represents an increase in entry price above the signal price.
      We represent this as negative values where -5% means entering 5% above the signal price.
"""

from typing import TypedDict

import numpy as np
import polars as pl
from typing_extensions import NotRequired

from app.strategies.ma_cross.tools.slippage_analysis import run_sensitivity_analysis
from app.strategies.ma_cross.tools.slippage_plotting import plot_results
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_rsi import calculate_rsi
from app.tools.config_service import ConfigService
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging


class Config(TypedDict):
    """
    Configuration type definition for slippage analysis.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        FAST_PERIOD (int): Period for short moving average
        SLOW_PERIOD (int): Period for long moving average
        USE_RSI (bool): Whether to enable RSI filtering
        RSI_WINDOW (int): Period for RSI calculation
        RSI_THRESHOLD (int): RSI threshold for signal filtering

    Optional Fields:
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
    """

    TICKER: str
    FAST_PERIOD: int
    SLOW_PERIOD: int
    USE_RSI: bool
    RSI_WINDOW: int
    RSI_THRESHOLD: int
    STOP_LOSS: NotRequired[float]
    DIRECTION: NotRequired[str]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]


# Default Configuration
config: Config = {
    "TICKER": "XYZ",
    "FAST_PERIOD": 7,
    "SLOW_PERIOD": 27,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "REFRESH": False,
    "USE_HOURLY": False,
    "RELATIVE": True,
    "DIRECTION": "Long",
    "USE_RSI": False,
    "RSI_WINDOW": 29,
    "RSI_THRESHOLD": 48,
    "STOP_LOSS": 0.1237,
}


def run(config: Config = config) -> bool:
    """
    Run slippage sensitivity analysis.

    This function:
    1. Sets up logging
    2. Prepares data with moving averages and RSI (if enabled)
    3. Runs sensitivity analysis across slippage percentages
    4. Generates and saves visualization plots

    Note: We use negative values to represent slippage, where -5% means entering 5% above
    the signal price. Higher negative values (e.g. -5%) represent worse entries than
    lower negative values (e.g. -1%).

    Args:
        config (Config): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful, raises exception otherwise

    Raises:
        Exception: If analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name="ma_cross",
        log_file="5_review_slippage.log",
    )

    try:
        config = ConfigService.process_config(config)
        log(f"Starting slippage analysis for {config['TICKER']}")

        # Create slippage range (0% to 5%)
        slippage_range = np.arange(0, 5.01, 0.01)
        log(f"Using slippage range: {slippage_range[0]}% to {slippage_range[-1]}%")

        data = get_data(config["TICKER"], config, log)
        data = calculate_mas(
            data,
            config["FAST_PERIOD"],
            config["SLOW_PERIOD"],
            config.get("USE_SMA", False),
            log,
        )

        if config.get("USE_RSI", False):
            data = calculate_rsi(data, config["RSI_WINDOW"])
            log(f"RSI enabled with period: {config['RSI_WINDOW']}")

        # Use new slippage analysis module
        results_df = run_sensitivity_analysis(data, slippage_range, config)
        log("Sensitivity analysis completed")

        pl.Config.set_fmt_str_lengths(20)
        plot_results(config["TICKER"], results_df, log)
        log("Results plotted successfully")

        log_close()
        return True

    except Exception as e:
        log(f"Execution failed: {e!s}", "error")
        log_close()
        raise


if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {e!s}")
        raise
