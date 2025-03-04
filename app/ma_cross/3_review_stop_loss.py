"""
Stop Loss Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on stop loss parameters in combination with
EMA cross signals. It analyzes how different stop loss percentages affect strategy
performance metrics including returns, win rate, and expectancy.

The analysis can be performed in relative or absolute terms based on the config:
- When config['RELATIVE'] is True, all metrics are relative to the baseline analysis
- When config['RELATIVE'] is False, all metrics are absolute
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
from app.ma_cross.tools.stop_loss_analysis import analyze_stop_loss_parameters
from app.ma_cross.tools.stop_loss_plotting import create_stop_loss_heatmap

# Use CacheConfig from cache_utils.py
default_config: CacheConfig = {
    "TICKER": 'FAST',
    "SHORT_WINDOW": 14,
    "LONG_WINDOW": 25,
    "BASE_DIR": ".",
    "USE_SMA": False,
    "REFRESH": True,
    "USE_HOURLY": False,
    "RELATIVE": True,
    "DIRECTION": "Long",
    "USE_CURRENT": True,
    "USE_RSI": False,
    "RSI_WINDOW": 4,
    "RSI_THRESHOLD": 52
}

def run(config: CacheConfig) -> bool:
    """
    Run stop loss parameter sensitivity analysis.

    This function performs sensitivity analysis on stop loss parameters by:
    1. Setting up logging
    2. Loading cached results or preparing new data
    3. Running sensitivity analysis across stop loss parameters
    4. Displaying interactive heatmaps in browser

    Args:
        config (CacheConfig): Configuration dictionary containing strategy parameters.
            When config['RELATIVE'] is True, metrics are relative to baseline analysis.
            When config['RELATIVE'] is False, metrics are absolute.

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If data preparation or analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='3_review_stop_loss.log'
    )
    
    try:
        config = get_config(config)
        log(f"Starting stop loss analysis for {config['TICKER']}")
        
        # Define parameter ranges with explicit 2 decimal place precision
        stop_loss_range = np.round(np.arange(0, 15, 0.01), decimals=2)
        # stop_loss_range = np.round(np.arange(0, 20, 0.01), decimals=2)
        # stop_loss_range = np.round(np.arange(0, 25, 0.1), decimals=2)
        log(f"Using stop loss range: {stop_loss_range[0]:.2f}% to {stop_loss_range[-1]:.2f}%")

        # Check for cached results
        cache_dir, cache_file = get_cache_filepath(config, 'stop_loss')
        cache_path = os.path.join(cache_dir, cache_file)
        metric_matrices = None
        
        if not config.get("REFRESH", False):
            metric_matrices = load_cached_analysis(
                filepath=cache_path,
                param_range=stop_loss_range,
                param_column='Stop Loss [%]'
            )
            if metric_matrices is not None:
                log("Using cached stop loss analysis results")
        
        # If no cache or refresh requested, run new analysis
        if metric_matrices is None:
            log("Running new stop loss analysis")
            data = get_data(config["TICKER"], config, log)
            
            metric_matrices = analyze_stop_loss_parameters(
                data=data,
                config=config,
                stop_loss_range=stop_loss_range,
                log=log
            )
        
        if metric_matrices is None:
            raise Exception("Failed to generate or load metric matrices")
            
        # Create heatmap figures
        figures = create_stop_loss_heatmap(
            metric_matrices=metric_matrices,
            stop_loss_range=stop_loss_range,
            ticker=str(config["TICKER"]),
            config=config # Pass config to create_stop_loss_heatmap
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
        log(f"Error during stop loss analysis: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run(default_config)
        if result:
            print("Stop loss analysis completed successfully!")
    except Exception as e:
        print(f"Stop loss analysis failed: {str(e)}")
        raise
