import polars as pl
from typing import Dict, Tuple, Callable
from app.tools.data_validation import validate_signals

def calculate_ma_signals(data: pl.DataFrame, config: Dict) -> Tuple[pl.Series, pl.Series]:
    """
    Generate entry and exit signals based on the strategy configuration.
    When USE_CURRENT is True, signals are only generated for crossovers on the last candle.
    Otherwise, signals are generated when the fast MA is above/below the slow MA.

    Args:
        data (pl.DataFrame): The input DataFrame containing MA_FAST and MA_SLOW columns
        config (Dict): The configuration dictionary containing strategy settings

    Returns:
        Tuple[pl.Series, pl.Series]: Entry and exit signals as polars Series
    """
    use_rsi = config.get('USE_RSI', False)
    use_current = config.get('USE_CURRENT', False)

    # Get MA values
    ma_fast = pl.col('MA_FAST')
    ma_slow = pl.col('MA_SLOW')
    
    # Always calculate crossovers accurately regardless of USE_CURRENT setting
    # Current MA relationship
    ma_fast_gt_slow = ma_fast > ma_slow
    ma_fast_lt_slow = ma_fast < ma_slow
    
    # Previous MA relationship (shift forward by 1)
    prev_ma_fast_gt_slow = ma_fast_gt_slow.shift(1)
    prev_ma_fast_lt_slow = ma_fast_lt_slow.shift(1)
    
    # For long positions
    if config.get('DIRECTION', 'Long') == 'Long':
        # Accurate crossover detection: Fast MA crosses above Slow MA
        entries = ma_fast_gt_slow & ~prev_ma_fast_gt_slow
        
        # If not using current crossovers, also include when fast MA is already above slow MA
        if not use_current:
            entries = entries | ma_fast_gt_slow
            
        # Exit when fast MA crosses below slow MA
        exits = ma_fast_lt_slow & ~prev_ma_fast_lt_slow
    else:
        # For short positions
        # Accurate crossover detection: Fast MA crosses below Slow MA
        entries = ma_fast_lt_slow & ~prev_ma_fast_lt_slow
        
        # If not using current crossovers, also include when fast MA is already below slow MA
        if not use_current:
            entries = entries | ma_fast_lt_slow
            
        # Exit when fast MA crosses above slow MA
        exits = ma_fast_gt_slow & ~prev_ma_fast_gt_slow
    
    # Apply RSI filter if configured
    if use_rsi:
        rsi_threshold = config.get('RSI_THRESHOLD', 70)
        if config.get('DIRECTION', 'Long') == 'Long':
            entries = entries & (pl.col('RSI') >= rsi_threshold)
        else:
            entries = entries & (pl.col('RSI') <= (100 - rsi_threshold))
    
    # Validate signals to ensure no false positives
    entries = validate_signals(entries, data, config)
    
    # Apply conditions to DataFrame
    result = data.with_columns([
        entries.alias('entries'),
        exits.alias('exits')
    ])
    
    return result.get_column('entries'), result.get_column('exits')

def verify_current_signals(data: pl.DataFrame, config: Dict, log: Callable) -> None:
    """
    Verify that current signals are accurate by checking the actual crossover conditions.
    
    Args:
        data: DataFrame with price and signal data
        config: Configuration dictionary
        log: Logging function
    """
    # Only verify if USE_CURRENT is True
    if not config.get('USE_CURRENT', False):
        return
    
    # Get the last few rows of data
    last_rows = data.tail(5)
    
    # Check if there are any signals in the last few rows
    signals = last_rows.filter(pl.col('Signal') != 0)
    
    if len(signals) > 0:
        log("Verifying current signals:")
        for i, row in enumerate(signals.to_dicts()):
            date = row['Date']
            signal = row['Signal']
            ma_fast = row['MA_FAST']
            ma_slow = row['MA_SLOW']
            
            # Get previous row's MAs if available
            prev_idx = i - 1
            if prev_idx >= 0:
                prev_row = signals.row(prev_idx)
                prev_ma_fast = prev_row[signals.columns.index('MA_FAST')]
                prev_ma_slow = prev_row[signals.columns.index('MA_SLOW')]
                
                # Verify crossover
                if signal > 0:  # Long signal
                    is_valid = ma_fast > ma_slow and prev_ma_fast <= prev_ma_slow
                    log(f"Long signal at {date}: {'Valid' if is_valid else 'Invalid'} crossover")
                    log(f"  Current: Fast MA={ma_fast:.2f}, Slow MA={ma_slow:.2f}")
                    log(f"  Previous: Fast MA={prev_ma_fast:.2f}, Slow MA={prev_ma_slow:.2f}")
                elif signal < 0:  # Short signal
                    is_valid = ma_fast < ma_slow and prev_ma_fast >= prev_ma_slow
                    log(f"Short signal at {date}: {'Valid' if is_valid else 'Invalid'} crossover")
                    log(f"  Current: Fast MA={ma_fast:.2f}, Slow MA={ma_slow:.2f}")
                    log(f"  Previous: Fast MA={prev_ma_fast:.2f}, Slow MA={prev_ma_slow:.2f}")
            else:
                log(f"Signal at {date}: Cannot verify (no previous data)")
    else:
        log("No current signals to verify")
