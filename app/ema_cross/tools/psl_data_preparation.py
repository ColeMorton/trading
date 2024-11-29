"""
Data preparation module for protective stop loss analysis.

This module handles the preparation of data by calculating technical indicators
and generating entry signals.
"""

import polars as pl
import numpy as np
from typing import Tuple, Callable
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_rsi import calculate_rsi
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.ema_cross.tools.psl_types import PSLConfig

def prepare_data(data: pl.DataFrame, config: PSLConfig, log: Callable) -> Tuple[pl.DataFrame, np.ndarray]:
    """
    Prepare data by calculating technical indicators and generating entry signals.

    Args:
        data (pl.DataFrame): Price data
        config (PSLConfig): Configuration parameters
        log (Callable): Logging function

    Returns:
        Tuple[pl.DataFrame, np.ndarray]: Prepared data and entry signals
    """
    # Calculate moving averages
    data = calculate_mas(
        data, 
        config['SHORT_WINDOW'], 
        config['LONG_WINDOW'], 
        config.get('USE_SMA', False)
    )
    
    # Calculate RSI if enabled
    if config.get("USE_RSI", False):
        data = calculate_rsi(data, config['RSI_PERIOD'])
        log(f"RSI calculated with period {config['RSI_PERIOD']}")
    
    # Generate entry signals
    entries, _ = calculate_ma_signals(data, config)
    entries = entries.to_numpy().astype(bool)
    
    return data, entries
