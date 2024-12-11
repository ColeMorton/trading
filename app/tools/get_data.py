from typing import Callable, Union, Tuple
import polars as pl
from app.tools.data_types import DataConfig
from app.tools.download_data import download_data
from app.tools.use_synthetic import use_synthetic
from app.geometric_brownian_motion.get_median import get_median

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
            log(f"Downloading market data for {ticker}")
            data = download_data(ticker, config, log)
            log("Market data download completed successfully")

        log(f"Data retrieval completed with {len(data)} records")
        return data

    except Exception as e:
        log(f"Error in get_data: {str(e)}", "error")
        raise
