from typing import Callable, Tuple, Optional, Dict, Any
import polars as pl
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_rsi import calculate_rsi
from app.tools.signal_conversion import convert_signals_to_positions, SignalAudit

def calculate_ma_and_signals(
    data: pl.DataFrame,
    short_window: int,
    long_window: int,
    config: dict,
    log: Callable,
    audit: Optional[SignalAudit] = None
) -> Tuple[pl.DataFrame, SignalAudit]:
    """
    Calculate MAs and generate trading signals.
    
    Args:
        data (pl.DataFrame): Input price data
        short_window (int): Short moving average window
        long_window (int): Long moving average window
        config (dict): Configuration dictionary
        log (Callable): Logging function
        
        audit (Optional[SignalAudit]): Optional audit trail object
        
    Returns:
        Tuple[pl.DataFrame, SignalAudit]:
            - Data with moving averages, signals, and positions
            - Audit trail object with signal conversion tracking
    """
    ma_type = "SMA" if config.get('USE_SMA', False) else "EMA"
    direction = "Short" if config.get('DIRECTION', 'Long') == 'Short' else "Long"
    log(f"Calculating {direction} {ma_type}s and signals with short window {short_window} and long window {long_window}")
    
    try:
        # Calculate moving averages
        data = calculate_mas(data, short_window, long_window, config.get('USE_SMA', False), log)
        
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
        strategy_config["STRATEGY_TYPE"] = "MA Cross"
        strategy_config["SHORT_WINDOW"] = short_window
        strategy_config["LONG_WINDOW"] = long_window
        
        data, signal_audit = convert_signals_to_positions(
            data=data,
            config=strategy_config,
            log=log,
            audit=audit
        )
        
        # Log conversion statistics
        summary = signal_audit.get_summary()
        log(f"Signal conversion: {summary['conversions']} positions from {summary['non_zero_signals']} signals "
            f"({summary['conversion_rate']*100:.1f}% conversion rate)", "info")
        
        return data, signal_audit
        
    except Exception as e:
        log(f"Failed to calculate {direction} {ma_type}s and signals: {e}", "error")
        raise
