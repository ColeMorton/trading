import logging
from typing import Dict, Optional, Tuple
import polars as pl
import pandas as pd
import os
import sys

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

    Exits:
        If USE_CURRENT is True and no signals are found for today
    """
    try:
        price_data = prepare_price_data(results_pl, config["TICKER"])
        use_ewm = not config.get("USE_SMA", False)
        window_combs = None

        if config.get("USE_CURRENT", False):
            # Determine filename and filepath
            filename = f"{config['TICKER']}_D_{'SMA' if config.get('USE_SMA', False) else 'EMA'}.csv"
            filepath = f"csv/ma_cross/current_signals/{filename}"
            
            # Generate new signals if:
            # 1. REFRESH is True
            # 2. OR for daily data (not hourly), file is not from today
            # 3. OR file doesn't exist
            should_generate = (
                config.get("REFRESH", False) or
                (not config.get("USE_HOURLY", False) and not is_file_from_today(filepath)) or
                not os.path.exists(filepath)
            )
            
            if should_generate:
                reason = "REFRESH=True" if config.get("REFRESH", False) else \
                        "daily data needs refresh" if not config.get("USE_HOURLY", False) else \
                        "file doesn't exist"
                logging.info(f"Generating new signals for {config['TICKER']} ({reason})")
                generate_current_signals(config)
            
            # Get window combinations from the file
            window_combs = get_current_window_combinations(filepath)
            
            # Exit if no signals found
            if window_combs is None or len(window_combs) == 0:
                message = f"No signals found for {config['TICKER']} {'SMA' if config['USE_SMA'] else 'EMA'}"
                logging.info(message)
                print(message)
                sys.exit(0)

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

    Exits:
        If no valid window combinations are found
    """
    if window_combs is None or len(window_combs) == 0:
        logging.info(f"No valid window combinations found for {config['TICKER']}")
        print(f"No valid window combinations found for {config['TICKER']}")
        sys.exit(0)

    # Convert window_combs to a list of tuples if it's not already
    if isinstance(window_combs, set):
        window_combs = list(window_combs)

    # Ensure each combination is valid and within the windows range
    valid_combs = []
    for short, long in window_combs:
        if short in windows and long in windows and short < long:
            valid_combs.append((short, long))
    
    if not valid_combs:
        logging.warning(f"No valid window combinations found for {config['TICKER']}")
        print(f"No valid window combinations found for {config['TICKER']}")
        sys.exit(0)

    # Update the window_combs in place with only valid combinations
    window_combs.clear()
    window_combs.extend(valid_combs)
        
    return True
