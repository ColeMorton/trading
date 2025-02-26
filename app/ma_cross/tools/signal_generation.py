import polars as pl
import numpy as np
from typing import List, Dict, Callable
from datetime import datetime
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.export_csv import export_csv
from app.ma_cross.tools.signal_types import Config
from app.ma_cross.tools.signal_utils import is_signal_current, check_signal_match

def get_current_signals(
    data: pl.DataFrame,
    short_windows: List[int],
    long_windows: List[int],
    config: Dict,
    log: Callable
) -> pl.DataFrame:
    """
    Get current signals for all window combinations.
    
    Args:
        data: Price data DataFrame
        short_windows: List of short window periods
        long_windows: List of long window periods
        config: Configuration dictionary
        log: Logging function for recording events and errors
    
    Returns:
        DataFrame containing window combinations with current signals
    """
    try:
        signals = []
        
        for short in short_windows:
            for long in long_windows:
                if short < long:  # Ensure short window is always less than long window
                    try:
                        temp_data = data.clone()
                        temp_data = calculate_ma_and_signals(temp_data, short, long, config, log)
                        
                        if temp_data is not None and len(temp_data) > 0:
                            # Check if required columns exist
                            if "Signal" in temp_data.columns and "Position" in temp_data.columns:
                                current = is_signal_current(temp_data)
                                if current:
                                    signals.append({
                                        "Short Window": int(short),
                                        "Long Window": int(long)
                                    })
                    except Exception as e:
                        log(f"Error processing window combination {short}/{long}: {str(e)}", "warning")
                        continue

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
        log(f"Failed to get current signals: {e}", "error")
        return pl.DataFrame(
            schema={
                "Short Window": pl.Int32,
                "Long Window": pl.Int32
            }
        )

def generate_current_signals(config: Config, log: Callable) -> pl.DataFrame:
    """
    Generate current signals for a given configuration.
    
    Args:
        config: Configuration dictionary
        log: Logging function for recording events and errors
    
    Returns:
        DataFrame containing current signals
    """
    try:
        from app.ma_cross.tools.signal_utils import set_last_trading_day
        
        config = get_config(config)
        config_copy = config.copy()
        config_copy["USE_CURRENT"] = True  # Ensure holiday check is enabled
        
        # Get data for the actual ticker first to determine last trading day
        try:
            data_result = get_data(config["TICKER"], config_copy, log)
            if isinstance(data_result, tuple):
                data, _ = data_result
            else:
                data = data_result
                
            if data is None or data.is_empty():
                log("Failed to get price data or data is empty", "error")
                return pl.DataFrame(
                    schema={
                        "Short Window": pl.Int32,
                        "Long Window": pl.Int32
                    }
                )
        except Exception as e:
            log(f"Error retrieving data: {str(e)}", "error")
            return pl.DataFrame(
                schema={
                    "Short Window": pl.Int32,
                    "Long Window": pl.Int32
                }
            )
            
        # Set the last trading day from the data
        last_date = data["Date"].max()
        if isinstance(last_date, datetime):
            last_date = last_date.date()
        elif isinstance(last_date, str):
            try:
                # Try parsing with timestamp first
                last_date = datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                try:
                    # Try parsing with just date if timestamp fails
                    last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
                except ValueError:
                    # Try parsing ISO format if both above fail
                    last_date = datetime.fromisoformat(last_date).date()
        
        log(f"Using last trading day: {last_date}")
        set_last_trading_day(last_date)
        
        # Check if specific windows are provided
        short_window = config.get("SHORT_WINDOW")
        long_window = config.get("LONG_WINDOW")
        
        if short_window is not None and long_window is not None:
            # Use specific windows from config
            current_signals = get_current_signals(data, [short_window], [long_window], config, log)
        else:
            # Use window permutations if WINDOWS is provided
            windows = config.get("WINDOWS")
            if windows is None or windows < 2:
                log("Missing or invalid WINDOWS parameter", "error")
                return pl.DataFrame(
                    schema={
                        "Short Window": pl.Int32,
                        "Long Window": pl.Int32
                    }
                )
            
            # Create distinct integer values for windows
            short_windows = list(np.arange(2, windows))
            long_windows = list(np.arange(2, windows))
            current_signals = get_current_signals(data, short_windows, long_windows, config, log)

        if not config.get("USE_SCANNER", False):
            export_csv(current_signals, "ma_cross", config, 'current_signals')
            
            if len(current_signals) == 0:
                print("No signals found for today")
        
        return current_signals

    except Exception as e:
        log(f"Failed to generate current signals: {e}", "error")
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
    slow_window: int,
    log: Callable
) -> bool:
    """
    Process moving average signals for a given ticker and configuration.

    Args:
        ticker: The ticker symbol to process
        ma_type: Type of moving average ('SMA' or 'EMA')
        config: Configuration dictionary
        fast_window: Fast window value from scanner
        slow_window: Slow window value from scanner
        log: Logging function for recording events and errors

    Returns:
        bool: True if current signal is found, False otherwise
    """
    ma_config = config.copy()
    ma_config.update({
        "TICKER": ticker,
        "USE_SMA": ma_type == "SMA",
        "SHORT_WINDOW": fast_window,
        "LONG_WINDOW": slow_window
    })
    
    signals = generate_current_signals(ma_config, log)
    
    is_current = check_signal_match(
        signals.to_dicts() if len(signals) > 0 else [], 
        fast_window, 
        slow_window
    )
    
    return is_current
