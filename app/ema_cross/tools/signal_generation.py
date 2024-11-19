import logging
import polars as pl
import numpy as np
import pandas as pd
from typing import List, Dict, TypedDict, NotRequired
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.utils import save_csv

class Config(TypedDict):
    """Configuration type definition.

    Required Fields:
        TICKER (str): Trading symbol
        WINDOWS (int): Maximum window size to test

    Optional Fields:
        SHORT (NotRequired[bool]): Whether to use short positions
        USE_SMA (NotRequired[bool]): Whether to use SMA instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use GBM simulation
        USE_SYNTHETIC (NotRequired[bool]): Whether to use synthetic data
        TICKER_1 (NotRequired[str]): First ticker for synthetic pair
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pair
        USE_SCANNER (NotRequired[bool]): Whether to use scanner mode
    """
    TICKER: str
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
    USE_SCANNER: NotRequired[bool]

def is_signal_current(signals: pl.DataFrame) -> bool:
    """
    Check if there is a current entry signal.
    
    Args:
        signals: DataFrame containing Signal and Position columns
    
    Returns:
        bool: True if there is a current entry signal, False otherwise
    """
    last_row = signals.tail(1)
    return (last_row.get_column("Signal") == 1).item() and (last_row.get_column("Position") == 0).item()

def get_current_signals(
    data: pl.DataFrame,
    short_windows: List[int],
    long_windows: List[int],
    config: Dict
) -> pl.DataFrame:
    """
    Get current signals for all window combinations.
    
    Args:
        data: Price data DataFrame
        short_windows: List of short window periods
        long_windows: List of long window periods
        config: Configuration dictionary
    
    Returns:
        DataFrame containing window combinations with current signals
    """
    try:
        signals = []
        
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    temp_data = data.clone()
                    temp_data = calculate_ma_and_signals(temp_data, short, long, config)
                    
                    if temp_data is not None and len(temp_data) > 0:
                        current = is_signal_current(temp_data)
                        if current:
                            signals.append({
                                "Short Window": short,
                                "Long Window": long
                            })

        return pl.DataFrame(signals)
    except Exception as e:
        logging.error(f"Failed to get current signals: {e}")
        return pl.DataFrame()

def generate_current_signals(config: Config) -> pl.DataFrame:
    """
    Generate current signals for a given configuration.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        DataFrame containing current signals
    """
    try:
        config = get_config(config)

        # Create distinct integer values for windows
        short_windows = np.arange(2, config["WINDOWS"])
        long_windows = np.arange(3, config["WINDOWS"])

        data = get_data(config["TICKER"], config)
        if data is None:
            logging.error("Failed to get price data")
            return pl.DataFrame()

        current_signals = get_current_signals(data, short_windows, long_windows, config)

        if not config.get("USE_SCANNER", False):
            save_csv(current_signals, "ma_cross", config, 'current_signals')
            
            if len(current_signals) == 0:
                print("No signals found for today")
            else:
                pd.set_option('display.max_rows', None)
                print("\nFull data table:")
                print(current_signals)
        
        return current_signals

    except Exception as e:
        logging.error(f"Failed to generate current signals: {e}")
        return pl.DataFrame()

def check_signal_match(
    signals: List[Dict],
    fast_window: int,
    slow_window: int
) -> bool:
    """
    Check if any signal matches the given window combination.

    Args:
        signals: List of signal dictionaries containing window information
        fast_window: Fast window value to match
        slow_window: Slow window value to match

    Returns:
        bool: True if a matching signal is found, False otherwise
    """
    if not signals:
        return False
    
    return any(
        signal["Short Window"] == fast_window and 
        signal["Long Window"] == slow_window
        for signal in signals
    )

def process_ma_signals(
    ticker: str,
    ma_type: str,
    config: Config,
    fast_window: int,
    slow_window: int
) -> bool:
    """
    Process moving average signals for a given ticker and configuration.

    Args:
        ticker: The ticker symbol to process
        ma_type: Type of moving average ('SMA' or 'EMA')
        config: Configuration dictionary
        fast_window: Fast window value from scanner
        slow_window: Slow window value from scanner

    Returns:
        bool: True if current signal is found, False otherwise
    """
    ma_config = config.copy()
    ma_config.update({
        "TICKER": ticker,
        "USE_SMA": ma_type == "SMA"
    })
    
    signals = generate_current_signals(ma_config)
    
    is_current = check_signal_match(
        signals.to_dicts() if len(signals) > 0 else [], 
        fast_window, 
        slow_window
    )
    
    message = (
        f"{ticker} {ma_type} - {'Current signal found' if is_current else 'No signals'} "
        f"for {fast_window}/{slow_window}{'!!!!!' if is_current else ''}"
    )
    print(message)
    
    return is_current
