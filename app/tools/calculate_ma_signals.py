import polars as pl
from typing import Tuple

def calculate_ma_signals(data: pl.DataFrame, config: dict) -> Tuple[pl.Series, pl.Series]:
    """
    Generate entry and exit signals based on the strategy configuration.

    Args:
        data (pl.DataFrame): The input DataFrame containing price and indicator data.
        config (dict): The configuration dictionary.

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing entry and exit signals as NumPy arrays.
    """
    use_rsi = config.get('USE_RSI', False)

    if config.get('SHORT', False):
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
