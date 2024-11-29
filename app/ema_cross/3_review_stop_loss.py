"""
Stop Loss Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on stop loss parameters in combination with
EMA cross signals. It analyzes how different stop loss percentages affect strategy
performance metrics including returns, win rate, and expectancy.
"""

import os
import numpy as np
from typing import TypedDict, NotRequired, Union, List
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.tools.file_utils import load_cached_stop_loss_analysis, get_stop_loss_cache_filepath
from app.ema_cross.tools.stop_loss_analysis import analyze_stop_loss_parameters
from app.ema_cross.tools.stop_loss_plotting import create_stop_loss_heatmap

class StopLossConfig(TypedDict):
    """Configuration type definition for stop loss analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average
        LONG_WINDOW (int): Period for long moving average
        BASE_DIR (str): Base directory for file operations
        USE_RSI (bool): Whether to enable RSI filtering
        RSI_PERIOD (int): Period for RSI calculation if USE_RSI is True
        RSI_THRESHOLD (float): RSI threshold for signal filtering if USE_RSI is True

    Optional Fields:
        SHORT (NotRequired[bool]): Whether to enable short positions
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
        REFRESH (NotRequired[bool]): Whether to force refresh analysis
    """
    TICKER: Union[str, List[str]]
    SHORT_WINDOW: int
    LONG_WINDOW: int
    BASE_DIR: str
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
    REFRESH: NotRequired[bool]

# Default configuration
default_config: StopLossConfig = {
    "TICKER": "NKE",
    "SHORT_WINDOW": 2,
    "LONG_WINDOW": 33,
    "BASE_DIR": ".",
    "USE_SMA": False,
    "USE_RSI": True,
    "RSI_PERIOD": 23,
    "RSI_THRESHOLD": 47,
    "REFRESH": False
}

def run(config: StopLossConfig) -> bool:
    """
    Run stop loss parameter sensitivity analysis.

    This function performs sensitivity analysis on stop loss parameters by:
    1. Setting up logging
    2. Loading cached results or preparing new data
    3. Running sensitivity analysis across stop loss parameters
    4. Displaying interactive heatmaps in browser

    Args:
        config (StopLossConfig): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If data preparation or analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='3_review_stop_loss.log'
    )
    
    try:
        config = get_config(config)
        log(f"Starting stop loss analysis for {config['TICKER']}")
        
        # Define parameter ranges with explicit 2 decimal place precision
        stop_loss_range = np.round(np.arange(0, 15, 0.01), decimals=2)
        log(f"Using stop loss range: {stop_loss_range[0]:.2f}% to {stop_loss_range[-1]:.2f}%")

        # Check for cached results
        cache_dir, cache_file = get_stop_loss_cache_filepath(config)
        cache_path = os.path.join(cache_dir, cache_file)
        metric_matrices = None
        
        if not config.get("REFRESH", False):
            metric_matrices = load_cached_stop_loss_analysis(
                cache_path,
                stop_loss_range
            )
            if metric_matrices is not None:
                log("Using cached stop loss analysis results")
        
        # If no cache or refresh requested, run new analysis
        if metric_matrices is None:
            log("Running new stop loss analysis")
            data = get_data(config["TICKER"], config)
            
            metric_matrices = analyze_stop_loss_parameters(
                data=data,
                config=config,
                stop_loss_range=stop_loss_range,
                log=log
            )
        
        if metric_matrices is None:
            raise Exception("Failed to generate or load metric matrices")
            
        # Create heatmap figures
        figures = create_stop_loss_heatmap(
            metric_matrices=metric_matrices,
            stop_loss_range=stop_loss_range,
            ticker=str(config["TICKER"])
        )
        
        if not figures:
            raise Exception("Failed to create heatmap figures")
            
        # Display all heatmaps in specific order
        metrics_to_display = ['trades', 'returns', 'sharpe_ratio', 'win_rate']
        for metric_name in metrics_to_display:
            if metric_name in figures:
                figures[metric_name].show()
                log(f"Displayed {metric_name} heatmap")
            else:
                raise Exception(f"Required {metric_name} heatmap not found in figures dictionary")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Error during stop loss analysis: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run(default_config)
        if result:
            print("Stop loss analysis completed successfully!")
    except Exception as e:
        print(f"Stop loss analysis failed: {str(e)}")
        raise
