"""
RSI Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on RSI (Relative Strength Index) parameters
in combination with EMA cross signals. It analyzes how different RSI thresholds and
window lengths affect strategy performance metrics.
"""

import os
import numpy as np
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.tools.cache_utils import (
    CacheConfig,
    get_cache_filepath,
    load_cached_analysis
)
from app.ma_cross.tools.rsi_heatmap import analyze_rsi_parameters
from app.ma_cross.tools.rsi_visualization import create_rsi_heatmap

# Use CacheConfig from cache_utils.py
default_config: CacheConfig = {
    "TICKER": 'OHM-USD',
    "SHORT_WINDOW": 53,
    "LONG_WINDOW": 89,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "REFRESH": True,
    "USE_HOURLY": True,
    "RELATIVE": True,
    "DIRECTION": "Short",
    "USE_CURRENT": False
}

def run(config: CacheConfig) -> bool:
    """
    Run RSI parameter sensitivity analysis.

    This function performs sensitivity analysis on RSI parameters by:
    1. Setting up logging
    2. Loading cached results or preparing new data
    3. Running sensitivity analysis across RSI parameters
    4. Displaying interactive heatmaps in browser

    Args:
        config (CacheConfig): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If data preparation or analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_review_rsi.log'
    )
    
    try:
        config = get_config(config)
        log(f"Starting RSI analysis for {config['TICKER']}")
        
        # Define parameter ranges
        rsi_thresholds = np.arange(30, 81, 1)  # 30 to 80
        # rsi_thresholds = np.arange(30, 33, 1)  # TESTING
        # rsi_thresholds = np.arange(78, 81, 1)  # TESTING
        rsi_windows = np.arange(2, 31, 1)      # 2 to 30
        log(f"Using RSI thresholds: {rsi_thresholds[0]} to {rsi_thresholds[-1]}")
        log(f"Using RSI windows: {rsi_windows[0]} to {rsi_windows[-1]}")

        # Check for cached results
        cache_dir, cache_file = get_cache_filepath(config, 'rsi')
        cache_path = os.path.join(cache_dir, cache_file)
        metric_matrices = None
        
        if not config.get("REFRESH", False):
            metric_matrices = load_cached_analysis(
                filepath=cache_path,
                param_range=rsi_thresholds,
                param_column='RSI Threshold',
                param_range_2=rsi_windows,
                param_column_2='RSI Window'
            )
            if metric_matrices is not None:
                log("Using cached RSI analysis results")
        
        # If no cache or refresh requested, run new analysis
        if metric_matrices is None:
            log("Running new RSI analysis")
            data = get_data(config["TICKER"], config, log)
            metric_matrices = analyze_rsi_parameters(
                data=data,
                config=config,
                rsi_thresholds=rsi_thresholds,
                rsi_windows=rsi_windows,
                log=log
            )
        
        if metric_matrices is None:
            raise Exception("Failed to generate or load metric matrices")
            
        # Create heatmap figures
        figures = create_rsi_heatmap(
            metric_matrices=metric_matrices,
            rsi_thresholds=rsi_thresholds,
            rsi_windows=rsi_windows,
            ticker=str(config["TICKER"]),
            config=config # Pass config to create_rsi_heatmap
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
        log(f"Error during RSI analysis: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run(default_config)
        if result:
            print("RSI analysis completed successfully!")
    except Exception as e:
        print(f"RSI analysis failed: {str(e)}")
        raise
