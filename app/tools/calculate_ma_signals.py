import polars as pl
from typing import Tuple

def calculate_ma_signals(data: pl.DataFrame, config: dict) -> Tuple[pl.Series, pl.Series]:
    """Calculate entry and exit signals based on MA crossover."""
    use_rsi = config.get('USE_RSI', False)

    if config['SHORT']:
        entries = (data['MA_FAST'] < data['MA_SLOW'])
        if use_rsi:
            entries = entries & (data['RSI'] <= (100 - config['RSI_THRESHOLD']))
        exits = data['MA_FAST'] > data['MA_SLOW']
    else:
        entries = (data['MA_FAST'] > data['MA_SLOW'])
        if use_rsi:
            entries = entries & (data['RSI'] >= config['RSI_THRESHOLD'])
        exits = data['MA_FAST'] < data['MA_SLOW']
    
    return entries, exits
