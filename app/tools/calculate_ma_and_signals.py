from typing import Callable
import polars as pl
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_rsi import calculate_rsi

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
    direction = "Short" if config.get('SHORT', False) else "Long"
    log(f"Calculating {direction} {ma_type}s and signals with short window {short_window} and long window {long_window}")
    
    try:
        # Calculate moving averages
        data = calculate_mas(data, short_window, long_window, config.get('USE_SMA', False))
        
        # Calculate RSI if needed
        if config.get('USE_RSI', False):
            # Use RSI_WINDOW from config for sensitivity analysis
            rsi_window = config.get('RSI_WINDOW', 14)  # Changed from RSI_PERIOD to RSI_WINDOW
            data = calculate_rsi(data, rsi_window)
        
        # Generate signals based on MA crossovers
        entries, exits = calculate_ma_signals(data, config)
        
        # Add Signal column (-1 for short entry, 1 for long entry, 0 for no signal)
        if config.get('SHORT', False):
            data = data.with_columns([
                pl.when(entries).then(-1).otherwise(0).alias("Signal")
            ])
        else:
            data = data.with_columns([
                pl.when(entries).then(1).otherwise(0).alias("Signal")
            ])
        
        # Add Position column (shifted Signal)
        data = data.with_columns([
            pl.col("Signal").shift(1).alias("Position")
        ])
        
        return data
        
    except Exception as e:
        log(f"Failed to calculate {direction} {ma_type}s and signals: {e}", "error")
        raise
