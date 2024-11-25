"""
Slippage Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on slippage parameters in combination with
EMA cross signals. It analyzes how different slippage percentages affect strategy
performance metrics including returns, win rate, and expectancy.

Note: For long positions, slippage represents an increase in entry price above the signal price.
      We represent this as negative values where -5% means entering 5% above the signal price.
"""

import polars as pl
import numpy as np
from typing import TypedDict, NotRequired
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.tools.calculate_mas import calculate_mas
from app.tools.get_data import get_data
from app.tools.calculate_rsi import calculate_rsi
from tools.slippage_analysis import run_sensitivity_analysis
from tools.slippage_plotting import plot_results

class Config(TypedDict):
    """
    Configuration type definition for slippage analysis.

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
    STOP_LOSS: NotRequired[float]
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
    "USE_SMA": True,
    "TICKER": 'CSX',
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'BTC-USD',
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "SHORT_WINDOW": 75,
    "LONG_WINDOW": 83,
    "RSI_PERIOD": 14,
    "USE_RSI": False,
    "RSI_THRESHOLD": 53,
    "STOP_LOSS": 0.0416
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
        module_name='ma_cross',
        log_file='5_review_slippage.log'
    )
    
    try:
        config = get_config(config)
        log(f"Starting slippage analysis for {config['TICKER']}")
        
        # Create slippage range (0% to 5%)
        slippage_range = np.arange(0, 5.01, 0.01)
        log(f"Using slippage range: {slippage_range[0]}% to {slippage_range[-1]}%")
        
        data = get_data(config["TICKER"], config)
        data = calculate_mas(data, config['SHORT_WINDOW'], config['LONG_WINDOW'], config.get('USE_SMA', False))
        
        if config.get('USE_RSI', False):
            data = calculate_rsi(data, config['RSI_PERIOD'])
            log(f"RSI enabled with period: {config['RSI_PERIOD']}")

        # Use new slippage analysis module
        results_df = run_sensitivity_analysis(data, slippage_range, config)
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
