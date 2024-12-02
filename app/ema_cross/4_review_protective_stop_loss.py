"""
Protective Stop Loss Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on protective stop loss parameters in combination with
EMA cross signals. It analyzes how different holding periods affect strategy performance
metrics including returns, win rate, and expectancy.
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
from app.ema_cross.tools.protective_stop_loss_analysis import analyze_protective_stop_loss_parameters
from app.ema_cross.tools.protective_stop_loss_plotting import create_protective_stop_loss_heatmap

# Use CacheConfig from cache_utils.py
default_config: CacheConfig = {
    "TICKER": "META",
    "SHORT_WINDOW": 9,
    "LONG_WINDOW": 63,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "REFRESH": False,
    "USE_RSI": False,
    "RSI_PERIOD": 26,
    "RSI_THRESHOLD": 44,
    "STOP_LOSS": 0.0522
}

def run(config: CacheConfig) -> bool:
    """
    Run protective stop loss parameter sensitivity analysis.

    This function performs sensitivity analysis on holding periods by:
    1. Setting up logging
    2. Loading cached results or preparing new data
    3. Running sensitivity analysis across holding period parameters
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
        log_file='4_review_protective_stop_loss.log'
    )
    
    try:
        config = get_config(config)
        log(f"Starting protective stop loss analysis for {config['TICKER']}")
        
        # Check for cached results
        cache_dir, cache_file = get_cache_filepath(config, 'protective_stop_loss')
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, cache_file)
        
        metric_matrices = None
        holding_period_range = None
        
        if not config.get("REFRESH", False):
            try:
                metric_matrices = load_cached_analysis(
                    filepath=cache_path,
                    param_column='Holding Period'
                )
                if metric_matrices is not None:
                    # Extract holding period range from cached results shape
                    holding_period_range = np.arange(1, len(metric_matrices['trades']) + 1)
                    log("Using cached protective stop loss analysis results")
            except Exception as e:
                log(f"Error loading cached protective stop loss analysis: {str(e)}")
                metric_matrices = None
                holding_period_range = None
        
        # If no cache or refresh requested, run new analysis
        if metric_matrices is None:
            log("Running new protective stop loss analysis")
            data = get_data(config["TICKER"], config)
            
            metric_matrices, holding_period_range = analyze_protective_stop_loss_parameters(
                data=data,
                config=config,
                log=log
            )
        
        if metric_matrices is None or holding_period_range is None:
            raise Exception("Failed to generate metric matrices")
            
        log(f"Analysis complete with holding periods from 1 to {holding_period_range[-1]} days")
            
        # Create heatmap figures
        figures = create_protective_stop_loss_heatmap(
            metric_matrices=metric_matrices,
            holding_period_range=holding_period_range,
            ticker=str(config["TICKER"])
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
        log(f"Error during protective stop loss analysis: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run(default_config)
        if result:
            print("Protective stop loss analysis completed successfully!")
    except Exception as e:
        print(f"Protective stop loss analysis failed: {str(e)}")
        raise
