import logging
import numpy as np
from typing import Dict

from app.utils import get_filename, get_path
from app.ema_cross.tools.create_heatmaps import create_full_heatmap, create_current_heatmap
from app.ema_cross.tools.heatmap_data import prepare_heatmap_data, validate_window_combinations

def plot_heatmap(results_pl, config: Dict) -> None:
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
    # Prepare data
    price_data, window_combs, use_ewm = prepare_heatmap_data(results_pl, config)
    if price_data is None:
        logging.error("Failed to prepare heatmap data")
        return

    # Generate windows array
    windows = np.arange(2, config["WINDOWS"])
    ma_type = "SMA" if config.get("USE_SMA", False) else "EMA"
    
    # Create appropriate heatmap
    if config.get("USE_CURRENT", False) and validate_window_combinations(window_combs, windows, config):
        window_combs = list(window_combs)  # Convert set to list before sorting
        window_combs.sort()
        fig = create_current_heatmap(price_data, windows, window_combs, use_ewm)
        title_suffix = "Current Signals Only"
    else:
        fig = create_full_heatmap(price_data, windows, use_ewm)
        title_suffix = "All Signals"
    
    # Update layout
    timeframe = "H" if config.get("USE_HOURLY", False) else "D"
    fig.update_layout(
        title=f'{config["TICKER"]} {timeframe} {ma_type} Cross Strategy Returns ({title_suffix})',
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
