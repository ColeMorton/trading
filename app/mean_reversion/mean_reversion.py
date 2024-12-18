"""
Parameter Sensitivity Analysis Module for Mean Reversion Strategy

This module performs sensitivity analysis on price change and relative volume parameters.
It analyzes how different price movement percentages and relative volume ratios affect strategy performance metrics.
"""

import os
import numpy as np
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.tools.cache_utils import (
    get_cache_filepath,
    load_cached_analysis
)
from app.mean_reversion.tools.heatmap import analyze_parameters
from app.mean_reversion.tools.visualization import create_heatmap

default_config = {
    "TICKER": "BTC-USD",
    "BASE_DIR": ".",
    "REFRESH": True,
    "USE_HOURLY": True,
    "DIRECTION": "Short"
}

def run(config) -> bool:
    """
    Run parameter sensitivity analysis.

    This function performs sensitivity analysis on price change and relative volume parameters by:
    1. Setting up logging
    2. Loading cached results or preparing new data
    3. Running sensitivity analysis across parameters
    4. Displaying interactive heatmaps in browser

    Args:
        config (CacheConfig): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If data preparation or analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='mean_reversion',
        log_file='mean_reversion.log'
    )
    
    try:
        config = get_config(config)
        log(f"Starting Mean Reversion analysis for {config['TICKER']}")
        
        # Define parameter ranges
        change_range = np.arange(0, 20.1, 0.1)
        rvol_range = np.arange(0, 3.1, 0.1)
        log(f"Using price change range: {change_range[0]} to {change_range[-1]}")
        log(f"Using relative volume range: {rvol_range[0]} to {rvol_range[-1]}")

        # Check for cached results
        cache_dir, cache_file = get_cache_filepath(config, 'mean_reversion')
        cache_path = os.path.join(cache_dir, cache_file)
        metric_matrices = None
        
        if not config.get("REFRESH", False):
            metric_matrices = load_cached_analysis(
                filepath=cache_path,
                param_range=change_range,
                param_column='Price Change Range',
                param_range_2=rvol_range,
                param_column_2='RVOL Range'
            )
            if metric_matrices is not None:
                log("Using cached RSI analysis results")
        
        # If no cache or refresh requested, run new analysis
        if metric_matrices is None:
            log("Running new mean reversion analysis")
            data = get_data(config["TICKER"], config, log)
            metric_matrices = analyze_parameters(
                data=data,
                config=config,
                change_range=change_range,
                rvol_range=rvol_range,
                log=log
            )
        
        if metric_matrices is None:
            raise Exception("Failed to generate or load metric matrices")
            
        # Create heatmap figures
        figures = create_heatmap(
            metric_matrices=metric_matrices,
            change_range=change_range,
            rvol_range=rvol_range,
            ticker=str(config["TICKER"]),
            config=config # Pass config to create_heatmap
        )
        
        if not figures:
            raise Exception("Failed to create heatmap figures")
            
        # Display all heatmaps in specific order
        metrics_to_display = ['trades', 'returns', 'sharpe_ratio', 'win_rate']
        for metric_name in metrics_to_display:
            if metric_name in figures:
                figures[metric_name].show()
                log(f"Displayed {metric_name} heatmap")
            else:
                raise Exception(f"Required {metric_name} heatmap not found in figures dictionary")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Error during mean reversion analysis: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run(default_config)
        if result:
            print("Mean reversion analysis completed successfully!")
    except Exception as e:
        print(f"Mean reversion analysis failed: {str(e)}")
        raise
