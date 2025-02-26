from typing import Callable
import polars as pl
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals, verify_current_signals
from app.tools.calculate_rsi import calculate_rsi
from app.tools.data_validation import validate_data

def calculate_ma_and_signals(
    data: pl.DataFrame,
    short_window: int,
    long_window: int,
    config: dict,
    log: Callable
) -> pl.DataFrame:
    """
    Calculate MAs and generate trading signals.
    
    Args:
        data (pl.DataFrame): Input price data
        short_window (int): Short moving average window
        long_window (int): Long moving average window
        config (dict): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        pl.DataFrame: Data with moving averages and signals
    """
    ma_type = "SMA" if config.get('USE_SMA', False) else "EMA"
    direction = "Short" if config.get('DIRECTION', 'Long') == 'Short' else "Long"
    log(f"Calculating {direction} {ma_type}s and signals with short window {short_window} and long window {long_window}")
    
    try:
        # Always validate and clean data first
        data = validate_data(data, config, log)
        
        # Calculate moving averages
        data = calculate_mas(data, short_window, long_window, config.get('USE_SMA', False), log)
        
        # Calculate RSI if needed
        if config.get('USE_RSI', False):
            # Use RSI_WINDOW from config for sensitivity analysis
            rsi_window = config.get('RSI_WINDOW', 14)
            data = calculate_rsi(data, rsi_window)
        
        # Generate signals based on MA crossovers
        entries, exits = calculate_ma_signals(data, config)
        
        # Add Signal column (-1 for short entry, 1 for long entry, 0 for no signal)
        direction_multiplier = -1 if config.get('DIRECTION', 'Long') == 'Short' else 1
        data = data.with_columns([
            pl.when(entries).then(direction_multiplier).otherwise(0).alias("Signal")
        ])
        
        # Add Position column (shifted Signal)
        data = data.with_columns([
            pl.col("Signal").shift(1).alias("Position")
        ])
        
        # Verify current signals if USE_CURRENT is True
        if config.get('USE_CURRENT', False):
            verify_current_signals(data, config, log)
        
        return data
        
    except Exception as e:
        log(f"Failed to calculate {direction} {ma_type}s and signals: {e}", "error")
        raise
