import logging
from typing import Dict

import numpy as np
import polars as pl

from app.utils import get_filename, get_path
from app.ema_cross.tools.create_full_heatmap import create_full_heatmap
from app.ema_cross.tools.create_current_heatmap import create_current_heatmap
from app.ema_cross.tools.get_current_window_combinations import get_current_window_combinations
from app.ema_cross.tools.prepare_price_data import prepare_price_data
from app.ema_cross.tools.generate_current_signals import generate_current_signals
from app.ema_cross.tools.is_file_from_today import is_file_from_today

def plot_heatmap(results_pl: pl.DataFrame, config: Dict) -> None:
    """
    Plot heatmap of MA cross strategy performance.
    
    Creates either a full heatmap of all possible window combinations or a focused
    heatmap showing only current signal combinations based on configuration.
    Uses Polars for data processing where possible, converting to Pandas only
    when required for vectorbt operations.

    Args:
        results_pl: Polars DataFrame containing price data with Date/Datetime and Close columns
        config: Configuration dictionary containing:
            - TICKER: str, ticker symbol
            - WINDOWS: int, maximum window size to test
            - USE_SMA: bool, whether to use SMA instead of EMA
            - USE_CURRENT: bool, whether to show only current signals

    Returns:
        None. Saves the plot to a file and displays it.
    """
    price_data = prepare_price_data(results_pl, config["TICKER"])
    windows = np.arange(2, config["WINDOWS"])
    use_ewm = not config.get("USE_SMA", False)
    ma_type = "SMA" if config.get("USE_SMA", False) else "EMA"
    
    if config.get("USE_CURRENT", False):
        filename = f"{config['TICKER']}_D_{ma_type}.csv"
        filepath = f"csv/ma_cross/current_signals/{filename}"
        
        # Check if file exists and was created today
        if not is_file_from_today(filepath):
            logging.info(f"Generating new signals for {config['TICKER']}")
            generate_current_signals(config)
        
        current_windows = get_current_window_combinations(filepath)
        if current_windows is None:
            logging.info(f"Falling back to full heatmap for {config['TICKER']}")
            config["USE_CURRENT"] = False
        else:
            window_combs = [(short, long) for short, long in current_windows 
                           if short in windows and long in windows]
            if not window_combs:
                logging.warning(f"No valid window combinations found for {config['TICKER']}")
                config["USE_CURRENT"] = False
            else:
                window_combs.sort()
                fig = create_current_heatmap(price_data, windows, window_combs, use_ewm)
                title_suffix = "Current Signals Only"
    
    if not config.get("USE_CURRENT", False):
        fig = create_full_heatmap(price_data, windows, use_ewm)
        title_suffix = "All Signals"
    
    # Update layout
    fig.update_layout(
        title=f'{config["TICKER"]} {ma_type} Cross Strategy Returns ({title_suffix})',
        xaxis_title='Short Window',
        yaxis_title='Long Window'
    )
    
    # Save plot
    png_path = get_path("png", "ema_cross", config, 'heatmap')
    png_filename = get_filename("png", config)
    full_path = f"{png_path}/{png_filename}"
    
    fig.write_image(full_path)
    logging.info(f"Plot saved as {full_path}")
    fig.show()
