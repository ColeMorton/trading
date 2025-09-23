import os
from typing import Callable, Tuple, Union

import polars as pl

from app.strategies.geometric_brownian_motion.get_median import get_median
from app.tools.data_types import DataConfig
from app.tools.download_data import download_data
from app.tools.file_utils import is_file_from_this_hour, is_file_from_today
from app.tools.use_synthetic import use_synthetic


def valid_data(ticker: str, config: DataConfig, log: Callable):
    # Handle refresh logic - default to False for smart refresh behavior
    refresh_setting = config.get("REFRESH", False)
    if refresh_setting == False:
        # Import market detection function
        from app.tools.market_hours import MarketType, detect_market_type

        # Detect market type for the ticker
        market_type = detect_market_type(ticker)

        # Use unified cache logic for both crypto and stock assets
        if market_type == MarketType.CRYPTO:
            log(f"Crypto market detected for {ticker}. Using cache logic.")
        else:
            log(f"Stock market detected for {ticker}. Using cache logic.")

        # Determine file suffix based on timeframe
        if config.get("USE_2DAY", False):
            file_suffix = "_2D"
        elif config.get("USE_4HOUR", False):
            file_suffix = "_4H"
        elif config.get("USE_HOURLY", False):
            file_suffix = "_H"
        else:
            file_suffix = "_D"

        file_name = f"{ticker}{file_suffix}"
        directory = os.path.join(config["BASE_DIR"], "data", "raw", "prices")

        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)

        # Use absolute path
        file_path = os.path.abspath(os.path.join(directory, f"{file_name}.csv"))

        log(f"Checking existing data from {file_path}.")

        # Check if file exists and was created in the appropriate timeframe
        if os.path.exists(file_path):
            # For 2-day data, use daily validation since it's derived from daily data
            # For 4-hour data, use hourly validation since it's derived from hourly data
            if config.get("USE_2DAY", False):
                is_valid = is_file_from_today(file_path)
                timeframe = "2-day"
            elif config.get("USE_4HOUR", False):
                is_valid = is_file_from_this_hour(file_path)
                timeframe = "4-hour"
            elif config.get("USE_HOURLY", False):
                is_valid = is_file_from_this_hour(file_path)
                timeframe = "hour"
            else:
                is_valid = is_file_from_today(file_path)
                timeframe = "day"

            if is_valid:
                log(f"Loading existing data from {file_path}.")
                return pl.read_csv(file_path)
            else:
                log(
                    f"File exists but wasn't created this {timeframe}. Downloading new data."
                )
        else:
            log("File doesn't exist. Downloading new data.")
    else:
        log(f"REFRESH is {refresh_setting}. Downloading new data.")

    # Only download if we haven't returned existing data
    return download_data(ticker, config, log)


def get_data(
    ticker: str, config: DataConfig, log: Callable
) -> Union[pl.DataFrame, Tuple[pl.DataFrame, str]]:
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

        # Check if this is a synthetic ticker
        # Primary check: USE_SYNTHETIC flag is explicitly True
        is_synthetic = config.get("USE_SYNTHETIC", False)

        # Fallback check: Detect synthetic ticker by name pattern (contains underscore)
        # This ensures synthetic tickers work even if the flag is not set properly
        if not is_synthetic and "_" in ticker and len(ticker.split("_")) == 2:
            # Looks like a synthetic ticker (TICKER1_TICKER2 format)
            log(f"Detected potential synthetic ticker by name pattern: {ticker}")
            is_synthetic = True
            config["USE_SYNTHETIC"] = True  # Set the flag for proper processing

        if config.get("USE_GBM", False):
            log("Using Geometric Brownian Motion simulation")
            data = get_median(config)
            log("GBM simulation completed successfully")
        elif is_synthetic:
            log(f"Processing as synthetic ticker: {ticker}")
            config["USE_SYNTHETIC"] = True  # Ensure the flag is set

            # First check if TICKER_1 and TICKER_2 are provided in the config
            ticker1 = config.get("TICKER_1")
            ticker2 = config.get("TICKER_2")

            # If not provided in config, try to extract from the ticker name
            if not ticker1 or not ticker2:
                ticker_parts = ticker.split("_")
                if len(ticker_parts) != 2:
                    raise ValueError(
                        f"Invalid ticker format for synthetic pair: {ticker}. Expected format: TICKER1_TICKER2"
                    )
                ticker1, ticker2 = ticker_parts

                # Update config with the extracted tickers
                config["TICKER_1"] = ticker1
                config["TICKER_2"] = ticker2

            log(f"Creating synthetic pair using {ticker1} and {ticker2}")
            data, synthetic_ticker = use_synthetic(ticker1, ticker2, config, log)
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
