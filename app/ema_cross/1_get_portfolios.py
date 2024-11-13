import os
import time
from typing import TypedDict, NotRequired, Union, List
import numpy as np
import polars as pl
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging, log_and_flush
from tools.parameter_sensitivity_analysis import parameter_sensitivity_analysis
from tools.filter_portfolios import filter_portfolios
from tools.is_file_from_today import is_file_from_today

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Setup logging
log_dir = os.path.join(project_root, 'logs', 'ma_cross')
logger, file_handler = setup_logging('portfolio_logger', log_dir, '1_get_portfolios.log')
log_and_flush(logger, file_handler, "Logging initialized")

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
    "TICKER": 'SUI-USD',
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "REFRESH": False
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
        log_and_flush(logger, file_handler, f"Processing ticker: {ticker}")
        
        config_copy = config.copy()
        config_copy["TICKER"] = ticker
        
        # Construct file path
        file_name = f'{ticker}{"_H" if config.get("USE_HOURLY_DATA", False) else "_D"}{"_SMA" if config.get("USE_SMA", False) else "_EMA"}'
        file_path = f'./csv/ma_cross/portfolios/{file_name}.csv'

        log_and_flush(logger, file_handler, f"Checking existing portfolio data from {file_path}")
        
        # Check if file exists and was created today
        if config.get("REFRESH", True) == False and os.path.exists(file_path) and is_file_from_today(file_path):
            log_and_flush(logger, file_handler, f"Loading existing portfolio data.")
            portfolios = pl.read_csv(file_path)
        else:
            # Create distinct integer values for windows
            short_windows = np.arange(2, config["WINDOWS"] + 1)  # [2, 3, ..., WINDOWS]
            long_windows = np.arange(3, config["WINDOWS"] + 1)  # [3, 4, ..., WINDOWS]

            log_and_flush(logger, file_handler, f"Getting data...")
            data = get_data(ticker, config_copy)

            log_and_flush(logger, file_handler, f"Beginning analysis...")
            portfolios = parameter_sensitivity_analysis(data, short_windows, long_windows, config_copy)

        print(f"\nResults for {ticker} {"SMA" if config.get("USE_SMA", False) else "EMA"}:")
        print(portfolios)

        filtered_portfolios = filter_portfolios(pl.DataFrame(portfolios), config_copy)
        print(filtered_portfolios)

    return True

if __name__ == "__main__":
    try:
        start_time = time.time()
        log_and_flush(logger, file_handler, "Starting execution")
        
        config_copy = config.copy()
        
        # Check if USE_SMA exists in config
        if "USE_SMA" not in config_copy:
            # Run with USE_SMA = False
            config_copy["USE_SMA"] = False
            log_and_flush(logger, file_handler, "Running with EMA")
            run(config_copy)
            
            # Run with USE_SMA = True
            config_copy["USE_SMA"] = True
            log_and_flush(logger, file_handler, "Running with SMA")
            run(config_copy)
        else:
            # Run with existing USE_SMA value
            run(config_copy)
            
        end_time = time.time()
        execution_time = end_time - start_time
        execution_msg = f"Total execution time: {execution_time:.2f} seconds"
        print(execution_msg)
        log_and_flush(logger, file_handler, execution_msg)
            
    except Exception as e:
        log_and_flush(logger, file_handler, f"Execution failed: {e}", "error")
        raise
