from typing import Callable
import polars as pl
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.tools.calculate_rsi import calculate_rsi

def calculate_macd_and_signals(
    data: pl.DataFrame,
    short_window: int,
    long_window: int,
    signal_window: int,
    config: dict,
    log: Callable
) -> pl.DataFrame:
    """
    Calculate MACD and generate trading signals.
    
    Args:
        data (pl.DataFrame): Input price data
        short_window (int): Fast EMA period
        long_window (int): Slow EMA period
        signal_window (int): Signal line EMA period
        config (dict): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        pl.DataFrame: Data with MACD indicators and signals
    """
    direction = "Short" if config.get('DIRECTION', 'Long') == 'Short' else "Long"
    log(f"Calculating {direction} MACD and signals with fast period {short_window}, slow period {long_window}, and signal period {signal_window}")
    
    try:
        # Calculate MACD
        data = calculate_macd(data, short_window, long_window, signal_window)
        
        # Calculate RSI if needed
        if config.get('RSI_WINDOW') and config.get('RSI_THRESHOLD'):
            rsi_period = config.get('RSI_WINDOW', 14)
            data = calculate_rsi(data, rsi_period)
        
        # Generate signals based on MACD crossovers
        is_short = config.get('DIRECTION', 'Long') == 'Short'
        data = calculate_macd_signals(data, is_short)
        
        # Add Position column (shifted Signal)
        data = data.with_columns([
            pl.col("Signal").shift(1).alias("Position")
        ])
        
        return data
        
    except Exception as e:
        log(f"Failed to calculate {direction} MACD and signals: {e}", "error")
        raise