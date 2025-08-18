"""
Heatmap Generation Utilities

This module provides functions for generating and processing heatmaps
from portfolio data for the EMA cross strategy.
"""

import os
from datetime import datetime

import polars as pl

from app.strategies.ma_cross.tools.plot_heatmaps import plot_heatmap
from app.tools.config_service import ConfigService
from app.tools.file_utils import get_portfolio_path
from app.tools.portfolio_transformation import transform_portfolio_data


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

        # If USE_CURRENT is True or USE_DATE is provided, filter data based on signals from specific date
        if config.get("USE_CURRENT", False) or config.get("USE_DATE"):
            # Get date in YYYYMMDD format - use provided date or current date
            if config.get("USE_DATE"):
                target_date = config.get("USE_DATE")
            else:
                target_date = datetime.now().strftime("%Y%m%d")

            # Determine file path components
            ma_type = "SMA" if config.get("USE_SMA", False) else "EMA"
            freq_type = "H" if config.get("USE_HOURLY", False) else "D"

            # Construct signals file path from portfolios directory
            signals_file = os.path.join(
                "csv",
                "ma_cross",
                "portfolios",
                target_date,
                f"{config['TICKER']}_{freq_type}_{ma_type}.csv",
            )

            if os.path.exists(signals_file):
                log(f"Loading signals from: {signals_file}")
                signals = pl.read_csv(signals_file)

                # Filter raw_data to only include rows where Fast Period and Slow Period
                # combinations exist in signals
                # Support both new and legacy column names
                left_cols = []
                right_cols = []

                # Determine which column names to use for joining
                if "Fast Period" in raw_data.columns:
                    left_cols = ["Fast Period", "Slow Period"]
                else:
                    left_cols = ["Fast Period", "Slow Period"]

                if "Fast Period" in signals.columns:
                    right_cols = ["Fast Period", "Slow Period"]
                else:
                    right_cols = ["Fast Period", "Slow Period"]

                raw_data = raw_data.join(
                    signals,
                    left_on=left_cols,
                    right_on=right_cols,
                    how="inner",
                )
                log(f"Filtered portfolio data to {len(raw_data)} signal combinations")
            else:
                log(f"Warning: Signals file not found: {signals_file}")

        log("Transforming portfolio data")
        data = transform_portfolio_data(raw_data)

        log("Generating heatmaps")
        plot_heatmap(data, config, log)
        log("Heatmap generated successfully")

        return True

    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        raise
