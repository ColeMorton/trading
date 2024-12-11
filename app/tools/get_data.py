from typing import Callable, Union, Tuple
import os
import polars as pl
from app.tools.data_types import DataConfig
from app.tools.download_data import download_data
from app.tools.use_synthetic import use_synthetic
from app.geometric_brownian_motion.get_median import get_median
from app.tools.file_utils import is_file_from_today, is_file_from_this_hour

def valid_data(ticker: str, config: DataConfig, log: Callable):
    if config.get("REFRESH", True) == False:
        # Construct file path using BASE_DIR
        file_name = f'{ticker}{"_H" if config.get("USE_HOURLY", False) else "_D"}'
        directory = os.path.join(config['BASE_DIR'], 'csv', 'price_data')
        
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Use absolute path
        file_path = os.path.abspath(os.path.join(directory, f'{file_name}.csv'))

        log(f"Checking existing data from {file_path}.")
        
        # Check if file exists and was created in the appropriate timeframe
        if os.path.exists(file_path):
            is_valid = (
                is_file_from_this_hour(file_path) 
                if config.get("USE_HOURLY", False) 
                else is_file_from_today(file_path)
            )
            if is_valid:
                log(f"Loading existing data from {file_path}.")
                return pl.read_csv(file_path)
            else:
                timeframe = "hour" if config.get("USE_HOURLY", False) else "day"
                log(f"File exists but wasn't created this {timeframe}. Downloading new data.")
        else:
            log("File doesn't exist. Downloading new data.")
    else:
        log("REFRESH is True. Downloading new data.")
    
    # Only download if we haven't returned existing data
    return download_data(ticker, config, log)


def get_data(ticker: str, config: DataConfig, log: Callable) -> Union[pl.DataFrame, Tuple[pl.DataFrame, str]]:
    """Get data based on configuration settings.
    
    Args:
        ticker (str): Stock ticker symbol
        config (DataConfig): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        Union[pl.DataFrame, Tuple[pl.DataFrame, str]]: Price data based on configuration.
        Returns tuple of (DataFrame, synthetic_ticker) when using synthetic pairs.
    """
    try:
        log(f"Initiating data retrieval for {ticker}")
        
        if config.get('USE_GBM', False):
            log("Using Geometric Brownian Motion simulation")
            data = get_median(config)
            log("GBM simulation completed successfully")
        elif config.get('USE_SYNTHETIC', False):
            log(f"Creating synthetic pair using {config['TICKER_1']} and {config['TICKER_2']}")
            data, synthetic_ticker = use_synthetic(config['TICKER_1'], config['TICKER_2'], config, log)
            log("Synthetic pair creation completed successfully")
            log(f"Data retrieval completed with {len(data)} records")
            return data, synthetic_ticker
        else:
            log(f"Retrieving market data for {ticker}")
            data = valid_data(ticker, config, log)
            if data is None:
                raise ValueError(f"Failed to retrieve data for {ticker}")
            log("Market data download completed successfully")

        log(f"Data retrieval completed with {len(data)} records")
        return data

    except Exception as e:
        log(f"Error in get_data: {str(e)}", "error")
        raise
