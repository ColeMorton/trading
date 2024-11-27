import numpy as np
from typing import Dict, Callable

from app.utils import get_filename, get_path
from app.ema_cross.tools.create_heatmaps import create_full_heatmap, create_current_heatmap
from app.ema_cross.tools.heatmap_data import prepare_heatmap_data, validate_window_combinations

def plot_heatmap(results_pl, config: Dict, log: Callable) -> None:
    """
    Plot heatmaps of MA cross strategy performance.
    
    Creates either full heatmaps of all possible window combinations or focused
    heatmaps showing only current signal combinations based on configuration.
    Uses Polars for data processing where possible, converting to Pandas only
    when required for vectorbt operations.

    Args:
        results_pl: Polars DataFrame containing price data with Date/Datetime and Close columns
        config: Configuration dictionary containing:
            - TICKER: str, ticker symbol
            - WINDOWS: int, maximum window size to test
            - USE_SMA: bool, whether to use SMA instead of EMA
            - USE_CURRENT: bool, whether to show only current signals
        log: Logging function for recording events and errors

    Returns:
        None. Saves the plots to files and displays them.
    """
    # Prepare data
    price_data, window_combs, use_ewm = prepare_heatmap_data(results_pl, config, log)
    if price_data is None:
        log("Failed to prepare heatmap data", "error")
        return

    # Generate windows array
    windows = np.arange(2, config["WINDOWS"])
    
    # Create appropriate heatmaps
    if config.get("USE_CURRENT", False) and validate_window_combinations(window_combs, windows, config, log):
        window_combs = list(window_combs)  # Convert set to list before sorting
        window_combs.sort()
        figures = create_current_heatmap(
            price_data, 
            windows, 
            window_combs, 
            use_ewm,
            ticker=config["TICKER"]
        )
    else:
        figures = create_full_heatmap(
            price_data, 
            windows, 
            use_ewm,
            ticker=config["TICKER"]
        )
    
    # Save and display plots
    png_path = get_path("png", "ema_cross", config, 'heatmap')
    base_filename = get_filename("png", config).replace('.png', '')
    
    for plot_type, fig in figures.items():
        filename = f"{base_filename}_{plot_type}.png"
        full_path = f"{png_path}/{filename}"
        fig.write_image(full_path)
        log(f"{plot_type.capitalize()} plot saved as {full_path}")
        fig.show()
