"""
Heatmap Generation Utilities

This module provides functions for generating and processing heatmaps
from portfolio data for the EMA cross strategy.
"""

import os
from datetime import datetime
import polars as pl

from app.tools.config_service import ConfigService
from app.tools.file_utils import get_portfolio_path
from app.tools.portfolio_transformation import transform_portfolio_data
from app.ma_cross.tools.plot_heatmaps import plot_heatmap
from app.tools.stats_converter import convert_stats

def process_heatmap_data(config: dict, log) -> bool:
    """Process portfolio data and generate heatmaps.

    Args:
        config (dict): Configuration dictionary
        log: Logging function

    Returns:
        bool: True if heatmap generation successful

    Raises:
        Exception: If portfolio data is missing or heatmap generation fails
    """
    try:
        config = ConfigService.process_config(config)
        log(f"Processing ticker: {config['TICKER']}")

        portfolio_file = get_portfolio_path(config)
        
        if not os.path.exists(portfolio_file):
            message = f"Portfolio file not found: {portfolio_file}"
            log(message)
            print(message)
            return False
            
        log(f"Loading portfolio data from: {portfolio_file}")
        raw_data = pl.read_csv(portfolio_file)

        # If USE_CURRENT is True, filter data based on current signals
        if config.get("USE_CURRENT", False):
            # Get current date in YYYYMMDD format
            current_date = datetime.now().strftime("%Y%m%d")
            
            # Determine file path components
            ma_type = 'SMA' if config.get('USE_SMA', False) else 'EMA'
            freq_type = 'H' if config.get('USE_HOURLY', False) else 'D'
            
            # Construct current signals file path from portfolios directory
            current_signals_file = os.path.join(
                'csv', 'ma_cross', 'portfolios',
                current_date,
                f"{config['TICKER']}_{freq_type}_{ma_type}.csv"
            )
            
            if os.path.exists(current_signals_file):
                log(f"Loading current signals from: {current_signals_file}")
                current_signals = pl.read_csv(current_signals_file)
                
                # Filter raw_data to only include rows where Short Window and Long Window
                # combinations exist in current_signals
                raw_data = raw_data.join(
                    current_signals,
                    left_on=['Short Window', 'Long Window'],
                    right_on=['Short Window', 'Long Window'],
                    how='inner'
                )
                log(f"Filtered portfolio data to {len(raw_data)} current signal combinations")
            else:
                log(f"Warning: Current signals file not found: {current_signals_file}")
        
        log("Transforming portfolio data")
        data = transform_portfolio_data(raw_data)
        
        log("Generating heatmaps")
        plot_heatmap(data, config, log)
        log("Heatmap generated successfully")
        
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        raise