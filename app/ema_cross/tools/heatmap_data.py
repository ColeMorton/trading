import logging
from typing import Dict, Optional, Tuple
import polars as pl
import pandas as pd

from app.tools.file_utils import get_current_window_combinations, is_file_from_today
from app.ema_cross.tools.prepare_price_data import prepare_price_data
from app.ema_cross.tools.signal_generation import generate_current_signals

def prepare_heatmap_data(
    results_pl: pl.DataFrame,
    config: Dict
) -> Tuple[Optional[pd.DataFrame], Optional[list], Optional[bool]]:
    """
    Prepare data for heatmap visualization.

    Args:
        results_pl: Polars DataFrame containing price data
        config: Configuration dictionary

    Returns:
        Tuple containing:
        - price_data: Pandas DataFrame prepared for vectorbt
        - window_combs: List of window combinations (for current signals)
        - use_ewm: Boolean indicating whether to use EMA
    """
    try:
        price_data = prepare_price_data(results_pl, config["TICKER"])
        use_ewm = not config.get("USE_SMA", False)
        window_combs = None

        if config.get("USE_CURRENT", False):
            filename = f"{config['TICKER']}_D_{'SMA' if config.get('USE_SMA', False) else 'EMA'}.csv"
            filepath = f"csv/ma_cross/current_signals/{filename}"
            
            if not is_file_from_today(filepath):
                logging.info(f"Generating new signals for {config['TICKER']}")
                generate_current_signals(config)
            
            window_combs = get_current_window_combinations(filepath)
            
            if window_combs is None:
                logging.info(f"Falling back to full heatmap for {config['TICKER']}")
                config["USE_CURRENT"] = False

        return price_data, window_combs, use_ewm

    except Exception as e:
        logging.error(f"Failed to prepare heatmap data: {e}")
        return None, None, None

def validate_window_combinations(
    window_combs: list,
    windows: list,
    config: Dict
) -> bool:
    """
    Validate window combinations for current signal heatmap.

    Args:
        window_combs: List of window combinations
        windows: List of window values
        config: Configuration dictionary

    Returns:
        bool: True if combinations are valid, False otherwise
    """
    if window_combs is None:
        return False

    valid_combs = [(short, long) for short, long in window_combs 
                   if short in windows and long in windows]
    
    if not valid_combs:
        logging.warning(f"No valid window combinations found for {config['TICKER']}")
        config["USE_CURRENT"] = False
        return False
        
    return True
