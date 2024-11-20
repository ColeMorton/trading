import polars as pl
from typing import Dict, Tuple

def calculate_ma_signals(data: pl.DataFrame, config: Dict) -> Tuple[pl.Series, pl.Series]:
    """
    Generate entry and exit signals based on the strategy configuration.
    Checks for crossovers on the most recent trading day.

    Args:
        data (pl.DataFrame): The input DataFrame containing MA_FAST and MA_SLOW columns
        config (Dict): The configuration dictionary containing strategy settings

    Returns:
        Tuple[pl.Series, pl.Series]: Entry and exit signals as polars Series
    """
    use_rsi = config.get('USE_RSI', False)

    # Get the previous trading day's values
    # shift(1) will give us the last trading day since yfinance only returns trading days
    ma_fast_prev = pl.col('MA_FAST').shift(1)
    ma_slow_prev = pl.col('MA_SLOW').shift(1)
    
    # Get the trading day before that to detect crossover
    ma_fast_prev2 = pl.col('MA_FAST').shift(2)
    ma_slow_prev2 = pl.col('MA_SLOW').shift(2)

    if config.get('SHORT', False):
        # For short positions, check if fast MA crossed below slow MA on the last trading day
        # This means: fast > slow two days ago, and fast < slow on the last trading day
        entries = (ma_fast_prev2 > ma_slow_prev2) & (ma_fast_prev < ma_slow_prev)
        if use_rsi:
            entries = entries & (pl.col('RSI') <= (100 - config.get('RSI_THRESHOLD', 70)))
        exits = (ma_fast_prev2 < ma_slow_prev2) & (ma_fast_prev > ma_slow_prev)
    else:
        # For long positions, check if fast MA crossed above slow MA on the last trading day
        # This means: fast < slow two days ago, and fast > slow on the last trading day
        entries = (ma_fast_prev2 < ma_slow_prev2) & (ma_fast_prev > ma_slow_prev)
        if use_rsi:
            entries = entries & (pl.col('RSI') >= config.get('RSI_THRESHOLD', 70))
        exits = (ma_fast_prev2 > ma_slow_prev2) & (ma_fast_prev < ma_slow_prev)
    
    # Apply conditions to DataFrame
    result = data.with_columns([
        entries.alias('entries'),
        exits.alias('exits')
    ])
    
    return result.get_column('entries'), result.get_column('exits')
