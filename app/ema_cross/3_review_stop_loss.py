"""
Stop Loss Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on stop loss parameters in combination with
EMA cross signals. It analyzes how different stop loss percentages affect strategy
performance metrics including returns, win rate, and expectancy.
"""

import polars as pl
import numpy as np
from typing import TypedDict, NotRequired
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.tools.calculate_mas import calculate_mas
from app.tools.get_data import get_data
from app.tools.calculate_rsi import calculate_rsi
from tools.stop_loss_analysis import run_sensitivity_analysis
from tools.stop_loss_plotting import plot_results

class Config(TypedDict):
    """
    Configuration type definition for stop loss analysis.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average
        LONG_WINDOW (int): Period for long moving average
        USE_RSI (bool): Whether to enable RSI filtering
        RSI_PERIOD (int): Period for RSI calculation
        RSI_THRESHOLD (float): RSI threshold for signal filtering

    Optional Fields:
        SHORT (NotRequired[bool]): Whether to enable short positions
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
    SHORT_WINDOW: int
    LONG_WINDOW: int
    USE_RSI: bool
    RSI_PERIOD: int
    RSI_THRESHOLD: float
    SHORT: NotRequired[bool]
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
    "TICKER": 'BTC-USD',
    "SHORT_WINDOW": 65,
    "LONG_WINDOW": 74,
    "RSI_PERIOD": 14,
    "USE_HOURLY": True,
    "USE_SMA": True,
    "USE_RSI": False,
    "RSI_THRESHOLD": 53
}

def run(config: Config = config) -> bool:
    """
    Run stop loss sensitivity analysis.

    This function:
    1. Sets up logging
    2. Prepares data with moving averages and RSI (if enabled)
    3. Runs sensitivity analysis across stop loss percentages
    4. Generates and saves visualization plots

    Args:
        config (Config): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful, raises exception otherwise

    Raises:
        Exception: If analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='3_review_stop_loss.log'
    )
    
    try:
        config = get_config(config)
        log(f"Starting stop loss analysis for {config['TICKER']}")
        
        stop_loss_range = np.arange(0, 15, 0.01)
        log(f"Using stop loss range: {stop_loss_range[0]}% to {stop_loss_range[-1]}%")

        data = get_data(config["TICKER"], config)
        data = calculate_mas(data, config['SHORT_WINDOW'], config['LONG_WINDOW'], config.get('USE_SMA', False))
        
        if config.get('USE_RSI', False):
            data = calculate_rsi(data, config['RSI_PERIOD'])
            log(f"RSI enabled with period: {config['RSI_PERIOD']}")

        results_df = run_sensitivity_analysis(data, stop_loss_range, config)
        log("Sensitivity analysis completed")
        
        pl.Config.set_fmt_str_lengths(20)
        plot_results(config["TICKER"], results_df, log)
        log("Results plotted successfully")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
