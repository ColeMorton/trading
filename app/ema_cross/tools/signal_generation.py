import logging
import polars as pl
import numpy as np
import pandas as pd
from typing import List, Dict
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.export_csv import export_csv
from app.ema_cross.tools.signal_types import Config
from app.ema_cross.tools.signal_utils import is_signal_current, check_signal_match

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
                if short < long:  # Ensure short window is always less than long window
                    temp_data = data.clone()
                    temp_data = calculate_ma_and_signals(temp_data, short, long, config)
                    
                    if temp_data is not None and len(temp_data) > 0:
                        current = is_signal_current(temp_data)
                        if current:
                            signals.append({
                                "Short Window": int(short),
                                "Long Window": int(long)
                            })

        # Create DataFrame with explicit schema
        if signals:
            return pl.DataFrame(
                signals,
                schema={
                    "Short Window": pl.Int32,
                    "Long Window": pl.Int32
                }
            )
        return pl.DataFrame(
            schema={
                "Short Window": pl.Int32,
                "Long Window": pl.Int32
            }
        )
    except Exception as e:
        logging.error(f"Failed to get current signals: {e}")
        return pl.DataFrame(
            schema={
                "Short Window": pl.Int32,
                "Long Window": pl.Int32
            }
        )

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

        # Create distinct integer values for windows starting at 2 for both ranges
        short_windows = np.arange(2, config["WINDOWS"])
        long_windows = np.arange(2, config["WINDOWS"])

        data = get_data(config["TICKER"], config)
        if data is None:
            logging.error("Failed to get price data")
            return pl.DataFrame(
                schema={
                    "Short Window": pl.Int32,
                    "Long Window": pl.Int32
                }
            )

        current_signals = get_current_signals(data, short_windows, long_windows, config)

        if not config.get("USE_SCANNER", False):
            export_csv(current_signals, "ma_cross", config, 'current_signals')
            
            if len(current_signals) == 0:
                print("No signals found for today")
        
        return current_signals

    except Exception as e:
        logging.error(f"Failed to generate current signals: {e}")
        return pl.DataFrame(
            schema={
                "Short Window": pl.Int32,
                "Long Window": pl.Int32
            }
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
