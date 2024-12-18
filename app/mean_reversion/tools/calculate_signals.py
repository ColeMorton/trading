"""
Mean Reversion Signal Calculator

This module calculates entry and exit signals for mean reversion strategy based on:
- Entry: Price close <= price close 1 candle ago by at least X%
- Exit: After Y number of candles
"""

import polars as pl
from typing import Dict, Any, Tuple
from typing_extensions import TypedDict

class SignalConfig(TypedDict):
    """Configuration type definition.

    Required Fields:
        PRICE_CHANGE_PCT (float): Minimum price decrease percentage for entry
        EXIT_CANDLES (int): Number of candles to hold position before exit
        DIRECTION (str): Trading direction ('Long' or 'Short')
    """
    PRICE_CHANGE_PCT: float
    EXIT_CANDLES: int
    DIRECTION: str

def calculate_signals(
    data: pl.DataFrame,
    config: SignalConfig
) -> Tuple[pl.Series, pl.Series]:
    """
    Calculate entry and exit signals for mean reversion strategy.

    Args:
        data (pl.DataFrame): Price data with 'Close' column
        config (SignalConfig): Strategy configuration parameters

    Returns:
        Tuple[pl.Series, pl.Series]: Entry and exit signals as polars Series:
            - entries: Series of entry signals (1 for long, -1 for short)
            - exits: Series of exit signals (True when position should be closed)

    Raises:
        ValueError: If invalid direction specified in config
    """
    if config['DIRECTION'] not in ['Long', 'Short']:
        raise ValueError("DIRECTION must be either 'Long' or 'Short'")

    # Calculate price change percentage
    df = data.with_columns([
        ((pl.col('Close') - pl.col('Close').shift(1)) / pl.col('Close').shift(1) * 100).alias('price_change_pct')
    ])

    # Generate entry conditions based on price change threshold
    if config['DIRECTION'] == 'Long':
        entries = pl.when(pl.col('price_change_pct') <= -config['PRICE_CHANGE_PCT']).then(1).otherwise(0)
    else:  # Short
        entries = pl.when(pl.col('price_change_pct') >= config['PRICE_CHANGE_PCT']).then(-1).otherwise(0)

    # Convert to pandas for position tracking and exit signal generation
    # (Required since we need to track position duration)
    pdf = df.to_pandas()
    position_duration = 0
    in_position = False
    exits_list = [False] * len(pdf)
    
    for i in range(len(pdf)):
        if pdf.iloc[i]['price_change_pct'] <= -config['PRICE_CHANGE_PCT'] and not in_position:
            in_position = True
            position_duration = 1
        elif in_position:
            position_duration += 1
            if position_duration >= config['EXIT_CANDLES']:
                exits_list[i] = True
                in_position = False
                position_duration = 0

    # Create exits Series
    exits = pl.Series(name="exits", values=exits_list)

    # Apply conditions to DataFrame and return columns
    result = df.with_columns([
        entries.alias('entries'),
        exits.alias('exits')
    ])
    
    return result.get_column('entries'), result.get_column('exits')
