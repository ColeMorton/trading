import polars as pl
from typing import Dict, Tuple

def calculate_ma_signals(data: pl.DataFrame, config: Dict) -> Tuple[pl.Series, pl.Series]:
    """
    Generate entry and exit signals based on the strategy configuration.

    Args:
        data (pl.DataFrame): The input DataFrame containing MA_FAST and MA_SLOW columns
        config (Dict): The configuration dictionary containing strategy settings

    Returns:
        Tuple[pl.Series, pl.Series]: Entry and exit signals as polars Series
    """
    use_rsi = config.get('USE_RSI', False)

    if config.get('SHORT', False):
        entries = (pl.col('MA_FAST') < pl.col('MA_SLOW'))
        if use_rsi:
            entries = entries & (pl.col('RSI') <= (100 - config.get('RSI_THRESHOLD', 70)))
        exits = (pl.col('MA_FAST') > pl.col('MA_SLOW'))
    else:
        entries = (pl.col('MA_FAST') > pl.col('MA_SLOW'))
        if use_rsi:
            entries = entries & (pl.col('RSI') >= config.get('RSI_THRESHOLD', 70))
        exits = (pl.col('MA_FAST') < pl.col('MA_SLOW'))
    
    # Apply conditions to DataFrame
    result = data.with_columns([
        entries.alias('entries'),
        exits.alias('exits')
    ])
    
    return result.get_column('entries'), result.get_column('exits')
