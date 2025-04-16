from typing import Callable, Optional, Dict, Any
import polars as pl
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_rsi import calculate_rsi
from app.tools.signal_conversion import convert_signals_to_positions

def calculate_ma_and_signals(
    data: pl.DataFrame,
    short_window: int,
    long_window: int,
    config: dict,
    log: Callable,
    strategy_type: str = "EMA"
) -> pl.DataFrame:
    """
    Calculate MAs and generate trading signals.
    
    Args:
        data (pl.DataFrame): Input price data
        short_window (int): Short moving average window
        long_window (int): Long moving average window
        config (dict): Configuration dictionary
        log (Callable): Logging function
        strategy_type (str, optional): Strategy type to use (SMA or EMA). Defaults to "EMA".
        
    Returns:
        pl.DataFrame: Data with moving averages, signals, and positions
    """
    direction = "Short" if config.get('DIRECTION', 'Long') == 'Short' else "Long"
    log(f"Calculating {direction} {strategy_type}s and signals with short window {short_window} and long window {long_window}")
    
    try:
        # Calculate moving averages
        use_sma = strategy_type == "SMA"
        data = calculate_mas(data, short_window, long_window, use_sma, log)
        
        # Calculate RSI if needed
        if config.get('USE_RSI', False):
            # Use RSI_WINDOW from config for RSI calculation
            rsi_period = config.get('RSI_WINDOW', 14)
            data = calculate_rsi(data, rsi_period)
            log(f"Calculated RSI with period {rsi_period}", "info")
        
        # Generate signals based on MA crossovers
        entries, exits = calculate_ma_signals(data, config)
        
        # Add Signal column (-1 for short entry, 1 for long entry, 0 for no signal)
        if config.get('DIRECTION', 'Long') == 'Short':
            data = data.with_columns([
                pl.when(entries).then(-1).otherwise(0).alias("Signal")
            ])
        else:
            data = data.with_columns([
                pl.when(entries).then(1).otherwise(0).alias("Signal")
            ])
        
        # Convert signals to positions with audit trail
        strategy_config = config.copy()
        strategy_config["STRATEGY_TYPE"] = strategy_type
        strategy_config["SHORT_WINDOW"] = short_window
        strategy_config["LONG_WINDOW"] = long_window
        data = convert_signals_to_positions(
            data=data,
            config=strategy_config,
            log=log
        )

        return data
        
    except Exception as e:
        log(f"Failed to calculate {direction} {strategy_type}s and signals: {e}", "error")
        raise
