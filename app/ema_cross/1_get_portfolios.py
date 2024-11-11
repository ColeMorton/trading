import logging
import os
import time
from typing import TypedDict, NotRequired, Union, List
import numpy as np
import polars as pl
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from tools.parameter_sensitivity_analysis import parameter_sensitivity_analysis
from tools.filter_portfolios import filter_portfolios

# Logging setup
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, '1_get_portfolios.log'), 
                   filemode='w',  # Overwrite file instead of append
                   level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class Config(TypedDict):
    TICKER: Union[str, List[str]]
    WINDOWS: int
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
    "TICKER": ['UNI-USD', 'MKR-USD'],
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "USE_SMA": False
}

def run(config: Config = config) -> bool:
    """
    Run the portfolio analysis for single ticker or multiple tickers.

    Args:
        config (Config): Configuration dictionary containing TICKER (str or list[str]) and other parameters

    Returns:
        bool: True if execution successful
    """
    config = get_config(config)
    
    # Handle both single ticker (str) and multiple tickers (list)
    tickers = [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
    
    for ticker in tickers:
        logging.info(f"Processing ticker: {ticker}")
        config_copy = config.copy()
        config_copy["TICKER"] = ticker
        
        # Create distinct integer values for windows
        short_windows = np.arange(2, config["WINDOWS"] + 1)  # [2, 3, ..., WINDOWS]
        long_windows = np.arange(3, config["WINDOWS"] + 1)  # [3, 4, ..., WINDOWS]

        portfolios = parameter_sensitivity_analysis(get_data(ticker, config_copy), short_windows, long_windows, config_copy)

        print(f"\nResults for {ticker} {"SMA" if config.get("USE_SMA", False) else "EMA"}:")
        print(portfolios)

        filtered_portfolios = filter_portfolios(pl.DataFrame(portfolios), config_copy)
        print(filtered_portfolios)

    return True

if __name__ == "__main__":
    try:
        start_time = time.time()
        logging.info("Starting execution")
        
        config_copy = config.copy()
        
        # Check if USE_SMA exists in config
        if "USE_SMA" not in config_copy:
            # Run with USE_SMA = False
            config_copy["USE_SMA"] = False
            logging.info("Running with EMA")
            run(config_copy)
            
            # Run with USE_SMA = True
            config_copy["USE_SMA"] = True
            logging.info("Running with SMA")
            run(config_copy)
        else:
            # Run with existing USE_SMA value
            run(config_copy)
            
        end_time = time.time()
        execution_time = end_time - start_time
        execution_msg = f"Total execution time: {execution_time:.2f} seconds"
        print(execution_msg)
        logging.info(execution_msg)
            
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
