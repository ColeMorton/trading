from typing import Callable, Union, Tuple, Optional
import os
import polars as pl
from app.tools.data_types import DataConfig
from app.tools.download_data import fetch_latest_data_point, download_complete_dataset
from app.tools.use_synthetic import use_synthetic
from app.geometric_brownian_motion.get_median import get_median
from app.tools.file_utils import is_file_from_today, is_file_from_this_hour
from app.tools.market_status import is_market_open, validate_cached_data_freshness
from app.tools.data_validation import validate_data

def get_cached_data(ticker: str, config: DataConfig, log: Callable) -> Optional[pl.DataFrame]:
    """
    Get cached data from file if available and valid.
    
    Args:
        ticker: Stock ticker symbol
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        Optional[pl.DataFrame]: Cached data if available, None otherwise
    """
    # Construct file path using BASE_DIR
    file_name = f'{ticker}{"_H" if config.get("USE_HOURLY", False) else "_D"}'
    directory = os.path.join(config['BASE_DIR'], 'csv', 'price_data')
    
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Use absolute path
    file_path = os.path.abspath(os.path.join(directory, f'{file_name}.csv'))

    log(f"Checking existing data from {file_path}.")
    
    # Check if file exists
    if not os.path.exists(file_path):
        log("File doesn't exist.")
        return None
        
    # Check if file was created in the appropriate timeframe
    is_valid = (
        is_file_from_this_hour(file_path)
        if config.get("USE_HOURLY", False)
        else is_file_from_today(file_path)
    )
    
    if is_valid:
        log(f"Loading existing data from {file_path}.")
        data = pl.read_csv(file_path)
        return data
    else:
        timeframe = "hour" if config.get("USE_HOURLY", False) else "day"
        log(f"File exists but wasn't created this {timeframe}.")
        return None

def get_latest_market_data(ticker: str, config: DataConfig, log: Callable) -> pl.DataFrame:
    """
    Get the most up-to-date market data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        pl.DataFrame: Latest market data
    """
    try:
        # Check if we should use cached data
        if config.get("REFRESH", True) == False:
            cached_data = get_cached_data(ticker, config, log)
            if cached_data is not None:
                log(f"Using cached data for {ticker}")
                # Even when using cached data, validate its freshness
                if validate_cached_data_freshness(cached_data, ticker, log):
                    return validate_data(cached_data, config, log)
                else:
                    log(f"Cached data for {ticker} is stale, fetching fresh data despite REFRESH=False")
        
        # Always fetch the latest data point to check if market is open
        latest_data = fetch_latest_data_point(ticker, config, log)
        
        # Always check market hours (this feature is always enabled)
        market_status = is_market_open(latest_data, ticker, config, log)
        log(f"Market status for {ticker}: {'Open' if market_status else 'Closed'}")
        
        # If market is closed, we can use cached data from today if available
        if not market_status and config.get("REFRESH", True) == False:
            cached_data = get_cached_data(ticker, config, log)
            if cached_data is not None:
                log(f"Market is closed. Using cached data for {ticker}")
                return validate_data(cached_data, config, log)
        
        # Download complete dataset
        log(f"Downloading fresh data for {ticker}")
        data = download_complete_dataset(ticker, config, log)
        if data is None or len(data) == 0:
            raise ValueError(f"Downloaded data for {ticker} is empty")
        
        # Validate and clean data
        return validate_data(data, config, log)
    except Exception as e:
        log(f"Error retrieving market data: {str(e)}", "error")
        raise

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
        log(f"Initiating data retrieval for {ticker}", "info")
        
        if config.get('USE_GBM', False):
            log("Using Geometric Brownian Motion simulation")
            data = get_median(config)
            log("GBM simulation completed successfully")
            # Validate GBM data
            data = validate_data(data, config, log)
        elif config.get('USE_SYNTHETIC', False):
            ticker_parts = ticker.split('_')
            if len(ticker_parts) != 2:
                raise ValueError(f"Invalid ticker format for synthetic pair: {ticker}. Expected format: TICKER1_TICKER2")
            ticker1, ticker2 = ticker_parts
            log(f"Creating synthetic pair using {ticker1} and {ticker2}")
            data, synthetic_ticker = use_synthetic(ticker1, ticker2, config, log)
            log("Synthetic pair creation completed successfully")
            # Validate synthetic data
            data = validate_data(data, config, log)
            log(f"Data retrieval completed with {len(data)} records")
            return data, synthetic_ticker
        else:
            log(f"Retrieving market data for {ticker}")
            try:
                data = get_latest_market_data(ticker, config, log)
                if data is None or data.is_empty():
                    raise ValueError(f"Failed to retrieve data for {ticker}")
                log("Market data retrieval completed successfully")
            except Exception as e:
                log(f"Error retrieving market data: {str(e)}", "error")
                raise ValueError(f"Failed to retrieve data for {ticker}: {str(e)}")

        log(f"Data retrieval completed with {len(data)} records")
        return data

    except Exception as e:
        log(f"Error in get_data: {str(e)}", "error")
        raise
